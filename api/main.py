from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

# Import sub-apps
from api.diet_co2.main import app as diet_app
from api.python_vin_co2.src.main import app as vin_app

app = FastAPI(title="Carbon-Tracker Unified API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount sub-apps
app.mount("/api/diet", diet_app)
app.mount("/api/vin", vin_app)

@app.get("/")
async def root():
    return {"message": "Carbon-Tracker API is running"}

if __name__ == "__main__":
    uvicorn.run("api.main:app", host="0.0.0.0", port=3000, reload=True)
