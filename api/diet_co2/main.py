import os
import uuid
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from fastapi.encoders import jsonable_encoder

from api.database import get_db
from api.models import FoodEmissionFactor, FoodEmission, User
from api.diet_co2.models import FoodInput, ConsumptionRequest, ConsumptionResponse, ComputationResult

app = FastAPI(title="Diet CO2 Service")

def normalize_name(n: str) -> str:
    return n.strip().lower()

async def lookup_ef(db: AsyncSession, food_name: str):
    norm = normalize_name(food_name)
    # Search by exact normalized name
    stmt = select(FoodEmissionFactor).where(FoodEmissionFactor.food_type_normalized == norm)
    result = await db.execute(stmt)
    ef = result.scalar_one_or_none()
    
    if not ef:
        # Fallback to regex-like search using LIKE
        stmt = select(FoodEmissionFactor).where(FoodEmissionFactor.food_type_normalized.like(f"%{norm}%"))
        result = await db.execute(stmt)
        ef = result.scalars().first()
        
    return ef

@app.post("/compute_food_co2", response_model=ConsumptionResponse)
async def compute_food_co2(req: ConsumptionRequest, db: AsyncSession = Depends(get_db)):
    # session id groups multiple items in one event
    session_id = str(uuid.uuid4())
    ate_at = req.ate_at or datetime.utcnow()
    user_id = req.user_id

    # Ensure user exists if provided
    if user_id:
        stmt = select(User).where(User.id == user_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            user = User(id=user_id)
            db.add(user)
            await db.commit()

    results: List[ComputationResult] = []
    total_co2 = 0.0

    if not req.items or len(req.items) == 0:
        raise HTTPException(status_code=400, detail="No items provided")

    for item in req.items:
        ef_doc = await lookup_ef(db, item.food_type)

        if not ef_doc:
            raise HTTPException(status_code=404, detail=f"Emission factor not found for '{item.food_type}'. Please add to database.")

        ef_val = float(ef_doc.kgco2e_per_kg)
        qty_kg = float(item.quantity_grams) / 1000.0
        co2 = round(qty_kg * ef_val, 6)
        total_co2 += co2

        result = ComputationResult(
            food_type=item.food_type,
            quantity_grams=item.quantity_grams,
            kgco2e_per_kg=ef_val,
            co2_kg=co2
        )
        results.append(result)

        # Log individual emission item
        db.add(FoodEmission(
            user_id=user_id,
            session_id=session_id,
            food_type=item.food_type,
            quantity_grams=item.quantity_grams,
            kgco2e_per_kg=ef_val,
            co2_kg=co2,
            ate_at=ate_at
        ))

    await db.commit()

    response = ConsumptionResponse(
        session_id=session_id,
        user_id=user_id,
        ate_at=ate_at,
        results=results,
        total_co2_kg=round(total_co2, 6)
    )
    return JSONResponse(status_code=200, content=jsonable_encoder(response))
