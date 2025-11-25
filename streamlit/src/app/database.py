"""
Database connection and management module
"""

import streamlit as st
import os
import time

def init_database(db_path):
    """Initialize DuckDB connection for education dataset (not cached - cache at call site).
    Recovers from corruption by removing WAL and recreating the DB file if needed.
    Automatically loads Parquet files from gold bucket if tables don't exist.
    """
    # Lazy import to avoid module-level initialization issues
    try:
        import duckdb
    except ImportError as e:
        raise Exception(f"Failed to import DuckDB: {e}")
    except Exception as e:
        # Catch any pybind11 or other initialization errors
        raise Exception(f"DuckDB initialization error: {e}")
    
    # Create data directory if it doesn't exist
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    # Attempt normal connection, then progressively recover on failure
    try:
        conn = duckdb.connect(db_path, read_only=False)
        result = conn.execute("SELECT 1").fetchone()
        if not result:
            raise Exception("Connection test failed")
        try:
            _configure_s3_if_enabled(conn)
        except Exception:
            pass
    except Exception:
        # Step 1: remove WAL if present and retry
        wal_path = f"{db_path}.wal"
        try:
            if os.path.exists(wal_path):
                os.remove(wal_path)
        except Exception:
            pass
        try:
            conn = duckdb.connect(db_path, read_only=False)
            result = conn.execute("SELECT 1").fetchone()
            if not result:
                raise Exception("Connection test failed after WAL cleanup")
        except Exception:
            # Step 2: move corrupted DB aside and recreate a new one
            try:
                if os.path.exists(db_path):
                    backup_path = f"{db_path}.corrupt-{int(time.time())}"
                    os.rename(db_path, backup_path)
            except Exception:
                pass
            conn = duckdb.connect(db_path, read_only=False)
            try:
                _configure_s3_if_enabled(conn)
            except Exception:
                pass
    
    # Check if tables exist (with error handling)
    try:
        tables = conn.execute("SHOW TABLES").fetchall()
        table_names = [table[0] for table in tables]
        
        # Always try to load tables from gold bucket (will skip if already exist)
        # This ensures Feedback tables are loaded even if other tables already exist
        try:
            success, msg = load_parquet_from_gold_bucket(conn)
            if success:
                # Re-check tables after loading
                tables = conn.execute("SHOW TABLES").fetchall()
                table_names = [table[0] for table in tables]
        except Exception:
            # Silently fail - tables might not be available yet
            pass
        
        if table_names:
            # Create materialized views for performance (silently fail if issues)
            try:
                create_materialized_views(conn)
            except Exception:
                pass
    except Exception:
        # If there's an error checking tables, just continue
        # The connection is still valid
        pass
    
    return conn


def check_tables_exist(conn):
    """Check if required tables exist in the database"""
    try:
        tables = conn.execute("SHOW TABLES").fetchall()
        table_names = [table[0] for table in tables]
        required_tables = ['schools', 'students', 'assessments', 'interventions']
        missing = [t for t in required_tables if t not in table_names]
        return len(missing) == 0, missing
    except Exception:
        return False, []


def _configure_s3_if_enabled(conn):
    """Configure DuckDB to work with MinIO/S3 if enabled"""
    if os.getenv("MINIO_ENABLED", "false").lower() == "true":
        try:
            # Only configure if not already configured to avoid conflicts
            region = os.getenv('MINIO_REGION', 'us-east-1')
            endpoint = os.getenv('MINIO_URL', 'http://minio:9000').replace('http://', '').replace('https://', '')
            access_key = os.getenv('MINIO_ACCESS_KEY', 'minioadmin')
            secret_key = os.getenv('MINIO_SECRET_KEY', 'minioadmin')
            
            # Try to install and load httpfs extension
            try:
                conn.execute("INSTALL httpfs;")
            except:
                pass  # Extension might already be installed
            
            try:
                conn.execute("LOAD httpfs;")
            except:
                pass  # Extension might already be loaded
            
            # Set S3 configuration
            conn.execute(f"SET s3_region='{region}';")
            conn.execute(f"SET s3_endpoint='{endpoint}';")
            conn.execute(f"SET s3_access_key_id='{access_key}';")
            conn.execute(f"SET s3_secret_access_key='{secret_key}';")
            conn.execute("SET s3_url_style='path';")  # Required for MinIO
            conn.execute("SET s3_use_ssl=false;")  # MinIO uses HTTP by default in dev
        except Exception:
            # Silently fail if S3 configuration doesn't work
            # This allows the app to continue working with local files only
            pass


def read_parquet_from_s3(conn, key: str):
    """Read a Parquet file from S3/MinIO using DuckDB"""
    bucket = os.getenv("MINIO_BUCKET", "gold")
    endpoint = os.getenv("MINIO_URL", "http://minio:9000")
    # DuckDB expects the endpoint without protocol in S3 paths
    s3_path = f"s3://{bucket}/{key}"
    query = f"SELECT * FROM '{s3_path}'"
    try:
        return conn.execute(query).fetchdf()
    except Exception as e:
        raise Exception(f"Error reading from S3: {str(e)}")


def get_s3_path(bucket: str, key: str) -> str:
    """Get S3 path for DuckDB queries"""
    return f"s3://{bucket}/{key}"


def create_materialized_views(conn):
    """Create materialized views for common queries"""
    try:
        # Equity quintiles materialized view
        conn.execute("""
            CREATE OR REPLACE VIEW mv_equity_quintiles AS
            WITH quintiles AS (
                SELECT 
                    s.school_id,
                    s.deprivation_index,
                    NTILE(5) OVER (ORDER BY s.deprivation_index) as quintile
                FROM schools s
            ),
            scores_by_quintile AS (
                SELECT 
                    q.quintile,
                    AVG(a.score) as avg_score,
                    COUNT(*) as assessment_count,
                    COUNT(DISTINCT st.student_id_hash) as student_count,
                    STDDEV(a.score) as std_score
                FROM assessments a
                JOIN students st ON a.student_id_hash = st.student_id_hash
                JOIN quintiles q ON st.school_id = q.school_id
                GROUP BY q.quintile
            )
            SELECT * FROM scores_by_quintile
        """)
        
        # Scores by region and subject
        conn.execute("""
            CREATE OR REPLACE VIEW mv_scores_by_region_subject AS
            SELECT 
                s.region,
                a.subject,
                AVG(a.score) as avg_score,
                COUNT(*) as assessment_count,
                COUNT(DISTINCT st.student_id_hash) as student_count
            FROM assessments a
            JOIN students st ON a.student_id_hash = st.student_id_hash
            JOIN schools s ON st.school_id = s.school_id
            GROUP BY s.region, a.subject
        """)
        
        # Intervention coverage monthly
        conn.execute("""
            CREATE OR REPLACE VIEW mv_intervention_coverage_monthly AS
            SELECT 
                DATE_TRUNC('month', i.start_date) as month,
                i.type,
                s.region,
                COUNT(DISTINCT i.intervention_id) as intervention_count,
                COUNT(DISTINCT i.school_id) as school_count,
                COUNT(DISTINCT st.student_id_hash) as student_count
            FROM interventions i
            JOIN schools s ON i.school_id = s.school_id
            LEFT JOIN students st ON st.school_id = s.school_id
            GROUP BY DATE_TRUNC('month', i.start_date), i.type, s.region
        """)
        
        conn.commit()
    except Exception as e:
        # Views might already exist or there might be schema issues
        # Silently fail - views are optional performance optimizations
        pass

def get_schema_info(conn):
    """Get table schema information for AI context"""
    try:
        if conn is None:
            return []
        
        # Get all table schemas for education dataset
        tables = conn.execute("SHOW TABLES").fetchall()
        if not tables:
            # Try to reload tables from gold bucket if enabled
            try:
                success, msg = load_parquet_from_gold_bucket(conn)
                if success:
                    # Retry getting tables
                    tables = conn.execute("SHOW TABLES").fetchall()
            except Exception as e:
                # Silently fail - tables might not be available
                pass
        
        all_schemas = []
        for table in tables:
            table_name = table[0]
            try:
                schema = conn.execute(f"DESCRIBE {table_name}").fetchdf()
                schema['table_name'] = table_name
                all_schemas.extend(schema.to_dict('records'))
            except Exception as e:
                # Skip this table if there's an error describing it
                continue
        return all_schemas
    except Exception as e:
        # Return empty list on any error
        return []

def get_database_values(conn):
    """Get distinct values from database for fuzzy matching"""
    regions = []
    interventions = []
    
    try:
        regions_df = conn.execute("SELECT DISTINCT region FROM schools ORDER BY region").fetchdf()
        interventions_df = conn.execute("SELECT DISTINCT type FROM interventions ORDER BY type").fetchdf()
        regions = regions_df['region'].tolist() if not regions_df.empty else []
        interventions = interventions_df['type'].tolist() if not interventions_df.empty else []
    except:
        pass
    
    return regions, interventions


def load_parquet_from_gold_bucket(conn, specific_table=None):
    """Load Parquet files from the gold bucket into DuckDB tables.
    Maps file names to table names (e.g., 'schools.parquet' -> 'schools' table).
    Also loads tables registered in FastAPI /schemas endpoint.
    
    Args:
        conn: DuckDB connection
        specific_table: Optional table name to load specifically (preserves exact case)
    
    Returns:
        Tuple of (success: bool, message: str) - True if at least one table was loaded
    """
    # Check if S3 is enabled
    minio_enabled = os.getenv("MINIO_ENABLED", "false").lower() == "true"
    if not minio_enabled:
        return False, f"MinIO is not enabled. Set MINIO_ENABLED=true in your .env file. Current value: {os.getenv('MINIO_ENABLED', 'not set')}"
    
    bucket = os.getenv("MINIO_BUCKET", "gold")
    minio_url = os.getenv("MINIO_URL", "http://minio:9000")
    
    # Ensure S3 is configured before trying to load
    try:
        _configure_s3_if_enabled(conn)
    except Exception as config_error:
        return False, f"Failed to configure S3/MinIO connection: {str(config_error)}. Check MINIO_URL={minio_url}"
    
    # Expected table names - include Feedback tables
    expected_tables = ['schools', 'students', 'assessments', 'interventions', 'Feedback', 'Feedback_Forms']
    
    # Also fetch table names from FastAPI schemas (preserve original case)
    fastapi_table_map = {}  # Map lowercase to original case
    try:
        import requests
        fastapi_url = os.getenv("FASTAPI_URL_EXTERNAL") or os.getenv("FASTAPI_URL")
        if not fastapi_url:
            fastapi_url = "http://fastapi-bi-backend:8000"
        
        schemas_url = f"{fastapi_url}/schemas"
        response = requests.get(schemas_url, timeout=10)
        if response.status_code == 200:
            schemas = response.json().get("schemas", [])
            for schema in schemas:
                original_name = schema.get("schema_name", "")
                if original_name:
                    lower_name = original_name.lower()
                    fastapi_table_map[lower_name] = original_name
                    # Add FastAPI tables to expected tables (avoid duplicates)
                    if lower_name not in expected_tables:
                        expected_tables.append(lower_name)
    except Exception as e:
        # Log but continue - FastAPI might not be available
        print(f"Warning: Could not fetch schemas from FastAPI: {e}")
    
    # If specific table requested, prioritize it
    if specific_table:
        specific_lower = specific_table.lower()
        if specific_lower not in expected_tables:
            expected_tables.insert(0, specific_lower)  # Add to front of list
        fastapi_table_map[specific_lower] = specific_table  # Use exact case provided
    
    loaded_tables = []
    errors = []
    
    # Try to load each expected table from Parquet files
    for table_name_lower in expected_tables:
        # Use original case if available, otherwise use lowercase
        table_name = fastapi_table_map.get(table_name_lower, table_name_lower)
        try:
            # Try different possible file paths/names with both original case and lowercase
            possible_paths = [
                f"{table_name}.parquet",  # Original case: school_intervention_v1.parquet
                f"{table_name_lower}.parquet",  # Lowercase: school_intervention_v1.parquet
                f"{table_name}/{table_name}.parquet",  # Nested original case
                f"{table_name_lower}/{table_name_lower}.parquet",  # Nested lowercase
            ]
            
            loaded = False
            last_error = None
            for parquet_path in possible_paths:
                s3_path = f"s3://{bucket}/{parquet_path}"
                try:
                    # Test if file exists by trying to read a single row
                    test_query = f"SELECT * FROM '{s3_path}' LIMIT 1"
                    conn.execute(test_query).fetchone()
                    
                    # File exists, create table from it (drop existing if any)
                    # Use original case for table name to match what's in SQL queries
                    drop_query = f"DROP TABLE IF EXISTS {table_name}"
                    conn.execute(drop_query)
                    
                    create_query = f"""
                        CREATE TABLE {table_name} AS 
                        SELECT * FROM '{s3_path}'
                    """
                    conn.execute(create_query)
                    print(f"✅ Loaded table '{table_name}' from {s3_path}")
                    loaded_tables.append(table_name)
                    loaded = True
                    break  # Successfully loaded, move to next table
                except Exception as path_error:
                    last_error = str(path_error)
                    # This path doesn't exist, try next one
                    continue
            
            if not loaded:
                error_msg = f"Table '{table_name}' not found in bucket '{bucket}'. Tried paths: {', '.join(possible_paths)}"
                if last_error:
                    error_msg += f" Last error: {last_error}"
                errors.append(error_msg)
            
            if loaded and specific_table and table_name_lower == specific_table.lower():
                # Found the specific table we were looking for
                return True, f"Successfully loaded table '{table_name}'"
        except Exception as e:
            errors.append(f"Error loading table '{table_name_lower}': {str(e)}")
            continue
    
    # Return results
    if loaded_tables:
        msg = f"Loaded {len(loaded_tables)} table(s): {', '.join(loaded_tables)}"
        if errors:
            msg += f"\nWarnings: {'; '.join(errors)}"
        return True, msg
    else:
        error_summary = "; ".join(errors) if errors else "No tables found in MinIO"
        return False, f"Failed to load tables. {error_summary}. Bucket: {bucket}, MinIO URL: {minio_url}"

