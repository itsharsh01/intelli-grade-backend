#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🚀 Starting setup..."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    echo "Creating virtual environment context..."
    source .venv/bin/activate
else
    echo "⚠️  No .venv directory found. Assuming dependencies are installed globally or in another environment."
fi

# Run database migrations
echo "🔄 Running database migrations..."
if alembic upgrade head; then
    echo "✅ Migrations applied successfully!"
else
    echo "❌ Migration failed!"
    exit 1
fi

# Start the FastAPI application
echo "🌟 Starting Intelligrade Server..."
uvicorn main:app --reload
