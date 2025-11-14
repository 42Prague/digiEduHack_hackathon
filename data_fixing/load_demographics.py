"""
Load Demographics from Excel Configuration File
This script reads demographics_config.xlsx and populates reference tables
"""

import pandas as pd
from database_utils import get_database_connection
from sqlalchemy import text
import sys

def create_reference_tables(engine):
    """Create reference tables for demographics"""
    
    tables_sql = [
        # Regions table
        """
        CREATE TABLE IF NOT EXISTS ref_regions (
            region_id TEXT PRIMARY KEY,
            region_name TEXT NOT NULL,
            description TEXT,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Schools table
        """
        CREATE TABLE IF NOT EXISTS ref_schools (
            school_id TEXT PRIMARY KEY,
            school_name TEXT NOT NULL,
            region_id TEXT,
            intervention_status TEXT,
            total_students INTEGER,
            total_teachers INTEGER,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """,
        
        # Grade levels
        """
        CREATE TABLE IF NOT EXISTS ref_grade_levels (
            grade_id TEXT PRIMARY KEY,
            grade_name TEXT NOT NULL,
            level TEXT,
            active BOOLEAN DEFAULT TRUE
        )
        """,
        
        # Subject areas
        """
        CREATE TABLE IF NOT EXISTS ref_subject_areas (
            subject_id TEXT PRIMARY KEY,
            subject_name TEXT NOT NULL,
            active BOOLEAN DEFAULT TRUE
        )
        """,
        
        # Teaching experience
        """
        CREATE TABLE IF NOT EXISTS ref_teaching_experience (
            experience_id TEXT PRIMARY KEY,
            experience_name TEXT NOT NULL,
            min_years INTEGER,
            max_years INTEGER,
            active BOOLEAN DEFAULT TRUE
        )
        """,
        
        # Intervention components
        """
        CREATE TABLE IF NOT EXISTS ref_intervention_components (
            component_id TEXT PRIMARY KEY,
            component_name TEXT NOT NULL,
            description TEXT,
            active BOOLEAN DEFAULT TRUE
        )
        """,
        
        # Performance outcomes
        """
        CREATE TABLE IF NOT EXISTS ref_performance_outcomes (
            outcome_id TEXT PRIMARY KEY,
            outcome_name TEXT NOT NULL,
            db_column TEXT NOT NULL,
            scale_min INTEGER,
            scale_max INTEGER,
            active BOOLEAN DEFAULT TRUE
        )
        """,
        
        # Learning elements
        """
        CREATE TABLE IF NOT EXISTS ref_learning_elements (
            element_id TEXT PRIMARY KEY,
            element_name TEXT NOT NULL,
            description TEXT,
            active BOOLEAN DEFAULT TRUE
        )
        """,
        
        # Skills improvement
        """
        CREATE TABLE IF NOT EXISTS ref_skills_improvement (
            skill_id TEXT PRIMARY KEY,
            skill_name TEXT NOT NULL,
            active BOOLEAN DEFAULT TRUE
        )
        """,
        
        # Configuration
        """
        CREATE TABLE IF NOT EXISTS ref_configuration (
            setting TEXT PRIMARY KEY,
            value TEXT NOT NULL,
            description TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    ]
    
    print("📋 Creating reference tables...")
    with engine.connect() as conn:
        for sql in tables_sql:
            conn.execute(text(sql))
        conn.commit()
    print("✓ Reference tables created")

def clear_reference_data(engine):
    """Clear existing reference data before loading new"""
    
    tables = [
        'ref_regions', 'ref_schools', 'ref_grade_levels', 
        'ref_subject_areas', 'ref_teaching_experience',
        'ref_intervention_components', 'ref_performance_outcomes',
        'ref_learning_elements', 'ref_skills_improvement', 'ref_configuration'
    ]
    
    print("🗑️  Clearing existing reference data...")
    with engine.connect() as conn:
        for table in tables:
            conn.execute(text(f"DELETE FROM {table}"))
        conn.commit()
    print("✓ Existing data cleared")

def load_excel_to_database(excel_file, engine):
    """Load all sheets from Excel into database"""
    
    # Read Excel file
    print(f"📖 Reading Excel file: {excel_file}")
    try:
        excel_data = pd.read_excel(excel_file, sheet_name=None)
    except FileNotFoundError:
        print(f"❌ Error: File '{excel_file}' not found!")
        print("   Run 'python create_demographics_template.py' first to create the template.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        sys.exit(1)
    
    print(f"✓ Found {len(excel_data)} sheets")
    
    # Mapping of sheet names to table names
    sheet_to_table = {
        'Regions': 'ref_regions',
        'Schools': 'ref_schools',
        'GradeLevels': 'ref_grade_levels',
        'SubjectAreas': 'ref_subject_areas',
        'TeachingExperience': 'ref_teaching_experience',
        'InterventionComponents': 'ref_intervention_components',
        'PerformanceOutcomes': 'ref_performance_outcomes',
        'LearningElements': 'ref_learning_elements',
        'SkillsImprovement': 'ref_skills_improvement',
        'Configuration': 'ref_configuration'
    }
    
    # Load each sheet into database
    print("\n📥 Loading data into database...")
    for sheet_name, table_name in sheet_to_table.items():
        if sheet_name in excel_data:
            df = excel_data[sheet_name]
            
            # Convert column names to lowercase for consistency
            df.columns = [col.lower() for col in df.columns]
            
            try:
                df.to_sql(table_name, engine, if_exists='append', index=False)
                print(f"   ✓ {sheet_name}: Loaded {len(df)} records into {table_name}")
            except Exception as e:
                print(f"   ✗ {sheet_name}: Error - {e}")
        else:
            print(f"   ⚠ {sheet_name}: Sheet not found in Excel file")
    
    print("\n✅ Demographics loaded successfully!")

def display_summary(engine):
    """Display summary of loaded data"""
    
    print("\n" + "="*60)
    print("📊 DEMOGRAPHICS SUMMARY")
    print("="*60)
    
    queries = [
        ("Regions", "SELECT COUNT(*) as count FROM ref_regions WHERE active = TRUE"),
        ("Schools", "SELECT COUNT(*) as count FROM ref_schools WHERE active = TRUE"),
        ("Grade Levels", "SELECT COUNT(*) as count FROM ref_grade_levels WHERE active = TRUE"),
        ("Subject Areas", "SELECT COUNT(*) as count FROM ref_subject_areas WHERE active = TRUE"),
        ("Teaching Experience Levels", "SELECT COUNT(*) as count FROM ref_teaching_experience WHERE active = TRUE"),
        ("Intervention Components", "SELECT COUNT(*) as count FROM ref_intervention_components WHERE active = TRUE"),
        ("Performance Outcomes", "SELECT COUNT(*) as count FROM ref_performance_outcomes WHERE active = TRUE"),
        ("Learning Elements", "SELECT COUNT(*) as count FROM ref_learning_elements WHERE active = TRUE"),
        ("Skills for Improvement", "SELECT COUNT(*) as count FROM ref_skills_improvement WHERE active = TRUE"),
    ]
    
    with engine.connect() as conn:
        for name, query in queries:
            result = conn.execute(text(query))
            count = result.fetchone()[0]
            print(f"   {name}: {count} active")
    
    print("="*60)
    
    # Show configuration
    print("\n⚙️  SYSTEM CONFIGURATION")
    print("="*60)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT setting, value FROM ref_configuration"))
        for row in result:
            print(f"   {row[0]}: {row[1]}")
    print("="*60)

def main():
    """Main function"""
    
    print("\n" + "="*60)
    print("🚀 DEMOGRAPHICS LOADER")
    print("="*60 + "\n")
    
    # Connect to database
    engine = get_database_connection()
    print("✓ Database connection established\n")
    
    # Create tables
    create_reference_tables(engine)
    
    # Clear existing data
    clear_reference_data(engine)
    
    # Load from Excel
    load_excel_to_database('demographics_config.xlsx', engine)
    
    # Display summary
    display_summary(engine)
    
    print("\n🎉 Done! Your frontend will now use these demographics.")
    print("   Restart Streamlit to see the changes.")

if __name__ == "__main__":
    main()




