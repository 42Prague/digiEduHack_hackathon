"""
Quick script to load sample data into the database
"""

from database_utils import get_database_connection, insert_survey_response
import pandas as pd
from datetime import datetime

print("🔄 Loading sample data into database...")

# Get database connection
engine = get_database_connection()
print("✓ Database connection established")

# Load sample data
df = pd.read_csv('data_structure_template.csv')
print(f"✓ Found {len(df)} sample responses in CSV")

# Convert to SQL
try:
    df.to_sql('teacher_survey_responses', engine, if_exists='append', index=False)
    print(f"✓ Successfully loaded {len(df)} responses into database!")
    print("\n🎉 Sample data loaded! You can now:")
    print("   1. View it in the Dashboard")
    print("   2. Query it with Ask Questions")
    print("   3. Submit more via Survey Form")
except Exception as e:
    print(f"✗ Error loading data: {e}")






