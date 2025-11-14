"""
Data Source Page - View all Parquet files available in MinIO gold bucket
"""

import streamlit as st
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import require_auth
from core.minio_client import (
    get_minio_config,
    test_minio_connection,
    list_parquet_files
)

# Require authentication
require_auth()


def main():
    st.title("📂 Data Source")
    st.markdown("View all Parquet files available in MinIO gold bucket")
    
    # Get MinIO configuration
    config = get_minio_config()
    
    # Display configuration (read-only)
    with st.expander("🔧 MinIO Configuration", expanded=False):
        st.write(f"**Endpoint:** {config['endpoint']}")
        st.write(f"**Bucket:** {config['bucket']}")
        st.write(f"**Secure:** {config['secure']}")
        st.caption("💡 Configuration is read from environment variables")
    
    # Test connection
    st.subheader("🔌 Connection Status")
    
    if st.button("🔄 Test Connection", type="primary"):
        with st.spinner("Testing MinIO connection..."):
            success, error = test_minio_connection()
            if success:
                st.success("✅ Successfully connected to MinIO!")
            else:
                st.error(f"❌ Connection failed: {error}")
    
    # List Parquet files
    st.subheader("📋 Available Parquet Files")
    
    try:
        parquet_files = list_parquet_files(config["bucket"])
        
        if not parquet_files:
            st.warning("⚠️ No Parquet files found in the bucket. Make sure files are uploaded to MinIO.")
            st.info("💡 Parquet files should have a `.parquet` extension")
            return
        
        # Display all parquet files
        st.write(f"**Total files found:** {len(parquet_files)}")
        
        # Display files in a clean list format
        for idx, file in enumerate(parquet_files, 1):
            st.write(f"{idx}. `{file}`")
            
    except Exception as e:
        st.error(f"❌ Error listing files: {str(e)}")
        st.info("💡 Make sure MinIO is running and accessible, and that the bucket exists.")


if __name__ == "__main__":
    main()

