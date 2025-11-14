"""
Export data from database to CSV for statistical analysis
"""

from database_utils import get_database_connection, get_all_responses
import pandas as pd
from datetime import datetime

print("📤 Exporting data for statistical analysis...")

# Get database connection
engine = get_database_connection()
print("✓ Database connected")

# Get all responses
df = get_all_responses(engine)

if df is None or df.empty:
    print("❌ No data found in database!")
    print("   Submit some survey responses first.")
else:
    # Save to CSV
    filename = f"survey_data_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    df.to_csv(filename, index=False)
    
    print(f"✅ Exported {len(df)} responses to: {filename}")
    print(f"\n📊 Data Summary:")
    print(f"   Total responses: {len(df)}")
    print(f"   Teachers: {df['teacher_id'].nunique()}")
    print(f"   Schools: {df['school_id'].nunique()}")
    print(f"   Regions: {df['region'].nunique()}")
    print(f"   Date range: {df['survey_date'].min()} to {df['survey_date'].max()}")
    print(f"\n🎯 Next step:")
    print(f"   1. Update analysis script to read '{filename}'")
    print(f"   2. Run: Rscript mixed_effects_analysis.R")
    print(f"   3. Or: python mixed_effects_analysis.py")




