"""
MinIO client utilities for connecting to MinIO and listing/loading Parquet files
"""

import os
from typing import List, Optional
import streamlit as st


def get_minio_config() -> dict:
    """
    Get MinIO configuration from environment variables
    
    Returns:
        Dictionary with MinIO configuration
    """
    return {
        "endpoint": os.getenv("MINIO_ENDPOINT", "minio:9000"),
        "access_key": os.getenv("MINIO_ACCESS_KEY", "minioadmin"),
        "secret_key": os.getenv("MINIO_SECRET_KEY", "minioadmin"),
        "secure": os.getenv("MINIO_SECURE", "0").lower() in ("1", "true", "yes"),
        "bucket": os.getenv("MINIO_BUCKET", "gold"),
    }


def get_minio_client():
    """
    Create and return a MinIO client instance
    
    Returns:
        MinIO client instance or None if connection fails
    """
    try:
        from minio import Minio
        from minio.error import S3Error
        
        config = get_minio_config()
        
        # Parse endpoint (remove protocol if present)
        endpoint = config["endpoint"].replace("http://", "").replace("https://", "")
        
        client = Minio(
            endpoint,
            access_key=config["access_key"],
            secret_key=config["secret_key"],
            secure=config["secure"]
        )
        
        return client
    except ImportError:
        st.error("⚠️ MinIO library not installed. Install with: pip install minio")
        return None
    except Exception as e:
        st.error(f"⚠️ Failed to create MinIO client: {str(e)}")
        return None


def test_minio_connection() -> tuple[bool, Optional[str]]:
    """
    Test MinIO connection
    
    Returns:
        Tuple of (success: bool, error_message: Optional[str])
    """
    try:
        client = get_minio_client()
        if client is None:
            return False, "MinIO client creation failed"
        
        config = get_minio_config()
        bucket = config["bucket"]
        
        # Try to list buckets or check if bucket exists
        if client.bucket_exists(bucket):
            return True, None
        else:
            return False, f"Bucket '{bucket}' does not exist"
    except Exception as e:
        return False, f"Connection error: {str(e)}"


def list_parquet_files(bucket: str, prefix: Optional[str] = None) -> List[str]:
    """
    List all Parquet files in a MinIO bucket
    
    Args:
        bucket: Bucket name
        prefix: Optional prefix to filter files (e.g., "gold/")
        
    Returns:
        List of object names (keys) for Parquet files
    """
    try:
        client = get_minio_client()
        if client is None:
            return []
        
        parquet_files = []
        
        # List objects in bucket
        objects = client.list_objects(bucket, prefix=prefix, recursive=True)
        
        for obj in objects:
            if obj.object_name.endswith('.parquet'):
                parquet_files.append(obj.object_name)
        
        return sorted(parquet_files)
    except Exception as e:
        st.error(f"Error listing Parquet files: {str(e)}")
        return []


def get_s3fs_storage_options() -> dict:
    """
    Get storage options for s3fs/pandas to read from MinIO
    
    Returns:
        Dictionary of storage options for s3fs
    """
    config = get_minio_config()
    
    # Parse endpoint
    endpoint = config["endpoint"].replace("http://", "").replace("https://", "")
    
    # Build endpoint URL
    if config["secure"]:
        endpoint_url = f"https://{endpoint}"
    else:
        endpoint_url = f"http://{endpoint}"
    
    return {
        "key": config["access_key"],
        "secret": config["secret_key"],
        "client_kwargs": {
            "endpoint_url": endpoint_url
        }
    }

