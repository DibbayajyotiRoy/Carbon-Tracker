# src/utils/excel_loader.py
from pathlib import Path
import pandas as pd
import os

# Resolve DATA_DIR relative to script if environment variable is not set
env_data_dir = os.getenv("DATA_DIR")
if env_data_dir:
    DATA_DIR = Path(env_data_dir)
else:
    # Default to ../../transport_co2_data relative to this script
    DATA_DIR = Path(__file__).parent.parent.parent / "transport_co2_data"


def _read_xlsx(name: str):
    path = DATA_DIR / name
    if not path.exists():
        raise FileNotFoundError(f"{path} not found. Place your Excel file there.")
    return pd.read_excel(path)

def load_grid_factors():
    """
    Robust loader for Electricity_co2_countrywise.xlsx.
    - Accepts either 'grid_co2_kg_per_kwh' OR 'grid_co2_g_per_kwh' (will convert g->kg).
    - Optional columns (subregion) are tolerated and created if missing.
    Returns DataFrame with columns:
      ['country_code', 'subregion', 'grid_co2_kg_per_kwh']
    """
    df = _read_xlsx("Electricity_co2_countrywise.xlsx")

    # strip column names
    df.rename(columns={c: c.strip() for c in df.columns}, inplace=True)

    # convert g->kg if needed
    if "grid_co2_kg_per_kwh" not in df.columns and "grid_co2_g_per_kwh" in df.columns:
        df["grid_co2_kg_per_kwh"] = pd.to_numeric(df["grid_co2_g_per_kwh"], errors="coerce") / 1000.0

    # ensure required columns
    if "country_code" not in df.columns:
        raise KeyError("Electricity_co2_countrywise.xlsx must include 'country_code' column.")
    if "grid_co2_kg_per_kwh" not in df.columns:
        raise KeyError("Electricity_co2_countrywise.xlsx must include 'grid_co2_kg_per_kwh' or 'grid_co2_g_per_kwh' column.")

    # create optional columns if missing
    if "subregion" not in df.columns:
        df["subregion"] = ""
    if "source" not in df.columns:
        df["source"] = ""

    # canonicalize and type conversion
    df["country_code"] = df["country_code"].astype(str).str.upper().str.strip()
    df["subregion"] = df["subregion"].fillna("").astype(str).str.upper().str.strip()
    df["grid_co2_kg_per_kwh"] = pd.to_numeric(df["grid_co2_kg_per_kwh"], errors="coerce")

    # drop invalid rows
    df = df.dropna(subset=["country_code", "grid_co2_kg_per_kwh"])

    # return consistent columns
    return df[["country_code", "subregion", "grid_co2_kg_per_kwh"]]

# def load_fuel_factors():
    """
    Loads fuel_emission_factors_worldwide.xlsx
    Expected minimal columns: fuel_type, kg_co2_per_unit (or numeric convertible)
    Optional columns: unit
    Returns DataFrame with columns: ['fuel_type', 'unit', 'kg_co2_per_unit']
    """
    df = _read_xlsx("fuel_emission_factors_worldwide.xlsx")
    df.rename(columns={c: c.strip() for c in df.columns}, inplace=True)

    if "fuel_type" not in df.columns:
        raise KeyError("fuel_emission_factors_worldwide.xlsx must include 'fuel_type' column.")

    # optional columns
    if "unit" not in df.columns:
        df["unit"] = ""
    if "source" not in df.columns:
        df["source"] = ""

    df["fuel_type"] = df["fuel_type"].astype(str).str.upper().str.strip()
    df["kg_co2_per_unit"] = pd.to_numeric(df.get("kg_co2_per_unit"), errors="coerce")

    # Note: kg_co2_per_unit may be NaN for 'ELECTRIC' (we use grid factor instead)
    return df[["fuel_type", "unit", "kg_co2_per_unit"]]


def load_fuel_factors():
    """
    Loads fuel_emission_factors_worldwide.xlsx
    Accepts either 'kg_co2_per_unit' OR 'co2_kg_per_unit' (common variants).
    Returns DataFrame with columns: ['fuel_type', 'unit', 'kg_co2_per_unit']
    """
    df = _read_xlsx("fuel_emission_factors_worldwide.xlsx")
    df.rename(columns={c: c.strip() for c in df.columns}, inplace=True)

    if "fuel_type" not in df.columns:
        raise KeyError("fuel_emission_factors_worldwide.xlsx must include 'fuel_type' column.")

    # optional columns
    if "unit" not in df.columns:
        df["unit"] = ""
    if "source" not in df.columns:
        df["source"] = ""

    # Accept several possible CO2 column names
    # prefer 'kg_co2_per_unit', fallback to 'co2_kg_per_unit'
    if "kg_co2_per_unit" in df.columns:
        co2_col = "kg_co2_per_unit"
    elif "co2_kg_per_unit" in df.columns:
        co2_col = "co2_kg_per_unit"
    else:
        # If they used a different name (e.g. 'co2_per_unit'), try that too
        possible = [c for c in df.columns if "co2" in c.lower() and "unit" in c.lower()]
        co2_col = possible[0] if possible else None

    if not co2_col:
        raise KeyError("fuel_emission_factors_worldwide.xlsx must include a CO2-per-unit column (e.g. 'kg_co2_per_unit' or 'co2_kg_per_unit').")

    # Normalize columns to 'kg_co2_per_unit'
    df["fuel_type"] = df["fuel_type"].astype(str).str.upper().str.strip()
    df["unit"] = df["unit"].astype(str).fillna("").str.strip()
    df["kg_co2_per_unit"] = pd.to_numeric(df.get(co2_col), errors="coerce")

    # return canonical columns
    return df[["fuel_type", "unit", "kg_co2_per_unit"]]






def load_category_consumption():
    """
    Loads Fuelconsumption_countrywise_vehiclewise.xlsx
    Expected minimal columns: country_code, vehicle_category, fuel_type, consumption_per_km
    Optional columns: unit
    Returns DataFrame: ['country_code', 'vehicle_category', 'fuel_type', 'consumption_per_km', 'unit']
    """
    df = _read_xlsx("Fuelconsumption_countrywise_vehiclewise.xlsx")
    df.rename(columns={c: c.strip() for c in df.columns}, inplace=True)

    # required columns check
    required = ["country_code", "vehicle_category", "fuel_type", "consumption_per_km"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise KeyError(f"Fuelconsumption_countrywise_vehiclewise.xlsx missing required columns: {missing}")

    # optional columns
    if "unit" not in df.columns:
        df["unit"] = ""
    if "source" not in df.columns:
        df["source"] = ""

    # normalize text and numeric conversion
    df["country_code"] = df["country_code"].astype(str).str.upper().str.strip()
    df["vehicle_category"] = df["vehicle_category"].astype(str).str.upper().str.strip()
    df["fuel_type"] = df["fuel_type"].astype(str).str.upper().str.strip()
    df["consumption_per_km"] = pd.to_numeric(df["consumption_per_km"], errors="coerce")

    # drop rows missing essential numeric value
    df = df.dropna(subset=["country_code", "vehicle_category", "fuel_type", "consumption_per_km"])

    return df[["country_code", "vehicle_category", "fuel_type", "consumption_per_km", "unit"]]
















# # src/utils/excel_loader.py
# from pathlib import Path
# import pandas as pd
# import os

# DATA_DIR = Path(os.getenv("DATA_DIR", "transport_co2_data"))

# def _read_xlsx(name: str):
#     path = DATA_DIR / name
#     if not path.exists():
#         raise FileNotFoundError(f"{path} not found. Place your Excel file there.")
#     return pd.read_excel(path)

# def load_grid_factors():
#     """
#     Loads Electricity_co2_countrywise.xlsx
#     Expected columns: country_code, subregion (opt), grid_co2_kg_per_kwh (or grid_co2_g_per_kwh), source, year
#     Converts g->kg if needed.
#     """
#     df = _read_xlsx("Electricity_co2_countrywise.xlsx")
#     df = df.rename(columns={c: c.strip() for c in df.columns})
#     # normalize names
#     if "grid_co2_g_per_kwh" in df.columns and "grid_co2_kg_per_kwh" not in df.columns:
#         df["grid_co2_kg_per_kwh"] = pd.to_numeric(df["grid_co2_g_per_kwh"], errors="coerce") / 1000.0
#     df["country_code"] = df["country_code"].astype(str).str.upper().str.strip()
#     if "subregion" in df.columns:
#         df["subregion"] = df["subregion"].fillna("").astype(str).str.upper().str.strip()
#     else:
#         df["subregion"] = ""
#     df = df.dropna(subset=["country_code", "grid_co2_kg_per_kwh"])
#     return df[["country_code", "subregion", "grid_co2_kg_per_kwh", "source"]]

# def load_fuel_factors():
#     """
#     Loads fuel_emission_factors_worldwide.xlsx
#     Expected columns: fuel_type, unit, kg_co2_per_unit (numeric), source, year
#     """
#     df = _read_xlsx("fuel_emission_factors_worldwide.xlsx")
#     df["fuel_type"] = df["fuel_type"].astype(str).str.upper().str.strip()
#     df["kg_co2_per_unit"] = pd.to_numeric(df["kg_co2_per_unit"], errors="coerce")
#     return df[["fuel_type", "unit", "kg_co2_per_unit", "source"]]

# def load_category_consumption():
#     """
#     Loads Fuelconsumption_countrywise_vehiclewise.xlsx
#     Expected: country_code, category, fuel_type, consumption_per_km, unit, source, year
#     """
#     df = _read_xlsx("Fuelconsumption_countrywise_vehiclewise.xlsx")
#     df["country_code"] = df["country_code"].astype(str).str.upper().str.strip()
#     df["category"] = df["category"].astype(str).str.upper().str.strip()
#     df["fuel_type"] = df["fuel_type"].astype(str).str.upper().str.strip()
#     df["consumption_per_km"] = pd.to_numeric(df["consumption_per_km"], errors="coerce")
#     return df[["country_code", "category", "fuel_type", "consumption_per_km", "unit", "source"]]
