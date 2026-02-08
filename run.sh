#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

echo "🚀 Starting setup..."

# Use venv or .venv if present (call executables directly so PATH isn't required)
VENV_BIN=
if [ -d ".venv" ]; then
    echo "Using .venv..."
    VENV_BIN=".venv/bin"
elif [ -d "venv" ]; then
    echo "Using venv..."
    VENV_BIN="venv/bin"
else
    echo "⚠️  No venv or .venv found. Using PATH for alembic/uvicorn."
fi

# Run database migrations
echo "🔄 Running database migrations..."
if [ -n "$VENV_BIN" ]; then
    RUN_ALEMBIC="$VENV_BIN/alembic"
else
    RUN_ALEMBIC="alembic"
fi
if $RUN_ALEMBIC upgrade head; then
    echo "✅ Migrations applied successfully!"
else
    echo "❌ Migration failed!"
    exit 1
fi

# Start the FastAPI application
echo "🌟 Starting Intelligrade Server..."
if [ -n "$VENV_BIN" ]; then
    exec "$VENV_BIN/uvicorn" main:app --reload
else
    exec uvicorn main:app --reload
fi
