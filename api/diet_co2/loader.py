import csv
import os
from datetime import datetime
import asyncio
from dotenv import load_dotenv

# load .env (tries package .env then project root)
env_path = os.path.join(os.path.dirname(__file__), ".env")
if not os.path.exists(env_path):
    env_path = os.path.join(os.getcwd(), ".env")
load_dotenv(env_path)

from .db import db

env_csv_path = os.getenv("FOOD_CSV_PATH")
if env_csv_path:
    CSV_PATH = env_csv_path
else:
    # Default to data/Food_type_co2.csv relative to this script
    CSV_PATH = os.path.join(os.path.dirname(__file__), "data", "Food_type_co2.csv")

FOOD_NAME_COL_OVERRIDE = os.getenv("FOOD_NAME_COL")
EF_COL_OVERRIDE = os.getenv("EF_COL")

NORMALIZED_COLLECTION = "food_efs"
RAW_COLLECTION = "food_efs_raw"

def normalize_food_name(name: str) -> str:
    return name.strip().lower()

def is_number(s: str):
    try:
        float(s)
        return True
    except Exception:
        return False

async def load_csv_into_mongo(csv_path: str = CSV_PATH):
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at {csv_path}")

    # Read CSV
    with open(csv_path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames or []
        raw_rows = [row for row in reader]

    # ---------- Insert raw rows AS-IS (no added metadata) ----------
    # Clear and reinsert raw rows exactly (preserves Excel headers)
    await db[RAW_COLLECTION].delete_many({})
    if raw_rows:
        # Insert raw rows exactly; Mongo will add its own ObjectId but we won't add extra fields
        await db[RAW_COLLECTION].insert_many(raw_rows)

    # ---------- Detect columns (same logic as before) ----------
    food_col = None
    ef_col = None

    if FOOD_NAME_COL_OVERRIDE and FOOD_NAME_COL_OVERRIDE in headers:
        food_col = FOOD_NAME_COL_OVERRIDE
    if EF_COL_OVERRIDE and EF_COL_OVERRIDE in headers:
        ef_col = EF_COL_OVERRIDE

    if not food_col:
        food_name_candidates = ["food_name", "Food", "food", "Food_name", "Food Name", "Name", "name", "Item", "Item Name", "FoodType", "food_type"]
        for c in food_name_candidates:
            if c in headers:
                food_col = c
                break

    if not ef_col:
        ef_candidates = ["kgco2e_per_kg","kgCO2e_per_kg","kg_co2e_per_kg","EF","kgco2e","EF_value","ef","kg_co2e","ef_value","kg_co2e_per_kg"]
        for c in ef_candidates:
            if c in headers:
                ef_col = c
                break

    if (not food_col or not ef_col) and raw_rows:
        first = raw_rows[0]
        if not food_col:
            for h in headers:
                v = first.get(h)
                if v and str(v).strip() != "":
                    food_col = h
                    break
        if not ef_col:
            for h in headers:
                numeric_found = False
                for rr in raw_rows[:10]:
                    v = rr.get(h)
                    if v is None:
                        continue
                    s = str(v).strip()
                    if is_number(s):
                        numeric_found = True
                        break
                if numeric_found:
                    ef_col = h
                    break

    # ---------- Build minimal normalized docs ----------
    normalized = []
    for r in raw_rows:
        # get food name
        raw_food_name = None
        if food_col and food_col in r:
            raw_food_name = r.get(food_col)
        else:
            for h in headers:
                v = r.get(h)
                if v and str(v).strip() != "":
                    raw_food_name = v
                    break
        if not raw_food_name:
            continue

        # get ef
        ef_val = None
        if ef_col and ef_col in r:
            s = r.get(ef_col)
            if s is not None and str(s).strip() != "":
                try:
                    ef_val = float(str(s).strip())
                except Exception:
                    ef_val = None
        # try any numeric column if still None
        if ef_val is None:
            for h in headers:
                v = r.get(h)
                if v is None:
                    continue
                s = str(v).strip()
                if is_number(s):
                    try:
                        ef_val = float(s)
                        break
                    except Exception:
                        continue

        doc = {
            "food_name": str(raw_food_name),
            "food_name_normalized": normalize_food_name(str(raw_food_name)),
            "kgco2e_per_kg": ef_val  # float or None
        }
        normalized.append(doc)

    # ---------- Insert/update normalized docs ----------
    # We'll use upsert matching on food_name_normalized; do not force _id
    for doc in normalized:
        await db[NORMALIZED_COLLECTION].update_one(
            {"food_name_normalized": doc["food_name_normalized"]},
            {"$set": doc},
            upsert=True
        )

    # create index on normalized name for fast lookup (idempotent)
    await db[NORMALIZED_COLLECTION].create_index("food_name_normalized", unique=True)

    return {"raw_count": len(raw_rows), "normalized_count": len(normalized), "detected_food_col": food_col, "detected_ef_col": ef_col}

if __name__ == "__main__":
    asyncio.run(load_csv_into_mongo())
    print("CSV loaded into MongoDB.")
