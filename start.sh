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
    echo "Please set these variables in your deployment environment:"
    echo "1. Update your .env file or Docker environment"
    echo "2. Add the missing variables"
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
# --proxy-headers makes FastAPI build redirect URLs from X-Forwarded-Proto. Without
# it, the trailing-slash redirect returns an http:// Location behind a TLS-
# terminating proxy, which browsers block as mixed content on an https page.
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info \
    --workers ${WEB_CONCURRENCY:-2} --proxy-headers --forwarded-allow-ips='*'

