# Carbon Tracker Unified API Documentation

The Carbon Tracker API is a unified suite of services for tracking environmental impact. 
It is hosted at: `http://10.0.0.200:8000`

## ⚙️ Configuration

The application uses specific data files for emission factors. We have implemented robust path handling to locate these files automatically.

| Resource | Default Relative Path | Environment Variable |
| :--- | :--- | :--- |
| **VIN CO2 Excel Data** | `api/python_vin_co2/transport_co2_data/` | `DATA_DIR` |
| **Diet CO2 CSV Data** | `api/diet_co2/data/Food_type_co2.csv` | `FOOD_CSV_PATH` |

- **Standalone Mode**: Paths are resolved relative to the script location.
- **Service Mode**: Ensure the working directory is set to the project root or use the environment variables above to override paths.


## 🛠 Testing the API

You can test the API using the interactive documentation provided by FastAPI:

- **Swagger UI**: [http://10.0.0.200:8000/docs](http://10.0.0.200:8000/docs)
- **Scalar (Modern Docs)**: [http://10.0.0.200:8000/scalar](http://10.0.0.200:8000/scalar)

---

## 🥗 1. Diet CO2 Service
**Base Path:** `/api/diet`

### POST `/compute_food_co2`
Calculates CO2 emissions for food items.
**Request:**
```json
{
  "user_id": "string",
  "items": [{"food_type": "Rice", "quantity_grams": 200}]
}
```

---

## 🚗 2. VIN CO2 Service
**Base Path:** `/api/vin`

### POST `/upload-vin`
Upload VIN image for OCR and decoding.
**Request:** `multipart/form-data` with `file` and `user_id`.

### POST `/calculate/daily`
Calculate daily vehicle emissions based on stored GPS distance.
**Request Body:**
```json
{
  "user_id": "string",
  "country_code": "IN",
  "subregion": "string"
}
```

### 🛰 2.1 GPS Tracking
**Base Path:** `/api/vin/gps`

#### POST `/update`
Store a GPS log point.
**Request Body:**
```json
{
  "user_id": "string",
  "lat": 0.0,
  "lon": 0.0,
  "speed_kmh": 0.0,
  "distance_km": 0.0,
  "timestamp_iso": "ISO-8601 string"
}
```

#### GET `/daily-modes`
Retrieve GPS distance summary for a specific day.
**Query Params:** `user_id` (required), `day` (optional YYYY-MM-DD)

---

## 🧠 3. Mode Prediction
**Base Path:** `/api/vin/predict`

### GET `/mode`
Predict transport mode based on speed.
**Query Params:** `speed` (float)

---

## ⚡ 4. Billing Service
**Base Path:** `/api/billing`

### POST `/upload-bill`
Upload electricity bill (PDF/JPG/PNG) for OCR and calculation.
**Request:** `multipart/form-data` with `bill` (file) and `userId` (string).

### GET `/emissions-summary`
Get total and monthly emissions summary.

### GET `/carbon-insights`
Get AI-generated suggestions for reduction.

### POST `/fetch-lpg`
Extract LPG data from text.
**Request:** `multipart/form-data` with `lpgText` and `userId`.

### POST `/calculate-lpg-emissions`
Manual LPG calculation.
**Request Body:** `{"cylindersConsumed": 1, "lpgInKg": 0}`
