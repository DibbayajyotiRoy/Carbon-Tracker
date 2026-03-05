import os
import json
import io
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from google import genai
from google.genai import types
from pypdf import PdfReader

from api.database import get_db
from api.models import User, ElectricityBill, LPGRecord

app = FastAPI(title="Billing Service")

# Initialize Gemini Client
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

def calc_carbon_electricity(units: float) -> float:
    return round(float(units) * 0.82, 2)

@app.post("/upload-bill")
async def upload_bill(
    userId: str = Form(...),
    bill: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        content = await bill.read()
        extracted_text = ""
        
        # 1. Extract Text
        if bill.content_type == "application/pdf":
            reader = PdfReader(io.BytesIO(content))
            for page in reader.pages:
                extracted_text += page.extract_text() + "\n"
        elif bill.content_type in ["image/jpeg", "image/png", "image/jpg"]:
            # Use Gemini for OCR
            response = client.models.generate_content(
                model="gemini-2.0-flash",
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_bytes(data=content, mime_type=bill.content_type),
                            types.Part.from_text(text="Extract all text content from this electricity bill image.")
                        ]
                    )
                ]
            )
            extracted_text = response.text
        else:
            raise HTTPException(status_code=400, detail="Only PDF, JPG, PNG allowed")

        # 2. Structure Data with Gemini
        prompt = f"""
        Extract this text into JSON:
        {{
          "consumerName": "",
          "billNumber": "",
          "billingDate": "",
          "billingMonth": "",
          "unitsConsumed": 0,
          "totalAmount": 0,
          "address": "",
          "tariffType": ""
        }}
        Here is the text:
        {extracted_text}
        """
        
        struct_response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        structured_data = json.loads(struct_response.text)
        units = float(structured_data.get("unitsConsumed", 0))
        carbon_emitted = calc_carbon_electricity(units)

        # 3. Save to DB
        # Ensure user exists
        stmt = select(User).where(User.id == userId)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            user = User(id=userId)
            db.add(user)

        new_bill = ElectricityBill(
            user_id=userId,
            file_name=bill.filename,
            file_type=bill.content_type,
            bill_data=content,
            extracted_data=structured_data,
            carbon_emitted=carbon_emitted,
            uploaded_at=datetime.utcnow()
        )
        db.add(new_bill)
        await db.commit()

        return {
            "success": True,
            "message": "Bill processed successfully",
            "data": {**structured_data, "carbonEmitted": carbon_emitted}
        }
    except Exception as e:
        print(f"Error processing bill: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/emissions-summary")
async def emissions_summary(db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(ElectricityBill)
        result = await db.execute(stmt)
        bills = result.scalars().all()
        
        monthly = {}
        total = 0.0
        
        for bill in bills:
            # Safely handle missing billingMonth
            month = bill.extracted_data.get("billingMonth", "Unknown") if bill.extracted_data else "Unknown"
            emitted = float(bill.carbon_emitted) if bill.carbon_emitted else 0.0
            monthly[month] = monthly.get(month, 0.0) + emitted
            total += emitted
            
        return {"total": total, "monthly": monthly}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/carbon-insights")
async def carbon_insights(db: AsyncSession = Depends(get_db)):
    try:
        stmt = select(ElectricityBill).order_by(desc(ElectricityBill.uploaded_at)).limit(5)
        result = await db.execute(stmt)
        bills = result.scalars().all()
        
        usage_data = []
        for b in bills:
            month = b.extracted_data.get("billingMonth", "Unknown") if b.extracted_data else "Unknown"
            emitted = b.carbon_emitted if b.carbon_emitted else 0
            usage_data.append(f"{month}: {emitted} kg CO₂")
            
        usage_str = '\n'.join(usage_data)
        prompt = f"""
        Analyze the following monthly carbon usage:
        {usage_str}
        Give short insights and 3 actionable suggestions to reduce electricity-based emissions.
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt]
        )
        
        return {"insights": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/fetch-lpg")
async def fetch_lpg(
    userId: str = Form(...),
    lpgText: str = Form(...),
    db: AsyncSession = Depends(get_db)
):
    try:
        prompt = f"""
        You are an LPG extraction engine.
        Return STRICT JSON ONLY:
        {{
          "consumerNumber": "",
          "provider": "",
          "state": "",
          "district": "",
          "month": "",
          "connectionType": "",
          "subsidyStatus": "",
          "cylindersConsumed": 0,
          "lpgInKg": 0,
          "notes": ""
        }}
        Rules:
        - No explanation text.
        - If unknown, return empty or 0.
        INPUT: "{lpgText}"
        """
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=[prompt],
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        
        json_data = json.loads(response.text)
        
        # Carbon Calculation
        EMISSION_PER_CYL = 44.2
        EMISSION_PER_KG = 3.1
        
        carbon = 0.0
        cyl = float(json_data.get("cylindersConsumed", 0))
        kg = float(json_data.get("lpgInKg", 0))
        
        if cyl > 0:
            carbon = cyl * EMISSION_PER_CYL
        elif kg > 0:
            carbon = kg * EMISSION_PER_KG
            
        json_data["carbonEmitted"] = round(carbon, 2)

        # Save to DB
        new_record = LPGRecord(
            user_id=userId,
            consumer_number=json_data.get("consumerNumber"),
            provider=json_data.get("provider"),
            state=json_data.get("state"),
            district=json_data.get("district"),
            connection_type=json_data.get("connectionType"),
            subsidy_status=json_data.get("subsidyStatus"),
            cylinders_consumed=cyl,
            lpg_in_kg=kg,
            carbon_emitted=json_data["carbonEmitted"],
            notes=json_data.get("notes"),
            created_at=datetime.utcnow()
        )
        db.add(new_record)
        await db.commit()
        
        return {
            "success": True,
            "message": "LPG data extracted & stored successfully.",
            "data": json_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/calculate-lpg-emissions")
async def calculate_lpg_emissions(cylindersConsumed: float = 0, lpgInKg: float = 0):
    if cylindersConsumed <= 0 and lpgInKg <= 0:
        raise HTTPException(status_code=400, detail="Provide either cylindersConsumed or lpgInKg (must be > 0)")
        
    EMISSION_PER_CYL = 44.2
    EMISSION_PER_KG = 3.1
    
    carbon = 0.0
    if cylindersConsumed > 0:
        carbon += cylindersConsumed * EMISSION_PER_CYL
    if lpgInKg > 0:
        carbon += lpgInKg * EMISSION_PER_KG
        
    return {
        "success": True,
        "data": {
            "cylindersConsumed": cylindersConsumed,
            "lpgInKg": lpgInKg,
            "carbonEmitted": round(carbon, 2)
        }
    }
