# Carbon Tracker Unified API Documentation

The Carbon Tracker API is a unified suite of services for tracking environmental impact. 
It is hosted at: `http://10.0.0.200:8000`

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
Calculate daily vehicle emissions.
**Request:**
```json
{
  "user_id": "string",
  "country_code": "IN"
}
```

---

## ⚡ 3. Billing Service
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
