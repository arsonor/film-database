#!/bin/bash
set -e

echo "=== Film Database Setup ==="

# Load .env
source .env 2>/dev/null || true

DB_NAME="${DB_NAME:-film_database}"
DB_USER="${DB_USER:-postgres}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"

echo "1. Creating database '$DB_NAME'..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || echo "   Database already exists."

echo "2. Running schema.sql..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/schema.sql

echo "3. Running seed_taxonomy.sql..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -f database/seed_taxonomy.sql

echo "4. Verifying tables..."
psql -h $DB_HOST -p $DB_PORT -U $DB_USER -d $DB_NAME -c "\dt" | head -40

echo "=== Setup complete ==="
