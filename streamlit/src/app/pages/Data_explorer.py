"""
Data Explorer Page - Preview, filter, and analyze data from all Parquet files in MinIO gold bucket
"""

import streamlit as st
import pandas as pd
import numpy as np
import sys
import os
import requests

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import require_auth
from core.minio_client import get_minio_config, list_parquet_files
from core.data_loader import load_parquet_from_minio

# Require authentication
require_auth()


def load_all_parquet_files(bucket: str) -> tuple[pd.DataFrame, list[str]]:
    """
    Load all parquet files from MinIO bucket and combine them
    
    Returns:
        Tuple of (combined DataFrame, list of loaded file names)
    """
    parquet_files = list_parquet_files(bucket)
    
    if not parquet_files:
        return None, []
    
    dataframes = []
    loaded_files = []
    
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    for idx, file_name in enumerate(parquet_files):
        status_text.text(f"Loading {file_name}... ({idx + 1}/{len(parquet_files)})")
        progress_bar.progress((idx + 1) / len(parquet_files))
        
        df = load_parquet_from_minio(bucket, file_name)
        if df is not None:
            # Add source file column to track origin
            df['_source_file'] = file_name
            dataframes.append(df)
            loaded_files.append(file_name)
    
    progress_bar.empty()
    status_text.empty()
    
    if not dataframes:
        return None, []
    
    # Combine all dataframes
    combined_df = pd.concat(dataframes, ignore_index=True)
    return combined_df, loaded_files


def main():
    st.title("🔎 Data Explorer")
    st.markdown("Explore and filter data from all Parquet files in MinIO gold bucket")
    
    # Get MinIO configuration
    config = get_minio_config()
    
    # Check if data is already loaded
    df = st.session_state.get("combined_df", None)
    loaded_files = st.session_state.get("loaded_files", [])
    
    # Load button or auto-load on first visit
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Load/Refresh All Parquet Files", type="primary"):
            with st.spinner("Loading all Parquet files from MinIO gold bucket..."):
                df, loaded_files = load_all_parquet_files(config["bucket"])
                
                if df is None or len(df) == 0:
                    st.warning("⚠️ No Parquet files found in the gold bucket. Please upload files to MinIO.")
                    st.stop()
                
                # Store in session state
                st.session_state.combined_df = df
                st.session_state.loaded_files = loaded_files
                st.success(f"✅ Successfully loaded {len(loaded_files)} file(s)!")
                st.rerun()
    
    # Auto-load on first visit if not already loaded
    if df is None:
        with st.spinner("Loading all Parquet files from MinIO gold bucket..."):
            df, loaded_files = load_all_parquet_files(config["bucket"])
            
            if df is None or len(df) == 0:
                st.warning("⚠️ No Parquet files found in the gold bucket. Please upload files to MinIO.")
                st.stop()
            
            # Store in session state
            st.session_state.combined_df = df
            st.session_state.loaded_files = loaded_files
            st.success(f"✅ Successfully loaded {len(loaded_files)} file(s)!")
    
    # Get DataFrame from session state (refresh after potential load)
    df = st.session_state.get("combined_df", None)
    loaded_files = st.session_state.get("loaded_files", [])
    
    if df is None or len(df) == 0:
        st.warning("⚠️ No data loaded. Click the button above to load all Parquet files from the gold bucket.")
        st.stop()
    
    st.info(f"📊 Exploring data from **{len(loaded_files)} file(s)**: {', '.join(loaded_files)} ({len(df):,} total rows, {len(df.columns)} columns)")
    
    # Basic statistics
    with st.expander("📈 Dataset Overview", expanded=True):
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Rows", f"{len(df):,}")
        with col2:
            st.metric("Total Columns", len(df.columns))
        with col3:
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            st.metric("Numeric Columns", len(numeric_cols))
        with col4:
            categorical_cols = df.select_dtypes(include=['object', 'category']).columns
            st.metric("Categorical Columns", len(categorical_cols))
    
    # Schema information
    with st.expander("📋 Schema Information", expanded=False):
        schema_df = pd.DataFrame({
            "Column": df.columns,
            "Data Type": [str(dtype) for dtype in df.dtypes],
            "Non-Null Count": [df[col].notna().sum() for col in df.columns],
            "Null Count": [df[col].isna().sum() for col in df.columns],
            "Null Percentage": [f"{(df[col].isna().sum() / len(df) * 100):.2f}%" for col in df.columns]
        })
        st.dataframe(schema_df, width='stretch')
    
    # Filters section
    st.subheader("🔍 Filters")
    
    # Initialize filtered DataFrame
    filtered_df = df.copy()
    
    # Create filter controls - exclude _source_file from automatic filters
    numeric_cols = [col for col in df.select_dtypes(include=[np.number]).columns.tolist() if col != '_source_file']
    categorical_cols = [col for col in df.select_dtypes(include=['object', 'category']).columns.tolist() if col != '_source_file']
    
    # Source file filter (if multiple files loaded)
    if len(loaded_files) > 1 and '_source_file' in df.columns:
        selected_sources = st.multiselect(
            "📁 Filter by Source File",
            options=loaded_files,
            default=loaded_files,
            help="Select which source files to include in the filtered view"
        )
        if selected_sources:
            filtered_df = filtered_df[filtered_df['_source_file'].isin(selected_sources)]
        else:
            filtered_df = filtered_df.iloc[0:0]  # Empty dataframe if no sources selected
    
    filter_cols = st.columns(min(3, len(numeric_cols) + len(categorical_cols)))
    col_idx = 0
    
    # Numeric filters
    for col in numeric_cols[:5]:  # Limit to first 5 numeric columns
        if col_idx >= len(filter_cols):
            break
        with filter_cols[col_idx]:
            min_val = float(df[col].min())
            max_val = float(df[col].max())
            selected_range = st.slider(
                f"{col}",
                min_value=min_val,
                max_value=max_val,
                value=(min_val, max_val),
                help=f"Filter {col} between {min_val} and {max_val}"
            )
            filtered_df = filtered_df[
                (filtered_df[col] >= selected_range[0]) &
                (filtered_df[col] <= selected_range[1])
            ]
        col_idx += 1
    
    # Categorical filters
    for col in categorical_cols[:5]:  # Limit to first 5 categorical columns
        if col_idx >= len(filter_cols):
            break
        unique_vals = df[col].dropna().unique().tolist()
        if len(unique_vals) <= 50:  # Only show multiselect if reasonable number of values
            with filter_cols[col_idx]:
                selected_vals = st.multiselect(
                    f"{col}",
                    options=unique_vals,
                    default=unique_vals,
                    help=f"Filter {col} by selected values"
                )
                if selected_vals:
                    filtered_df = filtered_df[filtered_df[col].isin(selected_vals)]
        col_idx += 1
    
    # Show filter results
    st.subheader("📊 Filtered Data Preview")
    st.write(f"Showing {len(filtered_df):,} rows (filtered from {len(df):,} total rows)")
    
    # Data preview
    preview_rows = st.slider("Number of rows to preview", 10, 100, 50)
    st.dataframe(filtered_df.head(preview_rows), width='stretch')
    
    # Basic statistics for filtered data
    if len(filtered_df) > 0:
        st.subheader("📈 Statistics (Filtered Data)")
        
        # Show source file distribution if multiple files
        if len(loaded_files) > 1 and '_source_file' in filtered_df.columns:
            st.write("**Source File Distribution:**")
            source_counts = filtered_df['_source_file'].value_counts()
            st.dataframe(source_counts.reset_index().rename(columns={"index": "Source File", "_source_file": "Row Count"}))
            st.write("---")
        
        # Numeric statistics
        if len(numeric_cols) > 0:
            st.write("**Numeric Columns:**")
            numeric_stats = filtered_df[numeric_cols].describe()
            st.dataframe(numeric_stats, width='stretch')
        
        # Categorical statistics
        if len(categorical_cols) > 0:
            st.write("**Categorical Columns:**")
            for col in categorical_cols[:5]:  # Limit to first 5
                value_counts = filtered_df[col].value_counts().head(10)
                if len(value_counts) > 0:
                    st.write(f"**{col}** (top 10 values):")
                    st.dataframe(value_counts.reset_index().rename(columns={"index": "Value", col: "Count"}))
    
    # View Registered Schemas Section
    st.subheader("📋 Registered Schemas")
    
    with st.expander("🔍 View Schema Metadata", expanded=False):
        # Get FastAPI URL
        fastapi_url = os.getenv("FASTAPI_URL_EXTERNAL") or os.getenv("FASTAPI_URL", "http://fastapi-backend:8000")
        
        if st.button("🔄 Refresh Schemas", type="secondary"):
            st.rerun()
        
        try:
            # Fetch schemas from FastAPI
            response = requests.get(
                f"{fastapi_url}/schemas",
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                schemas = data.get("schemas", [])
                
                if not schemas:
                    st.info("📭 No schemas registered yet.")
                else:
                    # Schema selector
                    schema_names = [s["schema_name"] for s in schemas]
                    selected_schema_name = st.selectbox(
                        "Select Schema to View",
                        options=schema_names,
                        help="Choose a schema to view its columns and descriptions"
                    )
                    
                    if selected_schema_name:
                        selected_schema = next((s for s in schemas if s["schema_name"] == selected_schema_name), None)
                        
                        if selected_schema:
                            st.write(f"**Schema:** `{selected_schema['schema_name']}`")
                            if selected_schema.get("description"):
                                st.write(f"**Description:** {selected_schema['description']}")
                            
                            columns = selected_schema.get("columns", {})
                            
                            if columns:
                                st.write(f"**Columns:** {len(columns)}")
                                
                                # Display columns in a table format
                                columns_data = []
                                for col_name, col_info in columns.items():
                                    if isinstance(col_info, dict):
                                        col_type = col_info.get("type", "unknown")
                                        col_desc = col_info.get("description", "")
                                    else:
                                        # Old format
                                        col_type = str(col_info)
                                        col_desc = ""
                                    
                                    columns_data.append({
                                        "Column Name": col_name,
                                        "Type": col_type,
                                        "Description": col_desc
                                    })
                                
                                if columns_data:
                                    columns_df = pd.DataFrame(columns_data)
                                    st.dataframe(
                                        columns_df,
                                        use_container_width=True,
                                        hide_index=True
                                    )
                            else:
                                st.info("No columns registered for this schema.")
            else:
                st.error(f"❌ Failed to fetch schemas: {response.status_code}")
                st.json(response.json())
                
        except requests.exceptions.RequestException as e:
            st.error(f"❌ Error connecting to FastAPI: {str(e)}")
            st.info(f"💡 Make sure FastAPI is running at: {fastapi_url}")
        except Exception as e:
            st.error(f"❌ Unexpected error: {str(e)}")
    
    # Create New Column Section
    st.subheader("➕ Create New Column")
    
    with st.expander("📝 Add Column to Schema Metadata", expanded=False):
        # Get FastAPI URL
        fastapi_url = os.getenv("FASTAPI_URL_EXTERNAL") or os.getenv("FASTAPI_URL", "http://fastapi-backend:8000")
        
        # Schema name input
        schema_name = st.text_input(
            "Schema Name",
            value=loaded_files[0].replace('.parquet', '') if loaded_files else "default_schema",
            help="Name of the schema to update in metadata.db"
        )
        
        # Column details
        col1, col2 = st.columns(2)
        with col1:
            new_column_name = st.text_input(
                "New Column Name",
                placeholder="e.g., calculated_score",
                help="Name of the new column to add"
            )
        with col2:
            column_type = st.selectbox(
                "Column Type",
                options=["string", "integer", "float", "date", "boolean"],
                help="Data type of the new column"
            )
        
        column_description = st.text_area(
            "Column Description",
            placeholder="Describe what this column represents...",
            help="Optional description of the column"
        )
        
        overwrite = st.checkbox(
            "Overwrite if exists",
            value=False,
            help="If checked, will overwrite existing column definition"
        )
        
        if st.button("💾 Register Column in Metadata", type="primary"):
            if not schema_name or not new_column_name:
                st.error("❌ Please provide both schema name and column name.")
            else:
                try:
                    # Prepare payload according to SchemaRegistration model
                    # Note: The endpoint expects columns: Dict[str, Dict[str, str]]
                    # but add_column_to_schema expects Dict[str, str] (column_name -> column_type)
                    # We'll send in the SchemaRegistration format and let the backend handle it
                    payload = {
                        "schema_name": schema_name,
                        "columns": {
                            new_column_name: {
                                "type": column_type,
                                "description": column_description or ""
                            }
                        },
                        "overwrite": overwrite,
                        "description": ""
                    }
                    
                    # Call FastAPI endpoint
                    response = requests.put(
                        f"{fastapi_url}/schemas/update",
                        json=payload,
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        result = response.json()
                        st.success(f"✅ Successfully registered column '{new_column_name}' in schema '{schema_name}'!")
                        st.info(f"📝 **Column Details:**\n- **Name:** `{new_column_name}`\n- **Type:** `{column_type}`\n- **Description:** {column_description or '*(no description)*'}")
                        st.info("💡 Scroll up to the '📋 Registered Schemas' section to view all columns with descriptions.")
                    else:
                        error_detail = response.json().get("detail", "Unknown error")
                        st.error(f"❌ Failed to register column: {error_detail}")
                        st.json(response.json())
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"❌ Error connecting to FastAPI: {str(e)}")
                    st.info(f"💡 Make sure FastAPI is running at: {fastapi_url}")
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()

