#!/bin/bash

# Startup script for BDD Property Tracker API
echo "🚀 Starting BDD Property Tracker API..."

# Check required environment variables
required_vars=("DATABASE_URL" "SECRET_KEY")
missing_vars=()

for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        missing_vars+=("$var")
    fi
done

if [ ${#missing_vars[@]} -ne 0 ]; then
    echo "❌ ERROR: Missing required environment variables:"
    for var in "${missing_vars[@]}"; do
        echo "  - $var"
    done
    echo ""
    echo "Please set these variables in Railway dashboard:"
    echo "1. Go to your service settings"
    echo "2. Click on 'Variables' tab"
    echo "3. Add the missing variables"
    exit 1
fi

# Print startup info
echo "✅ Environment variables validated"
echo "📊 Configuration:"
echo "  - Database: ${DATABASE_URL%%@*}@***" # Hide password
echo "  - Port: ${PORT:-8000}"
echo "  - Upload Directory: ${UPLOAD_DIRECTORY:-./uploads}"

# Run database migrations (if needed)
if [ "${RUN_MIGRATIONS:-true}" = "true" ]; then
    echo "🔄 Running database migrations..."
    alembic upgrade head || {
        echo "⚠️  Migration failed, but continuing..."
    }
fi

# Start the application
echo "🌐 Starting uvicorn server..."
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info

