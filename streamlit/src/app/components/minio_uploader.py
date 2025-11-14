"""
MinIO Uploader component for uploading raw documents from Streamlit
"""

import os
import requests
import streamlit as st


def render_minio_uploader(conn=None):
    """Render UI for uploading raw files to MinIO via FastAPI backend"""
    minio_enabled_env = os.getenv("MINIO_ENABLED", "false")
    minio_enabled = minio_enabled_env.lower() == "true"

    if not minio_enabled:
        st.info(f"ℹ️ MinIO is disabled. Set `MINIO_ENABLED=true` in your `.env` file to use this feature.")
        st.info(f"🔍 Debug: MINIO_ENABLED env var value is: `{minio_enabled_env}`")
        return

    # Modern upload UI
    st.markdown("""
    <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem; border-radius: 15px; margin-bottom: 2rem;'>
        <h2 style='color: white; margin: 0;'>📤 Upload Files</h2>
        <p style='color: rgba(255,255,255,0.9); margin: 0.5rem 0 0 0; font-size: 1rem;'>
            Upload CSV, TSV, or any data files to your storage
        </p>
    </div>
    """, unsafe_allow_html=True)

    fastapi_url = os.getenv("FASTAPI_URL", "http://fastapi-backend:8000")
    if os.getenv("FASTAPI_URL_EXTERNAL"):
        fastapi_url = os.getenv("FASTAPI_URL_EXTERNAL")

    # Use same bucket configuration as backend and dashboard
    default_bucket = os.getenv("MINIO_BUCKET", "eduzmena")
    default_prefix = os.getenv("MINIO_RAW_PREFIX", "raw/")

    with st.form("minio_upload_form"):
        # File uploader with better styling - now supports multiple files
        uploaded_files = st.file_uploader(
            "📁 Choose file(s) to upload",
            type=['csv', 'tsv', 'txt', 'json', 'parquet'],
            accept_multiple_files=True,
            help="Supported formats: CSV, TSV, JSON, Parquet, and text files. You can select multiple files at once."
        )
        
        # Auto-load option (only show for CSV/TSV when files are selected)
        auto_load_checkbox = False
        if conn and uploaded_files:
            has_delimited = any(
                f.name.lower().endswith('.csv') or f.name.lower().endswith('.tsv')
                for f in (uploaded_files if isinstance(uploaded_files, list) else [uploaded_files])
            )
            if has_delimited:
                st.markdown("---")
                auto_load_checkbox = st.checkbox(
                    "🔄 Automatically load CSV/TSV files into database after upload",
                    value=True,
                    help="Load CSV/TSV files into DuckDB immediately after upload for visualization"
                )
        
        st.markdown("---")
        submit = st.form_submit_button(
            "🚀 Upload File(s)",
            use_container_width=True,
            type="primary"
        )

    if submit:
        if not uploaded_files:
            st.error("❌ Please select at least one file before uploading.")
            return

        # Normalize to list
        files_list = uploaded_files if isinstance(uploaded_files, list) else [uploaded_files]
        
        # Use multiple file upload endpoint if more than one file
        if len(files_list) > 1:
            # Multiple file upload
            data = {
                "bucket": default_bucket,
                "prefix": default_prefix
            }

            files = []
            for uploaded_file in files_list:
                files.append(
                    ("files", (
                        uploaded_file.name,
                        uploaded_file.getvalue(),
                        uploaded_file.type or "application/octet-stream"
                    ))
                )

            with st.spinner(f"Uploading {len(files_list)} file(s) to MinIO..."):
                try:
                    response = requests.post(
                        f"{fastapi_url}/files/upload-multiple",
                        data=data,
                        files=files,
                        timeout=120  # Longer timeout for multiple files
                    )

                    if response.status_code == 201:
                        result = response.json()
                        successful = result.get('successful', 0)
                        failed = result.get('failed', 0)
                        results = result.get('results', [])
                        errors = result.get('errors', [])
                        
                        if successful > 0:
                            st.success(f"✅ **{successful} file(s) uploaded successfully!**")
                            
                            # Show summary
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("📦 Total Files", len(files_list))
                            with col2:
                                st.metric("✅ Successful", successful)
                            with col3:
                                st.metric("❌ Failed", failed)
                            
                            # Show successful uploads
                            if results:
                                st.markdown("### ✅ Successfully Uploaded Files")
                                for file_result in results:
                                    with st.expander(f"📄 {file_result.get('filename')}", expanded=False):
                                        col1, col2 = st.columns(2)
                                        with col1:
                                            st.metric("📍 Location", f"`{file_result.get('key')}`")
                                            size_bytes = file_result.get("size")
                                            if size_bytes is not None:
                                                size_mb = size_bytes / 1024 / 1024
                                                if size_mb < 1:
                                                    st.metric("📏 Size", f"{size_bytes / 1024:.2f} KB")
                                                else:
                                                    st.metric("📏 Size", f"{size_mb:.2f} MB")
                                        with col2:
                                            st.metric("🗂️ Bucket", f"`{file_result.get('bucket')}`")
                                            if file_result.get('processing'):
                                                st.info("🔄 Processing in background")
                            
                            # Show errors if any
                            if errors:
                                st.markdown("### ❌ Failed Uploads")
                                for error in errors:
                                    st.error(f"**{error.get('filename')}**: {error.get('error')}")
                            
                            # Auto-load CSV/TSV files if requested
                            if auto_load_checkbox and conn:
                                delimited_results = [r for r in results if r.get('processing', False)]
                                if delimited_results:
                                    with st.spinner(f"🔄 Loading {len(delimited_results)} CSV/TSV file(s) into database..."):
                                        try:
                                            from dashboard import load_delimited_file_from_minio_to_table, get_available_tables
                                            
                                            loaded_count = 0
                                            for file_result in delimited_results:
                                                try:
                                                    file_key = file_result.get('key')
                                                    file_name = file_result.get('filename')
                                                    
                                                    # Generate table name from filename
                                                    table_name = os.path.basename(file_key)
                                                    for ext in ['.csv', '.tsv', '_processed.csv', '_processed.tsv']:
                                                        table_name = table_name.replace(ext, '')
                                                    table_name = table_name.replace('.', '_').replace('-', '_')
                                                    
                                                    # Check if table exists and auto-append if schema matches
                                                    existing_tables = get_available_tables(conn)
                                                    append_if_exists = table_name.lower() in [t.lower() for t in existing_tables]
                                                    
                                                    load_delimited_file_from_minio_to_table(conn, file_key, table_name, append_if_exists)
                                                    loaded_count += 1
                                                except Exception as e:
                                                    st.warning(f"⚠️ Failed to load {file_name}: {str(e)}")
                                            
                                            if loaded_count > 0:
                                                st.success(f"✅ **{loaded_count} file(s) loaded into database!**")
                                                st.info("💡 Go to the **Dashboard** tab to visualize your data!")
                                        except Exception as e:
                                            st.warning(f"⚠️ Some files uploaded but failed to load into database: {str(e)}")
                                            st.info("💡 You can manually load them from the Dashboard tab.")
                    else:
                        try:
                            error_detail = response.json()
                        except ValueError:
                            error_detail = response.text
                        st.error(f"❌ Upload failed: {response.status_code} - {error_detail}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Unable to reach FastAPI backend. Ensure the backend is running and accessible.")
                except requests.exceptions.Timeout:
                    st.error("❌ Upload timed out. Try again or upload smaller files.")
                except Exception as exc:
                    st.error(f"❌ Unexpected error during upload: {exc}")
        else:
            # Single file upload (original behavior)
            uploaded_file = files_list[0]
            
            # Use default bucket "data" and prefix
            data = {
                "bucket": default_bucket,
                "prefix": default_prefix
            }

            files = {
                "file": (
                    uploaded_file.name,
                    uploaded_file.getvalue(),
                    uploaded_file.type or "application/octet-stream"
                )
            }

            with st.spinner("Uploading file to MinIO..."):
                try:
                    response = requests.post(
                        f"{fastapi_url}/files/upload",
                        data=data,
                        files=files,
                        timeout=60
                    )

                    if response.status_code == 201:
                        result = response.json()
                        file_ext = uploaded_file.name.lower()
                        is_csv = file_ext.endswith('.csv')
                        is_tsv = file_ext.endswith('.tsv')
                        is_delimited = is_csv or is_tsv
                        is_processing = result.get('processing', False)
                        file_key = result.get('key')
                        
                        # Success message with better styling
                        if is_processing:
                            st.success("✅ **File uploaded successfully!** Processing in background...")
                            file_type = "TSV" if is_tsv else "CSV"
                            st.info(f"🔄 {file_type} file is being processed. The processed file will be saved automatically.")
                        else:
                            st.success("✅ **File uploaded successfully!**")
                        
                        # Display file info in a nicer format
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("📦 File", uploaded_file.name)
                            size_bytes = result.get("size")
                            if size_bytes is not None:
                                size_mb = size_bytes / 1024 / 1024
                                if size_mb < 1:
                                    st.metric("📏 Size", f"{size_bytes / 1024:.2f} KB")
                                else:
                                    st.metric("📏 Size", f"{size_mb:.2f} MB")
                        
                        with col2:
                            st.metric("📍 Location", f"`{file_key}`")
                            st.metric("🗂️ Bucket", f"`{result.get('bucket')}`")
                        
                        # Automatically load CSV/TSV into DuckDB if requested
                        if is_delimited and auto_load_checkbox and conn:
                            with st.spinner("🔄 Loading file into database..."):
                                try:
                                    from dashboard import load_delimited_file_from_minio_to_table, get_available_tables
                                    
                                    # Generate table name from filename
                                    table_name = os.path.basename(file_key)
                                    for ext in ['.csv', '.tsv', '_processed.csv', '_processed.tsv']:
                                        table_name = table_name.replace(ext, '')
                                    table_name = table_name.replace('.', '_').replace('-', '_')
                                    
                                    # Check if table exists and auto-append if schema matches
                                    existing_tables = get_available_tables(conn)
                                    append_if_exists = table_name.lower() in [t.lower() for t in existing_tables]
                                    
                                    result = load_delimited_file_from_minio_to_table(conn, file_key, table_name, append_if_exists)
                                    file_type = "TSV" if is_tsv else "CSV"
                                    
                                    if isinstance(result, tuple):
                                        table_name, action = result
                                        if action == "appended":
                                            st.success(f"✅ **{file_type} data appended to table '{table_name}'!**")
                                            st.info("💡 Data was added to the existing table. Go to the **Dashboard** tab to visualize!")
                                        else:
                                            st.success(f"✅ **{file_type} loaded into database!**")
                                            st.info("💡 Go to the **Dashboard** tab to visualize your data!")
                                    else:
                                        st.success(f"✅ **{file_type} loaded into database!**")
                                        st.info("💡 Go to the **Dashboard** tab to visualize your data!")
                                except Exception as e:
                                    st.warning(f"⚠️ File uploaded but failed to load into database: {str(e)}")
                                    st.info("💡 You can manually load it from the Dashboard tab.")
                        elif is_delimited:
                            if conn:
                                st.info("💡 Enable 'Automatically load into database' to view data in the Dashboard immediately.")
                    else:
                        try:
                            error_detail = response.json()
                        except ValueError:
                            error_detail = response.text
                        st.error(f"❌ Upload failed: {response.status_code} - {error_detail}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Unable to reach FastAPI backend. Ensure the backend is running and accessible.")
                except requests.exceptions.Timeout:
                    st.error("❌ Upload timed out. Try again or upload a smaller file.")
                except Exception as exc:
                    st.error(f"❌ Unexpected error during upload: {exc}")


