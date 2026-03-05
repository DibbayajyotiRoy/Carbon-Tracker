import os
import logging
import math
import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from api.database import get_db
from api.models import User, Vehicle, GPSLog

# Local imports
from .services.gemini_ocr import extract_text_from_image_gemini
from .services.vin_lookup import decode_vin_vpic
from .services import emission
from .utils.validators import extract_vin_from_text, normalize_fuel

from .services.gps import router as gps_router
from .services.mode_predictor import router as mode_router

logger = logging.getLogger("uvicorn.error")

# ----------------- FastAPI App Initialization -----------------

app = FastAPI(title="Python VIN->CO2 Service")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

@app.on_event("startup")
async def startup_event():
    # Load tables for emission service
    emission.reload_tables()

# ----------------- Endpoints -----------------

@app.get("/")
def home():
    return {"Response" : "You are at home"}

@app.get("/ping")
def ping():
    return {"status": "ok"}

@app.post("/upload-vin")
async def upload_vin(user_id: str, file: UploadFile = File(...), db: AsyncSession = Depends(get_db)):
    raw = await file.read()
    mime = file.content_type or "image/jpeg"
    text = extract_text_from_image_gemini(raw, mime_type=mime)
    vin = extract_vin_from_text(text)
    if not vin:
        return {"vin": None, "decoded": None, "message": "VIN not detected. Send clearer/cropped VIN image."}
    
    decoded = await decode_vin_vpic(vin)
    
    # map category heuristics
    body = (decoded.get("BodyClass") or "") if decoded else ""
    vehicle_type = (decoded.get("VehicleType") or "") if decoded else ""
    
    cat = "CAR"
    if "TRUCK" in str(body).upper() or "TRUCK" in str(vehicle_type).upper():
        cat = "TRUCK_HEAVY"
    elif "BUS" in str(body).upper() or "BUS" in str(vehicle_type).upper():
        cat = "BUS"
    elif "MOTORCYCLE" in str(body).upper() or "MOTORCYCLE" in str(vehicle_type).upper():
        cat = "MOTORCYCLE"

    fuel = decoded.get("FuelTypePrimary") or decoded.get("FuelType") or decoded.get("FuelTypePrimary1") or None
    fuel_norm = normalize_fuel(fuel)
    
    # Save to DB
    stmt = select(Vehicle).where(Vehicle.vin == vin)
    result = await db.execute(stmt)
    vehicle = result.scalar_one_or_none()
    
    if not vehicle:
        vehicle = Vehicle(
            user_id=user_id,
            vin=vin,
            emission_factor=0.0
        )
        db.add(vehicle)
    
    vehicle.user_id = user_id
    vehicle.make = decoded.get("Make")
    vehicle.model = decoded.get("Model")
    vehicle.year = int(decoded.get("ModelYear")) if decoded.get("ModelYear") else None
    
    await db.commit()
    
    return {"vin": vin, "decoded": decoded, "vehicle_category": cat, "fuel_type": fuel_norm}

@app.post("/calculate/daily")
async def calculate_daily(user_id: str, country_code: str = None, subregion: str = "", db: AsyncSession = Depends(get_db)):
    user_id = str(user_id).strip()
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id is required")

    # Lookup vehicle
    stmt = select(Vehicle).where(Vehicle.user_id == user_id).limit(1)
    result = await db.execute(stmt)
    vehicle = result.scalar_one_or_none()
    
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found for this user.")

    vehicle_category = "CAR" 
    fuel_type = "GASOLINE"

    if not country_code:
        country_code = "IN"

    # Sum today's gps distance
    today_start = datetime.combine(date.today(), datetime.min.time())
    today_end = datetime.combine(date.today(), datetime.max.time())
    
    stmt = select(func.sum(GPSLog.distance_km)).where(
        GPSLog.user_id == user_id,
        GPSLog.timestamp >= today_start,
        GPSLog.timestamp <= today_end
    )
    result = await db.execute(stmt)
    distance = result.scalar() or 0.0

    if distance <= 0:
        raise HTTPException(status_code=400, detail=f"No GPS distance recorded for today.")

    try:
        res = emission.compute_co2_per_km(country_code, vehicle_category, fuel_type, subregion)
    except Exception as e:
        logger.exception("compute_co2_per_km failed")
        raise HTTPException(status_code=500, detail=f"compute_co2_per_km failed: {e}")

    kg_co2_per_km = res.get("kg_co2_per_km", 0.0)
    total_kg = distance * kg_co2_per_km

    return {
        "ok": True,
        "record": {
            "user_id": user_id,
            "date": date.today().isoformat(),
            "distance_km": distance,
            "co2_kg_per_km": kg_co2_per_km,
            "total_kg_co2": total_kg,
            "details": res
        }
    }

app.include_router(gps_router)
app.include_router(mode_router)
