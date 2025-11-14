"""
Data Transformation Component for Streamlit
Provides UI and functions for transforming data before visualization
"""

import streamlit as st
import pandas as pd
import re
from typing import Optional, List, Dict, Any


def parse_country_time_series(df: pd.DataFrame, column_name: str, start_year: Optional[int] = None) -> pd.DataFrame:
    """
    Parse a column containing country codes and time series values
    Example: "AT: 44577 47091 50242..." -> Country | Year | Value
    """
    result_rows = []
    
    for idx, row in df.iterrows():
        value_str = str(row[column_name])
        
        # Extract country code and values
        # Pattern: "AT: 44577 47091 50242..." or "AT : 44577 47091..."
        # Handle both formats with or without spaces around colon
        pattern = r'([A-Z]{2})\s*:\s*((?:[:\s]*\d+[:\s]*|[:\s]*d[:\s]*|[:\s]*bd[:\s]*)+)'
        matches = re.findall(pattern, value_str)
        
        if not matches:
            # Try alternative pattern without quotes
            pattern = r'"([A-Z]{2})\s*:\s*((?:[:\s]*\d+[:\s]*|[:\s]*d[:\s]*|[:\s]*bd[:\s]*)+)"'
            matches = re.findall(pattern, value_str)
        
        for country_code, values_str in matches:
            # Clean and split values
            # Remove extra spaces and split by whitespace
            values_str = re.sub(r'\s+', ' ', values_str.strip())
            values = values_str.split()
            
            # Determine start year (default to 2000 if not provided)
            current_year = start_year if start_year else 2000
            
            for year_idx, val in enumerate(values):
                # Skip missing values
                val_clean = val.strip()
                if val_clean in [':', 'd', 'bd', '', ':', ':d', ':bd']:
                    current_year += 1
                    continue
                
                try:
                    # Try to extract numeric value (handle cases like "119372 d" or "114254 bd")
                    numeric_match = re.search(r'(\d+)', val_clean)
                    if numeric_match:
                        numeric_val = float(numeric_match.group(1))
                        result_rows.append({
                            **{col: row[col] for col in df.columns if col != column_name},
                            'Country': country_code,
                            'Year': current_year + year_idx,
                            'Value': numeric_val
                        })
                except (ValueError, AttributeError):
                    continue
    
    return pd.DataFrame(result_rows) if result_rows else df


def unpivot_data(df: pd.DataFrame, id_vars: List[str], value_vars: List[str], 
                 var_name: str = 'Variable', value_name: str = 'Value') -> pd.DataFrame:
    """Unpivot/melt data from wide to long format"""
    return pd.melt(df, id_vars=id_vars, value_vars=value_vars, 
                   var_name=var_name, value_name=value_name)


def pivot_data(df: pd.DataFrame, index: List[str], columns: str, values: str) -> pd.DataFrame:
    """Pivot data from long to wide format"""
    return df.pivot_table(index=index, columns=columns, values=values, aggfunc='first').reset_index()


def split_column(df: pd.DataFrame, column_name: str, delimiter: str, 
                new_column_names: Optional[List[str]] = None) -> pd.DataFrame:
    """Split a column into multiple columns"""
    split_df = df[column_name].str.split(delimiter, expand=True)
    
    if new_column_names:
        split_df.columns = new_column_names[:len(split_df.columns)]
    else:
        split_df.columns = [f"{column_name}_{i+1}" for i in range(len(split_df.columns))]
    
    return pd.concat([df.drop(columns=[column_name]), split_df], axis=1)


def extract_regex(df: pd.DataFrame, column_name: str, pattern: str, 
                 new_column_name: str) -> pd.DataFrame:
    """Extract values using regex pattern"""
    df[new_column_name] = df[column_name].str.extract(pattern)
    return df


def filter_data(df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
    """Apply filters to dataframe"""
    filtered_df = df.copy()
    
    for column, condition in filters.items():
        if column in filtered_df.columns:
            if isinstance(condition, dict):
                if 'min' in condition:
                    filtered_df = filtered_df[filtered_df[column] >= condition['min']]
                if 'max' in condition:
                    filtered_df = filtered_df[filtered_df[column] <= condition['max']]
                if 'values' in condition:
                    filtered_df = filtered_df[filtered_df[column].isin(condition['values'])]
            elif isinstance(condition, (list, tuple)):
                filtered_df = filtered_df[filtered_df[column].isin(condition)]
            else:
                filtered_df = filtered_df[filtered_df[column] == condition]
    
    return filtered_df


def aggregate_data(df: pd.DataFrame, group_by: List[str], 
                  aggregations: Dict[str, List[str]]) -> pd.DataFrame:
    """Aggregate data by groups"""
    return df.groupby(group_by).agg(aggregations).reset_index()


def render_transformation_ui(conn, table_name: str):
    """Render UI for data transformation"""
    st.markdown("### 🔄 Data Transformation")
    st.info("💡 Transform your data to prepare it for visualization")
    
    try:
        # Load current table data
        df = conn.execute(f"SELECT * FROM {table_name} LIMIT 1000").fetchdf()
        
        if df.empty:
            st.warning("⚠️ Table is empty. No data to transform.")
            return None
        
        # Show current data info
        st.markdown(f"**Current data:** {len(df)} rows × {len(df.columns)} columns")
        
        # Transformation options
        transform_type = st.selectbox(
            "Select transformation:",
            [
                "-- Select transformation --",
                "Parse Country Time Series",
                "Unpivot (Wide to Long)",
                "Pivot (Long to Wide)",
                "Split Column",
                "Extract with Regex",
                "Filter Data",
                "Aggregate Data"
            ],
            key="transform_type"
        )
        
        if transform_type == "-- Select transformation --":
            return None
        
        # Store original dataframe in session state
        if 'original_df' not in st.session_state or st.session_state.get('current_table') != table_name:
            st.session_state.original_df = df.copy()
            st.session_state.current_table = table_name
        
        transformed_df = None
        
        if transform_type == "Parse Country Time Series":
            st.markdown("#### Parse Country Time Series")
            st.markdown("Extract country codes and time series values from a string column")
            st.markdown("**Example format:** `\"AT: 44577 47091 50242...\"` → Country | Year | Value")
            
            # Find columns that might contain country time series data
            # Look for columns with string data that might contain country codes
            potential_columns = []
            for col in df.columns:
                sample_val = str(df[col].iloc[0]) if len(df) > 0 else ""
                if re.search(r'[A-Z]{2}\s*:', sample_val):
                    potential_columns.append(col)
            
            if not potential_columns:
                potential_columns = df.columns.tolist()
            
            column_to_parse = st.selectbox(
                "Select column to parse:",
                potential_columns,
                key="parse_column"
            )
            
            # Show sample of selected column
            if column_to_parse:
                st.info(f"**Sample value:** `{str(df[column_to_parse].iloc[0])[:100]}...`")
            
            start_year = st.number_input(
                "Start year (optional, defaults to 2000):",
                value=2000,
                min_value=1900,
                max_value=2100,
                key="parse_start_year"
            )
            
            if st.button("🔄 Parse Data"):
                with st.spinner("Parsing country time series data..."):
                    transformed_df = parse_country_time_series(df, column_to_parse, int(start_year))
                    if len(transformed_df) > 0:
                        st.success(f"✅ Parsed {len(transformed_df)} rows")
                        st.info(f"📊 Extracted {transformed_df['Country'].nunique()} countries with {transformed_df['Year'].nunique()} years")
                    else:
                        st.warning("⚠️ No data extracted. Check the column format.")
        
        elif transform_type == "Unpivot (Wide to Long)":
            st.markdown("#### Unpivot Data (Wide to Long)")
            st.markdown("Convert wide format to long format")
            
            id_vars = st.multiselect(
                "ID columns (keep as-is):",
                df.columns.tolist(),
                key="unpivot_id"
            )
            
            value_vars = st.multiselect(
                "Value columns (to unpivot):",
                [col for col in df.columns.tolist() if col not in id_vars],
                key="unpivot_values"
            )
            
            var_name = st.text_input("Variable name:", value="Variable", key="unpivot_var")
            value_name = st.text_input("Value name:", value="Value", key="unpivot_val")
            
            if st.button("🔄 Unpivot Data") and id_vars and value_vars:
                with st.spinner("Unpivoting data..."):
                    transformed_df = unpivot_data(df, id_vars, value_vars, var_name, value_name)
                    st.success(f"✅ Unpivoted to {len(transformed_df)} rows")
        
        elif transform_type == "Pivot (Long to Wide)":
            st.markdown("#### Pivot Data (Long to Wide)")
            st.markdown("Convert long format to wide format")
            
            index_cols = st.multiselect(
                "Index columns:",
                df.columns.tolist(),
                key="pivot_index"
            )
            
            columns_col = st.selectbox(
                "Column to pivot:",
                [col for col in df.columns.tolist() if col not in index_cols],
                key="pivot_columns"
            )
            
            values_col = st.selectbox(
                "Values column:",
                [col for col in df.columns.tolist() if col not in index_cols + [columns_col]],
                key="pivot_values"
            )
            
            if st.button("🔄 Pivot Data") and index_cols:
                with st.spinner("Pivoting data..."):
                    transformed_df = pivot_data(df, index_cols, columns_col, values_col)
                    st.success(f"✅ Pivoted to {len(transformed_df)} rows")
        
        elif transform_type == "Split Column":
            st.markdown("#### Split Column")
            st.markdown("Split a column into multiple columns")
            
            column_to_split = st.selectbox(
                "Column to split:",
                df.columns.tolist(),
                key="split_column"
            )
            
            delimiter = st.text_input("Delimiter:", value=",", key="split_delimiter")
            
            new_cols_input = st.text_input(
                "New column names (comma-separated, optional):",
                key="split_new_cols"
            )
            
            new_column_names = None
            if new_cols_input:
                new_column_names = [col.strip() for col in new_cols_input.split(",")]
            
            if st.button("🔄 Split Column"):
                with st.spinner("Splitting column..."):
                    transformed_df = split_column(df, column_to_split, delimiter, new_column_names)
                    st.success(f"✅ Column split into {len(transformed_df.columns)} columns")
        
        elif transform_type == "Extract with Regex":
            st.markdown("#### Extract with Regex")
            st.markdown("Extract values using a regular expression pattern")
            
            column_to_extract = st.selectbox(
                "Column to extract from:",
                df.columns.tolist(),
                key="extract_column"
            )
            
            pattern = st.text_input("Regex pattern:", value=r"(\d+)", key="extract_pattern")
            new_column_name = st.text_input("New column name:", value="extracted", key="extract_new")
            
            if st.button("🔄 Extract"):
                with st.spinner("Extracting values..."):
                    transformed_df = extract_regex(df, column_to_extract, pattern, new_column_name)
                    st.success(f"✅ Values extracted to '{new_column_name}' column")
        
        elif transform_type == "Filter Data":
            st.markdown("#### Filter Data")
            st.markdown("Apply filters to the data")
            
            filter_column = st.selectbox(
                "Column to filter:",
                df.columns.tolist(),
                key="filter_column"
            )
            
            filter_type = st.selectbox(
                "Filter type:",
                ["Equals", "Contains", "Greater than", "Less than", "Between", "In list"],
                key="filter_type"
            )
            
            filter_value = None
            if filter_type == "Equals":
                if df[filter_column].dtype in ['int64', 'float64']:
                    filter_value = st.number_input("Value:", key="filter_val")
                else:
                    unique_vals = df[filter_column].unique()[:50]
                    filter_value = st.selectbox("Value:", unique_vals, key="filter_val")
            
            elif filter_type == "Contains":
                filter_value = st.text_input("Contains:", key="filter_val")
            
            elif filter_type == "Greater than":
                filter_value = st.number_input("Greater than:", key="filter_val")
            
            elif filter_type == "Less than":
                filter_value = st.number_input("Less than:", key="filter_val")
            
            elif filter_type == "Between":
                min_val = st.number_input("Min:", key="filter_min")
                max_val = st.number_input("Max:", key="filter_max")
                filter_value = {'min': min_val, 'max': max_val}
            
            elif filter_type == "In list":
                unique_vals = df[filter_column].unique()[:50]
                filter_value = st.multiselect("Values:", unique_vals, key="filter_val")
            
            if st.button("🔄 Apply Filter") and filter_value is not None:
                with st.spinner("Filtering data..."):
                    filters = {filter_column: filter_value}
                    transformed_df = filter_data(df, filters)
                    st.success(f"✅ Filtered to {len(transformed_df)} rows")
        
        elif transform_type == "Aggregate Data":
            st.markdown("#### Aggregate Data")
            st.markdown("Group and aggregate data")
            
            group_by = st.multiselect(
                "Group by columns:",
                df.columns.tolist(),
                key="agg_group"
            )
            
            numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
            agg_columns = st.multiselect(
                "Columns to aggregate:",
                numeric_cols,
                key="agg_cols"
            )
            
            agg_functions = st.multiselect(
                "Aggregation functions:",
                ["mean", "sum", "count", "min", "max", "std"],
                default=["mean"],
                key="agg_funcs"
            )
            
            if st.button("🔄 Aggregate Data") and group_by and agg_columns:
                with st.spinner("Aggregating data..."):
                    aggregations = {col: agg_functions for col in agg_columns}
                    transformed_df = aggregate_data(df, group_by, aggregations)
                    st.success(f"✅ Aggregated to {len(transformed_df)} rows")
        
        # Show transformed data preview
        if transformed_df is not None and not transformed_df.empty:
            st.markdown("---")
            st.markdown("### 📊 Transformed Data Preview")
            st.dataframe(transformed_df.head(100), use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                new_table_name = st.text_input(
                    "New table name (to save):",
                    value=f"{table_name}_transformed",
                    key="new_table_name"
                )
                if st.button("💾 Save as New Table") and new_table_name:
                    try:
                        # Register dataframe and create table
                        conn.register("temp_transformed", transformed_df)
                        conn.execute(f"CREATE OR REPLACE TABLE {new_table_name} AS SELECT * FROM temp_transformed")
                        st.success(f"✅ Saved as table '{new_table_name}'")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Error saving table: {str(e)}")
            
            with col2:
                if st.button("🔄 Use Transformed Data"):
                    # Store transformed data for visualization
                    st.session_state.transformed_df = transformed_df
                    st.session_state.use_transformed = True
                    st.success("✅ Using transformed data for visualization")
                    st.rerun()
            
            return transformed_df
        
        return None
        
    except Exception as e:
        st.error(f"❌ Error in transformation: {str(e)}")
        return None

