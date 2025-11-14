"""
====================================================================
DATABASE UTILITIES
Helper functions for database operations
====================================================================
"""

import streamlit as st
import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, text
from datetime import datetime
import os

# ====================================================================
# DATABASE CONNECTION
# ====================================================================

@st.cache_resource
def get_database_connection():
    """
    Create and return database connection based on configuration.
    Checks Streamlit secrets first, then falls back to SQLite.
    """
    
    try:
        # Try to get database config from Streamlit secrets
        if "db_type" in st.secrets:
            db_type = st.secrets["db_type"]
        else:
            # Check individual database configs
            if "postgres" in st.secrets:
                db_type = "postgresql"
            elif "mysql" in st.secrets:
                db_type = "mysql"
            else:
                db_type = "sqlite"
        
        if db_type == "postgresql":
            host = st.secrets.get("db_host", "localhost")
            port = st.secrets.get("db_port", "5432")
            database = st.secrets.get("db_name", "survey_db")
            username = st.secrets.get("db_user", "user")
            password = st.secrets.get("db_password", "password")
            
            connection_string = f'postgresql://{username}:{password}@{host}:{port}/{database}'
            engine = create_engine(connection_string)
            
        elif db_type == "mysql":
            host = st.secrets.get("db_host", "localhost")
            port = st.secrets.get("db_port", "3306")
            database = st.secrets.get("db_name", "survey_db")
            username = st.secrets.get("db_user", "user")
            password = st.secrets.get("db_password", "password")
            
            connection_string = f'mysql+pymysql://{username}:{password}@{host}:{port}/{database}'
            engine = create_engine(connection_string)
            
        else:  # SQLite (default)
            db_path = st.secrets.get("db_path", "teacher_survey.db")
            connection_string = f'sqlite:///{db_path}'
            engine = create_engine(connection_string)
            
            # Create tables if they don't exist
            create_tables_if_not_exist(engine)
        
        # Test connection
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        
        return engine
        
    except Exception as e:
        st.warning(f"Database connection failed: {str(e)}. Using SQLite fallback.")
        
        # Fallback to SQLite
        db_path = "teacher_survey.db"
        connection_string = f'sqlite:///{db_path}'
        engine = create_engine(connection_string)
        create_tables_if_not_exist(engine)
        
        return engine

# ====================================================================
# TABLE CREATION
# ====================================================================

def create_tables_if_not_exist(engine):
    """Create database tables if they don't exist."""
    
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS teacher_survey_responses (
        response_id TEXT PRIMARY KEY,
        survey_date DATE NOT NULL,
        teacher_id TEXT NOT NULL,
        school_id TEXT NOT NULL,
        school_name TEXT,
        region TEXT NOT NULL,
        teaching_experience_years INTEGER,
        grade_level TEXT,
        subject_area TEXT,
        class_size INTEGER,
        intervention_status TEXT,
        intervention_duration_months INTEGER DEFAULT 0,
        intervention_component_1 INTEGER DEFAULT 0,
        intervention_component_2 INTEGER DEFAULT 0,
        intervention_component_3 INTEGER DEFAULT 0,
        intervention_component_4 INTEGER DEFAULT 0,
        b1_overall_performance INTEGER,
        b2_problem_solving INTEGER,
        b3_critical_thinking INTEGER,
        b4_collaboration INTEGER,
        b5_communication INTEGER,
        b6_engagement INTEGER,
        b7_behavior INTEGER,
        b8_persistence INTEGER,
        c1_performance_change INTEGER,
        c2_problem_solving_change INTEGER,
        c3_engagement_change INTEGER,
        c4_communication_change INTEGER,
        c5_behavior_change INTEGER,
        d1_intervention_impact INTEGER,
        d2_skill_most_improved_1 TEXT,
        d2_skill_most_improved_2 TEXT,
        d2_skill_most_improved_3 TEXT,
        d3_component_rank_1 TEXT,
        d3_component_rank_2 TEXT,
        d3_component_rank_3 TEXT,
        e1_important_element_1 TEXT,
        e1_important_element_2 TEXT,
        e1_important_element_3 TEXT,
        e2_teaching_practice_change TEXT,
        f1_performance_factors TEXT,
        f2_effective_practice TEXT,
        f3_challenges TEXT,
        f4_additional_comments TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(create_table_sql))
            conn.commit()
    except Exception as e:
        st.error(f"Error creating tables: {str(e)}")

# ====================================================================
# QUERY EXECUTION
# ====================================================================

def execute_query(engine, query, params=None):
    """
    Execute a SELECT query and return results as DataFrame.
    """
    try:
        with engine.connect() as conn:
            if params:
                result = conn.execute(text(query), params)
            else:
                result = conn.execute(text(query))
            
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
            return df
    except Exception as e:
        st.error(f"Query execution error: {str(e)}")
        return None

def execute_insert(engine, query, params):
    """
    Execute an INSERT query.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text(query), params)
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Insert error: {str(e)}")
        return False

def execute_update(engine, query, params):
    """
    Execute an UPDATE query.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text(query), params)
            conn.commit()
        return True
    except Exception as e:
        st.error(f"Update error: {str(e)}")
        return False

# ====================================================================
# DATA INSERTION
# ====================================================================

def insert_survey_response(engine, response_data):
    """
    Insert a new survey response into the database.
    
    Args:
        engine: SQLAlchemy engine
        response_data: Dictionary containing all response fields
    
    Returns:
        bool: True if successful, False otherwise
    """
    
    insert_query = """
    INSERT INTO teacher_survey_responses (
        response_id, survey_date, teacher_id, school_id, school_name, region,
        teaching_experience_years, grade_level, subject_area, class_size,
        intervention_status, intervention_duration_months,
        intervention_component_1, intervention_component_2, 
        intervention_component_3, intervention_component_4,
        b1_overall_performance, b2_problem_solving, b3_critical_thinking,
        b4_collaboration, b5_communication, b6_engagement,
        b7_behavior, b8_persistence,
        c1_performance_change, c2_problem_solving_change, c3_engagement_change,
        c4_communication_change, c5_behavior_change,
        d1_intervention_impact, d2_skill_most_improved_1, d2_skill_most_improved_2,
        d2_skill_most_improved_3, d3_component_rank_1, d3_component_rank_2,
        d3_component_rank_3, e1_important_element_1, e1_important_element_2,
        e1_important_element_3, e2_teaching_practice_change,
        f1_performance_factors, f2_effective_practice, f3_challenges,
        f4_additional_comments
    ) VALUES (
        :response_id, :survey_date, :teacher_id, :school_id, :school_name, :region,
        :teaching_experience_years, :grade_level, :subject_area, :class_size,
        :intervention_status, :intervention_duration_months,
        :intervention_component_1, :intervention_component_2,
        :intervention_component_3, :intervention_component_4,
        :b1_overall_performance, :b2_problem_solving, :b3_critical_thinking,
        :b4_collaboration, :b5_communication, :b6_engagement,
        :b7_behavior, :b8_persistence,
        :c1_performance_change, :c2_problem_solving_change, :c3_engagement_change,
        :c4_communication_change, :c5_behavior_change,
        :d1_intervention_impact, :d2_skill_most_improved_1, :d2_skill_most_improved_2,
        :d2_skill_most_improved_3, :d3_component_rank_1, :d3_component_rank_2,
        :d3_component_rank_3, :e1_important_element_1, :e1_important_element_2,
        :e1_important_element_3, :e2_teaching_practice_change,
        :f1_performance_factors, :f2_effective_practice, :f3_challenges,
        :f4_additional_comments
    )
    """
    
    return execute_insert(engine, insert_query, response_data)

# ====================================================================
# DATA RETRIEVAL
# ====================================================================

def get_all_responses(engine, limit=None):
    """Get all survey responses."""
    query = "SELECT * FROM teacher_survey_responses ORDER BY survey_date DESC"
    if limit:
        query += f" LIMIT {limit}"
    return execute_query(engine, query)

def get_responses_by_region(engine, region):
    """Get responses for a specific region."""
    query = "SELECT * FROM teacher_survey_responses WHERE region = :region ORDER BY survey_date DESC"
    return execute_query(engine, query, {"region": region})

def get_responses_by_school(engine, school_id):
    """Get responses for a specific school."""
    query = "SELECT * FROM teacher_survey_responses WHERE school_id = :school_id ORDER BY survey_date DESC"
    return execute_query(engine, query, {"school_id": school_id})

def get_unique_values(engine, column):
    """Get unique values for a column."""
    query = f"SELECT DISTINCT {column} FROM teacher_survey_responses WHERE {column} IS NOT NULL ORDER BY {column}"
    result = execute_query(engine, query)
    return result[column].tolist() if result is not None else []

# ====================================================================
# STATISTICS QUERIES
# ====================================================================

def get_summary_stats(engine):
    """Get overall summary statistics."""
    query = """
    SELECT 
        COUNT(*) as total_responses,
        COUNT(DISTINCT teacher_id) as total_teachers,
        COUNT(DISTINCT school_id) as total_schools,
        COUNT(DISTINCT region) as total_regions,
        AVG(b1_overall_performance) as avg_performance,
        MIN(survey_date) as first_survey,
        MAX(survey_date) as latest_survey
    FROM teacher_survey_responses
    """
    return execute_query(engine, query)

def get_regional_comparison(engine):
    """Get performance comparison by region."""
    query = """
    SELECT 
        region,
        intervention_status,
        COUNT(*) as n_responses,
        AVG(b1_overall_performance) as avg_performance,
        AVG(b2_problem_solving) as avg_problem_solving,
        AVG(b6_engagement) as avg_engagement
    FROM teacher_survey_responses
    GROUP BY region, intervention_status
    ORDER BY region, intervention_status
    """
    return execute_query(engine, query)

def get_temporal_trends(engine):
    """Get performance trends over time."""
    query = """
    SELECT 
        survey_date,
        intervention_status,
        region,
        AVG(b1_overall_performance) as avg_performance,
        COUNT(*) as n_responses
    FROM teacher_survey_responses
    GROUP BY survey_date, intervention_status, region
    ORDER BY survey_date
    """
    return execute_query(engine, query)

# ====================================================================
# VALIDATION
# ====================================================================

def check_duplicate_response(engine, teacher_id, survey_date):
    """Check if a teacher has already submitted a response for a given date."""
    query = """
    SELECT COUNT(*) as count
    FROM teacher_survey_responses
    WHERE teacher_id = :teacher_id AND survey_date = :survey_date
    """
    result = execute_query(engine, query, {
        "teacher_id": teacher_id,
        "survey_date": survey_date
    })
    return result['count'].iloc[0] > 0 if result is not None else False

# ====================================================================
# UTILITY FUNCTIONS
# ====================================================================

def generate_response_id():
    """Generate a unique response ID."""
    from datetime import datetime
    import random
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_suffix = random.randint(1000, 9999)
    return f"RESP_{timestamp}_{random_suffix}"

def format_date(date_obj):
    """Format date for database insertion."""
    if isinstance(date_obj, str):
        return date_obj
    return date_obj.strftime("%Y-%m-%d")

# ====================================================================
# DYNAMIC OPTIONS FROM DEMOGRAPHICS (Excel-driven)
# ====================================================================

def get_active_regions(engine):
    """Get list of active regions from reference table."""
    query = "SELECT region_id, region_name FROM ref_regions WHERE active = TRUE ORDER BY region_name"
    try:
        result = execute_query(engine, query)
        if result is not None and not result.empty:
            return result['region_id'].tolist()
        else:
            # Fallback to unique values from responses
            return get_unique_values(engine, 'region')
    except:
        # Fallback if ref table doesn't exist
        return get_unique_values(engine, 'region')

def get_active_schools(engine, region_id=None):
    """Get list of active schools, optionally filtered by region."""
    if region_id:
        query = "SELECT school_id, school_name FROM ref_schools WHERE active = TRUE AND region_id = :region_id ORDER BY school_name"
        params = {"region_id": region_id}
    else:
        query = "SELECT school_id, school_name FROM ref_schools WHERE active = TRUE ORDER BY school_name"
        params = None
    
    try:
        result = execute_query(engine, query, params)
        if result is not None and not result.empty:
            return result.to_dict('records')  # Returns list of {school_id, school_name}
        else:
            # Fallback
            return []
    except:
        return []

def get_grade_levels(engine):
    """Get list of active grade levels."""
    query = "SELECT grade_id, grade_name FROM ref_grade_levels WHERE active = TRUE ORDER BY grade_id"
    try:
        result = execute_query(engine, query)
        if result is not None and not result.empty:
            return result['grade_name'].tolist()
        else:
            return ['Kindergarten', 'Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Grade 5',
                   'Grade 6', 'Grade 7', 'Grade 8', 'Grade 9', 'Grade 10', 'Grade 11', 'Grade 12']
    except:
        return ['Kindergarten', 'Grade 1', 'Grade 2', 'Grade 3', 'Grade 4', 'Grade 5',
               'Grade 6', 'Grade 7', 'Grade 8', 'Grade 9', 'Grade 10', 'Grade 11', 'Grade 12']

def get_subject_areas(engine):
    """Get list of active subject areas."""
    query = "SELECT subject_id, subject_name FROM ref_subject_areas WHERE active = TRUE ORDER BY subject_name"
    try:
        result = execute_query(engine, query)
        if result is not None and not result.empty:
            return result['subject_name'].tolist()
        else:
            return ['Mathematics', 'Reading/Language Arts', 'Science', 'Social Studies', 
                   'Arts', 'Physical Education', 'Music', 'All Subjects']
    except:
        return ['Mathematics', 'Reading/Language Arts', 'Science', 'Social Studies',
               'Arts', 'Physical Education', 'Music', 'All Subjects']

def get_teaching_experience_levels(engine):
    """Get list of teaching experience levels."""
    query = "SELECT experience_name FROM ref_teaching_experience WHERE active = TRUE ORDER BY min_years"
    try:
        result = execute_query(engine, query)
        if result is not None and not result.empty:
            return result['experience_name'].tolist()
        else:
            return ["0-2 years", "3-5 years", "6-10 years", "11-20 years", "20+ years"]
    except:
        return ["0-2 years", "3-5 years", "6-10 years", "11-20 years", "20+ years"]

def get_intervention_components(engine):
    """Get list of active intervention components."""
    query = "SELECT component_id, component_name FROM ref_intervention_components WHERE active = TRUE ORDER BY component_id"
    try:
        result = execute_query(engine, query)
        if result is not None and not result.empty:
            return result.to_dict('records')  # Returns list of {component_id, component_name}
        else:
            return [
                {'component_id': 'COMP1', 'component_name': 'Professional Development'},
                {'component_id': 'COMP2', 'component_name': 'Curriculum Materials'},
                {'component_id': 'COMP3', 'component_name': 'Technology Integration'},
                {'component_id': 'COMP4', 'component_name': 'Collaborative Learning'}
            ]
    except:
        return [
            {'component_id': 'COMP1', 'component_name': 'Professional Development'},
            {'component_id': 'COMP2', 'component_name': 'Curriculum Materials'},
            {'component_id': 'COMP3', 'component_name': 'Technology Integration'},
            {'component_id': 'COMP4', 'component_name': 'Collaborative Learning'}
        ]

def get_performance_outcomes(engine):
    """Get list of active performance outcomes."""
    query = "SELECT outcome_id, outcome_name, db_column FROM ref_performance_outcomes WHERE active = TRUE ORDER BY outcome_id"
    try:
        result = execute_query(engine, query)
        if result is not None and not result.empty:
            return result.to_dict('records')
        else:
            return []
    except:
        return []

def get_learning_elements(engine):
    """Get list of active learning elements."""
    query = "SELECT element_name FROM ref_learning_elements WHERE active = TRUE ORDER BY element_id"
    try:
        result = execute_query(engine, query)
        if result is not None and not result.empty:
            return result['element_name'].tolist()
        else:
            return [
                "Clear learning objectives",
                "Active engagement",
                "Prior knowledge connections",
                "Personalized learning",
                "Motivation and interest",
                "Supportive environment",
                "Regular feedback",
                "Real-world application"
            ]
    except:
        return [
            "Clear learning objectives",
            "Active engagement",
            "Prior knowledge connections",
            "Personalized learning",
            "Motivation and interest",
            "Supportive environment",
            "Regular feedback",
            "Real-world application"
        ]

def get_skills_improvement(engine):
    """Get list of skills that can be improved."""
    query = "SELECT skill_name FROM ref_skills_improvement WHERE active = TRUE ORDER BY skill_id"
    try:
        result = execute_query(engine, query)
        if result is not None and not result.empty:
            return result['skill_name'].tolist()
        else:
            return [
                "Academic knowledge", "Problem-solving", "Critical thinking", "Communication",
                "Collaboration", "Creativity", "Engagement", "Behavior",
                "Self-regulation", "Persistence"
            ]
    except:
        return [
            "Academic knowledge", "Problem-solving", "Critical thinking", "Communication",
            "Collaboration", "Creativity", "Engagement", "Behavior",
            "Self-regulation", "Persistence"
        ]

def get_system_configuration(engine):
    """Get system configuration settings."""
    query = "SELECT setting, value FROM ref_configuration"
    try:
        result = execute_query(engine, query)
        if result is not None and not result.empty:
            return dict(zip(result['setting'], result['value']))
        else:
            return {}
    except:
        return {}

