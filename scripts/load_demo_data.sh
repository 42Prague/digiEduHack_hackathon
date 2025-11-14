#!/bin/bash
# Load Demo Data Script for EduScale Engine Hackathon Submission
# This script sets up the database and loads demo data

set -e

echo "🚀 Setting up demo data for EduScale Engine..."
echo ""

# Check if docker compose is available
if ! command -v docker compose &> /dev/null; then
    echo "❌ Error: docker compose is not installed"
    exit 1
fi

# Start services
echo "📦 Starting Docker services..."
docker compose up -d db backend

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run migrations using db_setup.py
echo "🔄 Running database migrations..."
docker compose exec backend python swx_api/core/database/db_setup.py || {
    echo "⚠️  Migration may have already run (this is OK)"
}

# Wait a bit more
sleep 3

# Load transcripts
echo "📝 Loading transcripts..."
if docker compose exec -T db psql -U swx_user -d swx_db < mock_data/insert_transcripts.sql 2>&1 | grep -q "INSERT"; then
    echo "  ✅ Transcripts loaded"
else
    echo "  ⚠️  Some transcripts may already exist (this is OK)"
fi

# Load cultural analyses
echo "📊 Loading cultural analyses..."
if docker compose exec -T db psql -U swx_user -d swx_db < mock_data/insert_cultural_analysis.sql 2>&1 | grep -q "INSERT"; then
    echo "  ✅ Cultural analyses loaded"
else
    echo "  ⚠️  Some analyses may already exist (this is OK)"
fi

# Verify data
echo ""
echo "✅ Verifying loaded data..."
TRANSCRIPTS=$(docker compose exec -T db psql -U swx_user -d swx_db -t -c "SELECT COUNT(*) FROM transcripts;" 2>/dev/null | tr -d ' ' || echo "0")
ANALYSES=$(docker compose exec -T db psql -U swx_user -d swx_db -t -c "SELECT COUNT(*) FROM cultural_analysis;" 2>/dev/null | tr -d ' ' || echo "0")

echo ""
echo "📊 Data Summary:"
echo "  - Transcripts: $TRANSCRIPTS"
echo "  - Cultural Analyses: $ANALYSES"
echo ""

if [ "$TRANSCRIPTS" -gt "0" ] && [ "$ANALYSES" -gt "0" ]; then
    echo "✅ Demo data loaded successfully!"
    echo ""
    echo "🌐 Access the application:"
    echo "  - Frontend: http://localhost:3000"
    echo "  - Backend API: http://localhost:8000/docs"
    echo ""
    echo "📸 See SCREENSHOT_GUIDE.md for screenshot opportunities"
    echo ""
    echo "💡 To view data in database:"
    echo "  docker compose exec db psql -U swx_user -d swx_db"
else
    echo "⚠️  Warning: Data may not have loaded correctly"
    echo "   Check logs: docker compose logs backend"
    echo "   Or try running migrations manually:"
    echo "   docker compose exec backend python swx_api/core/database/db_setup.py"
fi
