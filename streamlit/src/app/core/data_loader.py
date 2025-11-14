"""
Data loading utilities for reading Parquet files from MinIO
"""

import pandas as pd
from typing import Optional
import streamlit as st


def load_parquet_from_minio(bucket: str, object_name: str) -> Optional[pd.DataFrame]:
    """
    Load a Parquet file from MinIO into a pandas DataFrame
    
    Args:
        bucket: MinIO bucket name
        object_name: Object key/path in the bucket
        
    Returns:
        pandas DataFrame or None if loading fails
    """
    try:
        from .minio_client import get_s3fs_storage_options
        
        storage_options = get_s3fs_storage_options()
        s3_path = f"s3://{bucket}/{object_name}"
        
        # Try using s3fs with pandas
        try:
            df = pd.read_parquet(s3_path, storage_options=storage_options)
            return df
        except Exception as e1:
            # Fallback: use MinIO client to download and read
            try:
                from minio import Minio
                from .minio_client import get_minio_config
                import io
                import pyarrow.parquet as pq
                
                config = get_minio_config()
                endpoint = config["endpoint"].replace("http://", "").replace("https://", "")
                
                client = Minio(
                    endpoint,
                    access_key=config["access_key"],
                    secret_key=config["secret_key"],
                    secure=config["secure"]
                )
                
                # Get object from MinIO
                response = client.get_object(bucket, object_name)
                data = response.read()
                response.close()
                response.release_conn()
                
                # Read Parquet from bytes
                parquet_file = pq.ParquetFile(io.BytesIO(data))
                df = parquet_file.read().to_pandas()
                
                return df
            except Exception as e2:
                st.error(f"Failed to load Parquet file using both methods: {str(e1)}, {str(e2)}")
                return None
                
    except ImportError as e:
        st.error(f"Required library not installed: {str(e)}. Install with: pip install s3fs pyarrow")
        return None
    except Exception as e:
        st.error(f"Error loading Parquet file '{object_name}': {str(e)}")
        return None


def load_parquet_to_df(bucket: str, object_name: str, sample_rows: Optional[int] = None) -> Optional[pd.DataFrame]:
    """
    Alias for load_parquet_from_minio with optional sampling
    
    Args:
        bucket: MinIO bucket name
        object_name: Object key/path in the bucket
        sample_rows: Optional number of rows to sample (if None, loads full dataset)
        
    Returns:
        pandas DataFrame or None if loading fails
    """
    df = load_parquet_from_minio(bucket, object_name)
    
    if df is not None and sample_rows is not None and sample_rows > 0:
        # Sample rows for performance
        if len(df) > sample_rows:
            df = df.head(sample_rows)
    
    return df

