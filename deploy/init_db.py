import asyncio
import sys
import os

# Add the root directory to sys.path to allow importing api
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api.database import engine, Base
from api.models import FoodEmissionFactor, User
import pandas as pd

async def init_db():
    print("Creating tables...")
    async with engine.begin() as conn:
        # For development/init, you might want to drop and recreate
        # await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Tables created.")

    # Seed Food Emission Factors from CSV
    print("Seeding food emission factors...")
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy import select
    
    AsyncSessionLocal = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with AsyncSessionLocal() as session:
        csv_path = os.path.join(os.path.dirname(__file__), "..", "api", "diet_co2", "data", "Food_type_co2.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            for _, row in df.iterrows():
                food_type = row['food_type']
                co2 = row['co2 _per_kg']
                
                # Check if exists
                stmt = select(FoodEmissionFactor).where(FoodEmissionFactor.food_type == food_type)
                result = await session.execute(stmt)
                if not result.scalar_one_or_none():
                    fe = FoodEmissionFactor(
                        food_type=food_type,
                        food_type_normalized=food_type.strip().lower(),
                        kgco2e_per_kg=co2
                    )
                    session.add(fe)
            await session.commit()
            print("Food emission factors seeded.")
        else:
            print(f"CSV not found at {csv_path}")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())
