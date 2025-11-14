#!/bin/bash

# ====================================================================
# Docker Entrypoint Script
# Handles initialization sequence for the application
# ====================================================================

set -e

echo "======================================================================"
echo "🚀 Student Performance Survey System - Initialization"
echo "======================================================================"
echo ""

# Database path
DB_PATH="${DB_PATH:-/app/data/teacher_survey.db}"
DB_DIR=$(dirname "$DB_PATH")

# ====================================================================
# Step 1: Ensure database directory exists
# ====================================================================

echo "📁 Step 1: Checking database directory..."
if [ ! -d "$DB_DIR" ]; then
    echo "   Creating database directory: $DB_DIR"
    mkdir -p "$DB_DIR"
fi
echo "   ✅ Database directory ready: $DB_DIR"
echo ""

# ====================================================================
# Step 2: Initialize database if it doesn't exist
# ====================================================================

echo "🗄️  Step 2: Checking database..."
if [ ! -f "$DB_PATH" ]; then
    echo "   Database not found. Creating new database..."
    
    # Create empty database file
    touch "$DB_PATH"
    
    # Initialize database schema using Python (better than SQLite CLI for compatibility)
    echo "   Initializing database schema..."
    python3 << EOF
import sqlite3
import sys

try:
    conn = sqlite3.connect("$DB_PATH")
    cursor = conn.cursor()
    
    # Read and execute SQL schema
    with open('database_setup.sql', 'r') as f:
        sql_script = f.read()
        
        # Split by statements and execute (handling views separately)
        statements = []
        current_statement = []
        
        for line in sql_script.split('\n'):
            # Skip comments and empty lines
            if line.strip().startswith('--') or not line.strip():
                continue
            
            current_statement.append(line)
            
            # Check if statement is complete
            if ';' in line:
                statement = '\n'.join(current_statement)
                statements.append(statement)
                current_statement = []
        
        # Execute CREATE TABLE statements first
        for stmt in statements:
            if 'CREATE TABLE' in stmt.upper():
                try:
                    # Remove MySQL-specific syntax
                    stmt = stmt.replace('ON DUPLICATE KEY UPDATE', '--')
                    stmt = stmt.replace('ON UPDATE CURRENT_TIMESTAMP', '')
                    cursor.execute(stmt)
                except Exception as e:
                    print(f"   ⚠️  Warning executing statement: {e}")
        
        conn.commit()
    
    conn.close()
    print("   ✅ Database schema initialized successfully")
    sys.exit(0)
    
except Exception as e:
    print(f"   ❌ Error initializing database: {e}")
    sys.exit(1)
EOF

    if [ $? -eq 0 ]; then
        echo "   ✅ Database created and initialized"
    else
        echo "   ❌ Failed to initialize database"
        exit 1
    fi
else
    echo "   ✅ Database already exists: $DB_PATH"
fi
echo ""

# ====================================================================
# Step 3: Generate mock data if requested
# ====================================================================

echo "📊 Step 3: Checking mock data..."
GENERATE_MOCK_DATA="${GENERATE_MOCK_DATA:-true}"

if [ "$GENERATE_MOCK_DATA" = "true" ]; then
    # Check if database has data
    DATA_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM teacher_survey_responses;" 2>/dev/null || echo "0")
    
    if [ "$DATA_COUNT" = "0" ]; then
        echo "   No data found. Generating mock data..."
        
        # Set database path for the script
        export DB_PATH="$DB_PATH"
        
        # Run mock data generator
        if python3 generate_mock_data.py; then
            echo "   ✅ Mock data generated successfully"
        else
            echo "   ⚠️  Warning: Failed to generate mock data"
            echo "   Application will start but may have no data to display"
        fi
    else
        echo "   ✅ Database already contains $DATA_COUNT records"
    fi
else
    echo "   ⏭️  Mock data generation skipped (GENERATE_MOCK_DATA=false)"
fi
echo ""

# ====================================================================
# Step 4: Verify database health
# ====================================================================

echo "🔍 Step 4: Verifying database health..."
if sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM teacher_survey_responses;" > /dev/null 2>&1; then
    RECORD_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM teacher_survey_responses;")
    echo "   ✅ Database is healthy"
    echo "   📈 Total survey responses: $RECORD_COUNT"
else
    echo "   ⚠️  Warning: Could not verify database health"
fi
echo ""

# ====================================================================
# Step 5: Start the application
# ====================================================================

echo "======================================================================"
echo "🎉 Initialization Complete!"
echo "======================================================================"
echo "📊 Application Details:"
echo "   - Database: $DB_PATH"
echo "   - Records: $RECORD_COUNT"
echo "   - Port: ${STREAMLIT_SERVER_PORT:-8501}"
echo ""
echo "🌐 Access the application at:"
echo "   http://localhost:${STREAMLIT_SERVER_PORT:-8501}"
echo ""
echo "======================================================================"
echo "🚀 Starting Streamlit application..."
echo "======================================================================"
echo ""

# Execute the main command (from CMD in Dockerfile)
exec "$@"

