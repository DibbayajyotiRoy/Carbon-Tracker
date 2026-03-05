# VM Setup Guide (10.0.0.200)

Follow these steps to host the Carbon-Tracker backend on your VM.

## 1. Install PostgreSQL
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

## 2. Configure Database
Log into PostgreSQL and create the database and user:
```bash
sudo -u postgres psql
```
In the PSQL prompt:
```sql
CREATE DATABASE carbon_tracker;
CREATE USER carbon_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE carbon_tracker TO carbon_user;
\q
```

## 3. Install uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env
```

## 4. Initialize Backend
Assuming the files are in `/home/roy/Documents/carbon-app/Carbon-Tracker`:
```bash
cd /home/roy/Documents/carbon-app/Carbon-Tracker
uv sync
```

## 5. Seed Database
Run the initialization script to create tables and seed food emission factors:
```bash
DATABASE_URL=postgresql+asyncpg://carbon_user:password@localhost/carbon_tracker uv run deploy/init_db.py
```

## 6. Setup systemd Service
Copy the service file and enable it:
```bash
sudo cp deploy/carbon-tracker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable carbon-tracker.service
sudo systemctl start carbon-tracker.service
```

## 7. Verify Status
```bash
sudo systemctl status carbon-tracker.service
curl http://localhost:3000/
```
