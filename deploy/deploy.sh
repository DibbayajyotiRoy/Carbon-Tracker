#!/bin/bash
set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR/.."
echo "Working in $(pwd)"

# 1. Update and install dependencies
sudo apt update
sudo apt install -y postgresql postgresql-contrib curl

# 2. Database Setup
echo "Configuring PostgreSQL..."
# Run psql from /tmp to avoid "Permission denied" warnings from the postgres user
pushd /tmp > /dev/null
sudo -u postgres psql <<EOF
-- Idempotent DB setup
SELECT 'CREATE DATABASE carbon_tracker' WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'carbon_tracker')\gexec
SELECT 'CREATE USER carbon_user WITH PASSWORD ''password''' WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'carbon_user')\gexec
GRANT ALL PRIVILEGES ON DATABASE carbon_tracker TO carbon_user;
-- Ensure user has permissions to create tables in the public schema (required for PG 15+)
\c carbon_tracker
GRANT ALL ON SCHEMA public TO carbon_user;
EOF
popd > /dev/null

# 3. Install uv
echo "Installing uv..."
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
else
    echo "uv is already installed."
fi

# 4. Environment Setup
echo "Creating .env file if missing..."
if [ ! -f .env ]; then
    cat <<EOF > .env
DATABASE_URL=postgresql+asyncpg://carbon_user:password@localhost/carbon_tracker
GEMINI_API_KEY=YOUR_API_KEY_HERE
EOF
    echo ".env created. PLEASE UPDATE GEMINI_API_KEY later!"
fi

# 5. Sync dependencies
echo "Syncing dependencies with uv..."
uv sync

# 6. Initialize and seed DB
echo "Initializing Database..."
# Use explicit python for uv run and ensure correct relative path
uv run python deploy/init_db.py

# 7. Setup systemd
echo "Setting up systemd service..."
# Update paths and user/group in service file for ubuntu user
sed -i "s|/home/roy|/home/ubuntu|g" deploy/carbon-tracker.service
sed -i "s|User=roy|User=ubuntu|g" deploy/carbon-tracker.service
sed -i "s|Group=roy|Group=ubuntu|g" deploy/carbon-tracker.service
sudo cp deploy/carbon-tracker.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable carbon-tracker.service
sudo systemctl start carbon-tracker.service

echo "Deployment Complete! Backend should be running at http://localhost:8000"
sudo systemctl status carbon-tracker.service --no-pager
