"""
S3/MinIO Browser Component for Streamlit
Allows users to browse and preview Parquet files from MinIO
"""

import streamlit as st
import os
import requests


def render_s3_browser(conn):
    """Render S3 browser interface for viewing MinIO objects"""
    minio_enabled_env = os.getenv("MINIO_ENABLED", "false")
    minio_enabled = minio_enabled_env.lower() == "true"
    
    if not minio_enabled:
        st.info(f"ℹ️ MinIO is disabled. Set `MINIO_ENABLED=true` in your `.env` file to use this feature.")
        st.info(f"🔍 Debug: MINIO_ENABLED env var value is: `{minio_enabled_env}`")
        return
    
    st.header("📦 S3/MinIO Browser")
    st.markdown("Browse and preview files stored in MinIO")
    
    # Get FastAPI URL from environment or default
    fastapi_url = os.getenv("FASTAPI_URL", "http://fastapi-backend:8000")
    if os.getenv("FASTAPI_URL_EXTERNAL"):
        fastapi_url = os.getenv("FASTAPI_URL_EXTERNAL")
    
    # Prefix options
    raw_prefix = os.getenv("MINIO_RAW_PREFIX", "raw/")
    parquet_prefix = os.getenv("MINIO_PARQUET_PREFIX", "parquet/")
    
    # Let user choose prefix
    prefix_option = st.selectbox(
        "📁 Browse folder:",
        ["All files", f"Raw files ({raw_prefix})", f"Processed files ({parquet_prefix})"],
        key="s3_prefix_selector"
    )
    
    selected_prefix = ""
    if prefix_option == f"Raw files ({raw_prefix})":
        selected_prefix = raw_prefix
    elif prefix_option == f"Processed files ({parquet_prefix})":
        selected_prefix = parquet_prefix
    
    try:
        # Fetch list of objects from FastAPI
        response = requests.get(
            f"{fastapi_url}/files/list",
            params={"prefix": selected_prefix},
            timeout=5
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if not data.get("enabled", False):
                st.warning("⚠️ MinIO sync endpoints returned disabled status")
                return
            
            objects = data.get("objects", [])
            # Show CSV, TSV and Parquet files
            data_files = [
                obj["key"] for obj in objects 
                if obj["key"].endswith((".parquet", ".csv", ".tsv"))
            ]
            
            if not data_files:
                st.info(f"📭 No data files found in bucket with prefix '{selected_prefix or 'root'}'")
                return
            
            # File selector
            selected_file = st.selectbox(
                "📄 Select a file to preview",
                ["-- Select a file --"] + data_files
            )
            
            if selected_file and selected_file != "-- Select a file --":
                st.markdown(f"**Selected:** `{selected_file}`")
                
                # Preview button
                if st.button("🔍 Preview File"):
                    with st.spinner("Loading data from S3..."):
                        try:
                            # Handle Parquet, CSV and TSV files
                            if selected_file.endswith('.parquet'):
                                from database import read_parquet_from_s3
                                df = read_parquet_from_s3(conn, selected_file)
                            elif selected_file.endswith(('.csv', '.tsv')):
                                # Read CSV/TSV directly from MinIO using DuckDB
                                import pandas as pd
                                import io
                                # Use DuckDB to read delimited file from S3 (auto-detects delimiter)
                                try:
                                    # Try to read via DuckDB S3
                                    bucket = os.getenv('MINIO_BUCKET', 'eduzmena')
                                    df = conn.execute(f"SELECT * FROM read_csv_auto('s3://{bucket}/{selected_file}')").fetchdf()
                                except Exception:
                                    # Fallback: download and read
                                    download_response = requests.post(
                                        f"{fastapi_url}/sync/download",
                                        json={"key": selected_file},
                                        timeout=60
                                    )
                                    if download_response.status_code == 200:
                                        result = download_response.json()
                                        local_path = result.get('local_path')
                                        if selected_file.endswith('.tsv'):
                                            df = pd.read_csv(local_path, delimiter='\t')
                                        else:
                                            df = pd.read_csv(local_path)
                                    else:
                                        raise Exception("Failed to read file")
                            else:
                                raise Exception("Unsupported file type")
                            
                            st.success(f"✅ Loaded {len(df)} rows")
                            
                            # Display metadata
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Rows", len(df))
                            with col2:
                                st.metric("Columns", len(df.columns))
                            with col3:
                                size_mb = df.memory_usage(deep=True).sum() / 1024 / 1024
                                st.metric("Size (approx)", f"{size_mb:.2f} MB")
                            
                            # Display preview
                            st.markdown("### Preview")
                            st.dataframe(df.head(200), use_container_width=True)
                            
                            # Download option (local copy)
                            st.markdown("### Download Options")
                            col1, col2 = st.columns(2)
                            with col1:
                                if st.button("⬇️ Download to Local"):
                                    with st.spinner("Downloading..."):
                                        try:
                                            download_response = requests.post(
                                                f"{fastapi_url}/sync/download",
                                                json={"key": selected_file},
                                                timeout=60
                                            )
                                            if download_response.status_code == 200:
                                                result = download_response.json()
                                                st.success(f"✅ Downloaded to: {result.get('local_path')}")
                                            else:
                                                st.error(f"❌ Download failed: {download_response.text}")
                                        except Exception as e:
                                            st.error(f"❌ Error downloading: {str(e)}")
                            
                        except Exception as e:
                            st.error(f"❌ Error reading file: {str(e)}")
                            st.info("💡 Make sure DuckDB httpfs extension is properly configured for S3 access")
            
            # Show all files
            with st.expander("📋 All Files in Bucket"):
                if objects:
                    st.write(f"**Total files:** {len(objects)}")
                    for obj in objects[:50]:  # Show first 50
                        st.write(f"- `{obj['key']}` ({obj['size']:,} bytes)")
                    if len(objects) > 50:
                        st.write(f"... and {len(objects) - 50} more files")
                else:
                    st.write("No files found")
        
        else:
            st.error(f"❌ Error fetching files: {response.status_code} - {response.text}")
            st.info("💡 Make sure the FastAPI backend is running and accessible")
    
    except requests.exceptions.ConnectionError:
        st.error("❌ Unable to connect to FastAPI backend")
        st.info("💡 Ensure the FastAPI service is running at the configured URL")
    except Exception as e:
        st.error(f"❌ Unexpected error: {str(e)}")

