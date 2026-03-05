#!/bin/bash
set -e

echo "Starting Carbon-Tracker Deployment..."

# 1. Update and install dependencies
sudo apt update
sudo apt install -y postgresql postgresql-contrib curl

# 2. Database Setup
echo "Configuring PostgreSQL..."
sudo -u postgres psql <<EOF
CREATE DATABASE carbon_tracker;
CREATE USER carbon_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE carbon_tracker TO carbon_user;
EOF

# 3. Install uv
echo "Installing uv..."
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# 4. Sync dependencies
echo "Syncing dependencies with uv..."
uv sync

# 5. Initialize and seed DB
echo "Initializing Database..."
DATABASE_URL=postgresql+asyncpg://carbon_user:password@localhost/carbon_tracker uv run deploy/init_db.py

# 6. Setup systemd
echo "Setting up systemd service..."
sudo cp deploy/carbon-tracker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable carbon-tracker.service
sudo systemctl start carbon-tracker.service

echo "Deployment Complete! Backend should be running at http://localhost:3000"
sudo systemctl status carbon-tracker.service --no-pager
