#!/usr/bin/env python3
"""
Script to clear DuckDB database and MinIO storage
"""

import os
import sys
import boto3
from botocore.exceptions import ClientError
import duckdb

# MinIO configuration
MINIO_ENDPOINT = os.getenv("MINIO_URL", "http://localhost:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")

# Database path
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "education.duckdb")
DB_WAL_PATH = f"{DB_PATH}.wal"


def clear_duckdb():
    """Clear DuckDB database by dropping all tables"""
    print("🗄️  Clearing DuckDB database...")
    
    if not os.path.exists(DB_PATH):
        print("   ℹ️  Database file doesn't exist, nothing to clear.")
        return
    
    try:
        # Connect to database
        conn = duckdb.connect(DB_PATH, read_only=False)
        
        # Get all tables
        tables = conn.execute("SHOW TABLES").fetchall()
        table_names = [table[0] for table in tables]
        
        if table_names:
            print(f"   Found {len(table_names)} table(s): {', '.join(table_names)}")
            
            # Drop all tables
            for table_name in table_names:
                try:
                    conn.execute(f"DROP TABLE IF EXISTS {table_name}")
                    print(f"   ✓ Dropped table: {table_name}")
                except Exception as e:
                    print(f"   ⚠️  Error dropping table {table_name}: {e}")
            
            # Drop all views
            try:
                views = conn.execute("SELECT viewname FROM pg_views WHERE schemaname = 'main'").fetchall()
                for view in views:
                    view_name = view[0]
                    try:
                        conn.execute(f"DROP VIEW IF EXISTS {view_name}")
                        print(f"   ✓ Dropped view: {view_name}")
                    except Exception as e:
                        print(f"   ⚠️  Error dropping view {view_name}: {e}")
            except Exception:
                # pg_views might not be available, try alternative
                try:
                    conn.execute("DROP VIEW IF EXISTS mv_equity_quintiles")
                    conn.execute("DROP VIEW IF EXISTS mv_scores_by_region_subject")
                    conn.execute("DROP VIEW IF EXISTS mv_intervention_coverage_monthly")
                except:
                    pass
            
            conn.commit()
        else:
            print("   ℹ️  No tables found in database.")
        
        conn.close()
        
        # Optionally remove WAL file
        if os.path.exists(DB_WAL_PATH):
            try:
                os.remove(DB_WAL_PATH)
                print(f"   ✓ Removed WAL file: {DB_WAL_PATH}")
            except Exception as e:
                print(f"   ⚠️  Could not remove WAL file: {e}")
        
        print("   ✅ DuckDB database cleared successfully!")
        
    except Exception as e:
        print(f"   ❌ Error clearing DuckDB: {e}")
        # If connection fails, try to delete the database file
        try:
            if os.path.exists(DB_PATH):
                os.remove(DB_PATH)
                print(f"   ✓ Deleted database file: {DB_PATH}")
            if os.path.exists(DB_WAL_PATH):
                os.remove(DB_WAL_PATH)
                print(f"   ✓ Deleted WAL file: {DB_WAL_PATH}")
        except Exception as e2:
            print(f"   ❌ Error deleting database files: {e2}")


def clear_minio():
    """Clear MinIO storage by deleting all objects from all buckets"""
    print("\n📦 Clearing MinIO storage...")
    
    try:
        # Create S3 client
        s3_client = boto3.client(
            "s3",
            endpoint_url=MINIO_ENDPOINT,
            aws_access_key_id=MINIO_ACCESS_KEY,
            aws_secret_access_key=MINIO_SECRET_KEY,
            region_name=os.getenv("MINIO_REGION", "us-east-1"),
        )
        
        # List all buckets
        try:
            response = s3_client.list_buckets()
            buckets = [bucket["Name"] for bucket in response.get("Buckets", [])]
        except ClientError as e:
            print(f"   ❌ Error listing buckets: {e}")
            return
        
        if not buckets:
            print("   ℹ️  No buckets found in MinIO.")
            return
        
        print(f"   Found {len(buckets)} bucket(s): {', '.join(buckets)}")
        
        # Delete all objects from each bucket
        for bucket_name in buckets:
            print(f"\n   📂 Processing bucket: {bucket_name}")
            
            try:
                # List all objects in the bucket
                paginator = s3_client.get_paginator("list_objects_v2")
                pages = paginator.paginate(Bucket=bucket_name)
                
                object_count = 0
                objects_to_delete = []
                
                for page in pages:
                    if "Contents" in page:
                        for obj in page["Contents"]:
                            objects_to_delete.append({"Key": obj["Key"]})
                            object_count += 1
                
                if objects_to_delete:
                    print(f"      Found {object_count} object(s)")
                    
                    # Delete objects in batches of 1000 (S3 limit)
                    for i in range(0, len(objects_to_delete), 1000):
                        batch = objects_to_delete[i:i + 1000]
                        try:
                            s3_client.delete_objects(
                                Bucket=bucket_name,
                                Delete={"Objects": batch}
                            )
                            print(f"      ✓ Deleted {len(batch)} object(s)")
                        except ClientError as e:
                            print(f"      ⚠️  Error deleting objects: {e}")
                    
                    print(f"      ✅ Cleared {object_count} object(s) from bucket '{bucket_name}'")
                else:
                    print(f"      ℹ️  Bucket '{bucket_name}' is already empty")
                
            except ClientError as e:
                print(f"      ⚠️  Error processing bucket '{bucket_name}': {e}")
        
        print("\n   ✅ MinIO storage cleared successfully!")
        
    except Exception as e:
        print(f"   ❌ Error clearing MinIO: {e}")
        print(f"   Make sure MinIO is running and accessible at {MINIO_ENDPOINT}")


def main():
    """Main function"""
    print("🧹 Starting storage cleanup...\n")
    
    # Clear DuckDB
    clear_duckdb()
    
    # Clear MinIO
    clear_minio()
    
    print("\n✨ Storage cleanup completed!")


if __name__ == "__main__":
    main()

