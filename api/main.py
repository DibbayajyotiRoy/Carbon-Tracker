from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import sub-apps
from api.diet_co2.main import router as diet_router
from api.python_vin_co2.src.main import router as vin_router, init_vin_service
from api.billing.main import router as billing_router

app = FastAPI(title="Carbon-Tracker Unified API")

@app.on_event("startup")
async def startup_event():
    init_vin_service()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(diet_router, prefix="/api/diet")
app.include_router(vin_router, prefix="/api/vin")
app.include_router(billing_router, prefix="/api/billing")

@app.get("/")
async def root():
    return {"message": "Carbon-Tracker API is running"}

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=8000, reload=True)
