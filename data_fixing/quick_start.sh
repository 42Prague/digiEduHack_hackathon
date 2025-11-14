#!/bin/bash

# ====================================================================
# QUICK START SCRIPT
# Student Performance Survey System
# ====================================================================

echo "🚀 Student Performance Survey System - Quick Start"
echo "=================================================="
echo ""

# Check Python version
echo "📋 Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "   Found Python $python_version"

# Create virtual environment
echo ""
echo "📦 Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "   ✓ Virtual environment created"
else
    echo "   ✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "🔧 Activating virtual environment..."
source venv/bin/activate
echo "   ✓ Virtual environment activated"

# Install dependencies
echo ""
echo "📥 Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "   ✓ Dependencies installed"

# Create .streamlit directory if not exists
echo ""
echo "⚙️  Setting up configuration..."
if [ ! -d ".streamlit" ]; then
    mkdir .streamlit
    echo "   ✓ Created .streamlit directory"
fi

# Create secrets.toml if not exists
if [ ! -f ".streamlit/secrets.toml" ]; then
    cat > .streamlit/secrets.toml << 'EOF'
# Database Configuration
# Default: SQLite (no external database needed)

db_type = "sqlite"
db_path = "teacher_survey.db"

# For PostgreSQL, uncomment and configure:
# db_type = "postgresql"
# db_host = "localhost"
# db_port = "5432"
# db_name = "teacher_survey_db"
# db_user = "survey_admin"
# db_password = "your_password"

# For MySQL, uncomment and configure:
# db_type = "mysql"
# db_host = "localhost"
# db_port = "3306"
# db_name = "teacher_survey_db"
# db_user = "survey_admin"
# db_password = "your_password"
EOF
    echo "   ✓ Created secrets.toml with SQLite defaults"
else
    echo "   ✓ secrets.toml already exists"
fi

# Test database connection
echo ""
echo "🗄️  Testing database connection..."
python3 << 'PYTHON'
try:
    from database_utils import get_database_connection
    engine = get_database_connection()
    print("   ✓ Database connection successful")
except Exception as e:
    print(f"   ✗ Database connection failed: {e}")
PYTHON

# Create sample data (optional)
echo ""
read -p "📊 Would you like to load sample data? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 << 'PYTHON'
from database_utils import get_database_connection
import pandas as pd

try:
    engine = get_database_connection()
    df = pd.read_csv('data_structure_template.csv')
    df.to_sql('teacher_survey_responses', engine, if_exists='append', index=False)
    print(f"   ✓ Loaded {len(df)} sample responses")
except Exception as e:
    print(f"   ✗ Failed to load sample data: {e}")
PYTHON
else
    echo "   Skipped sample data loading"
fi

# Success message
echo ""
echo "✅ Setup complete!"
echo ""
echo "=================================================="
echo "🎉 Your survey system is ready!"
echo "=================================================="
echo ""
echo "To start the application:"
echo ""
echo "   streamlit run app.py"
echo ""
echo "The app will open automatically at http://localhost:8501"
echo ""
echo "📚 Documentation:"
echo "   - Setup Guide: SETUP_GUIDE.md"
echo "   - Project Overview: README_PROJECT_OVERVIEW.md"
echo "   - Analysis Guide: mixed_effects_model_analysis_guide.md"
echo ""
echo "Need help? Check the troubleshooting section in SETUP_GUIDE.md"
echo ""

# Ask if user wants to start now
read -p "Would you like to start the application now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 Starting Streamlit application..."
    echo "   Press Ctrl+C to stop"
    echo ""
    streamlit run app.py
fi




