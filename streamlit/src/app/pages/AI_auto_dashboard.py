"""
AI Auto Dashboard Page - Automatically generate dashboard insights using LLM
Uses LangChain + Ollama + Qwen VL 4B to analyze table schemas and generate visualizations
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import require_auth
from core.minio_client import (
    get_minio_config,
    list_parquet_files
)
from core.data_loader import load_parquet_to_df
from core.ai_dashboard import (
    generate_schema_summary,
    generate_dashboard_insights
)

# Require authentication
require_auth()


def render_insight_chart(df: pd.DataFrame, insight: dict) -> None:
    """
    Render a chart based on an insight configuration
    
    Args:
        df: pandas DataFrame
        insight: Insight dictionary with chart configuration
    """
    try:
        chart_type = insight.get("chart_type", "table")
        
        # Handle filters if specified (simplified - just for basic filtering)
        plot_df = df.copy()
        filters = insight.get("filters")
        if filters and filters != "null":
            # For now, skip complex filtering - would need NLP parsing
            st.info(f"💡 Filter suggestion: {filters} (not yet implemented)")
        
        # Apply aggregation if specified
        x_col = insight.get("x") if insight.get("x") != "null" else None
        y_col = insight.get("y") if insight.get("y") != "null" else None
        group_by = insight.get("group_by") if insight.get("group_by") != "null" else None
        aggregation = insight.get("aggregation")
        
        if aggregation and aggregation != "null":
            if x_col and x_col in plot_df.columns:
                if aggregation == "count":
                    plot_df = plot_df.groupby(x_col).size().reset_index(name="count")
                    y_col = "count"
                elif aggregation == "mean" and y_col and y_col in plot_df.columns:
                    plot_df = plot_df.groupby(x_col)[y_col].mean().reset_index()
                elif aggregation == "sum" and y_col and y_col in plot_df.columns:
                    plot_df = plot_df.groupby(x_col)[y_col].sum().reset_index()
                elif aggregation == "min" and y_col and y_col in plot_df.columns:
                    plot_df = plot_df.groupby(x_col)[y_col].min().reset_index()
                elif aggregation == "max" and y_col and y_col in plot_df.columns:
                    plot_df = plot_df.groupby(x_col)[y_col].max().reset_index()
        
        # Render chart based on type
        if chart_type == "table":
            # Show first 100 rows
            st.dataframe(plot_df.head(100), width='stretch', height=400)
            
        elif chart_type == "bar":
            if x_col and y_col and x_col in plot_df.columns and y_col in plot_df.columns:
                if group_by and group_by in plot_df.columns:
                    # Grouped bar chart
                    fig = px.bar(
                        plot_df,
                        x=x_col,
                        y=y_col,
                        color=group_by,
                        title=insight.get("title", f"{y_col} by {x_col}"),
                        labels={x_col: x_col.replace('_', ' ').title(), 
                               y_col: y_col.replace('_', ' ').title(),
                               group_by: group_by.replace('_', ' ').title()},
                        barmode='group'
                    )
                else:
                    # Simple bar chart
                    fig = px.bar(
                        plot_df,
                        x=x_col,
                        y=y_col,
                        title=insight.get("title", f"{y_col} by {x_col}"),
                        labels={x_col: x_col.replace('_', ' ').title(), 
                               y_col: y_col.replace('_', ' ').title()}
                    )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"⚠️ Invalid column references: x={x_col}, y={y_col}")
                
        elif chart_type == "line":
            if x_col and y_col and x_col in plot_df.columns and y_col in plot_df.columns:
                fig = px.line(
                    plot_df,
                    x=x_col,
                    y=y_col,
                    color=group_by if group_by and group_by in plot_df.columns else None,
                    title=insight.get("title", f"{y_col} over {x_col}"),
                    labels={x_col: x_col.replace('_', ' ').title(), 
                           y_col: y_col.replace('_', ' ').title()},
                    markers=True
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"⚠️ Invalid column references: x={x_col}, y={y_col}")
                
        elif chart_type == "area":
            if x_col and y_col and x_col in plot_df.columns and y_col in plot_df.columns:
                fig = px.area(
                    plot_df,
                    x=x_col,
                    y=y_col,
                    color=group_by if group_by and group_by in plot_df.columns else None,
                    title=insight.get("title", f"{y_col} over {x_col}"),
                    labels={x_col: x_col.replace('_', ' ').title(), 
                           y_col: y_col.replace('_', ' ').title()}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"⚠️ Invalid column references: x={x_col}, y={y_col}")
                
        elif chart_type == "pie":
            if x_col and y_col and x_col in plot_df.columns and y_col in plot_df.columns:
                fig = px.pie(
                    plot_df,
                    values=y_col,
                    names=x_col,
                    title=insight.get("title", f"Distribution of {y_col} by {x_col}")
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"⚠️ Invalid column references: x={x_col}, y={y_col}")
                
        elif chart_type == "scatter":
            if x_col and y_col and x_col in plot_df.columns and y_col in plot_df.columns:
                fig = px.scatter(
                    plot_df,
                    x=x_col,
                    y=y_col,
                    color=group_by if group_by and group_by in plot_df.columns else None,
                    title=insight.get("title", f"{y_col} vs {x_col}"),
                    labels={x_col: x_col.replace('_', ' ').title(), 
                           y_col: y_col.replace('_', ' ').title()}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"⚠️ Invalid column references: x={x_col}, y={y_col}")
                
        elif chart_type == "histogram":
            if y_col and y_col in plot_df.columns:
                fig = px.histogram(
                    plot_df,
                    x=y_col,
                    color=group_by if group_by and group_by in plot_df.columns else None,
                    title=insight.get("title", f"Distribution of {y_col}"),
                    labels={y_col: y_col.replace('_', ' ').title()}
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.error(f"⚠️ Invalid column reference: y={y_col}")
        else:
            st.warning(f"⚠️ Unsupported chart type: {chart_type}")
            
    except Exception as e:
        st.error(f"⚠️ Error rendering chart: {str(e)}")


def render_insight_card(idx: int, df: pd.DataFrame, insight: dict, expand_default: bool) -> None:
    """
    Render an insight inside an expander so it can be placed in any container.
    """
    insight_title = insight.get("title", "Untitled")
    with st.expander(
        f"📈 Insight {idx + 1}: {insight_title}",
        expanded=expand_default
    ):
        st.markdown(f"**Description:** {insight.get('description', 'No description available')}")
        
        with st.expander("⚙️ Chart Configuration", expanded=False):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Chart Type:** {insight.get('chart_type', 'unknown')}")
                st.write(f"**X-Axis:** {insight.get('x', 'N/A')}")
                st.write(f"**Y-Axis:** {insight.get('y', 'N/A')}")
            with col2:
                st.write(f"**Group By:** {insight.get('group_by', 'N/A')}")
                st.write(f"**Aggregation:** {insight.get('aggregation', 'N/A')}")
                if insight.get('filters'):
                    st.write(f"**Filters:** {insight.get('filters')}")
        
        st.markdown("#### Visualization")
        render_insight_chart(df, insight)


def main():
    # Ensure scrolling works on this page and add grid layout for large screens
    st.markdown("""
    <style>
    html, body {
        overflow-y: auto !important;
        overflow-x: hidden !important;
        height: auto !important;
    }
    .main {
        overflow-y: auto !important;
        overflow-x: hidden !important;
        height: auto !important;
    }
    [data-testid="stAppViewContainer"] {
        overflow-y: auto !important;
        overflow-x: hidden !important;
        height: auto !important;
    }
    .main .block-container {
        overflow-y: visible !important;
        height: auto !important;
    }
    .stMainBlockContainer {
        max-width: 100% !important;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🤖 AI Auto Dashboard")
    st.markdown("""
    Automatically generate dashboard insights from your Parquet tables using AI.
    The AI analyzes your table schema and statistics, then suggests meaningful visualizations.
    """)
    
    # Get MinIO configuration
    config = get_minio_config()
    
    # List Parquet files from gold bucket
    gold_bucket = "gold"
    try:
        parquet_files = list_parquet_files(gold_bucket)
        
        if not parquet_files:
            st.warning("⚠️ No Parquet files found in the gold bucket. Please upload files to MinIO first.")
            return
        
        # Auto-select the first file (or process all if multiple)
        selected_file = parquet_files[0]
        
        if len(parquet_files) > 1:
            st.info(f"📊 Found {len(parquet_files)} tables in the gold bucket. Processing: {selected_file}")
        else:
            st.info(f"📊 Processing table: {selected_file}")
        
        # Check if dashboard already generated for this file
        if "ai_dashboard_insights" not in st.session_state:
            st.session_state.ai_dashboard_insights = {}
        if "ai_dashboard_df" not in st.session_state:
            st.session_state.ai_dashboard_df = {}
        
        # Generate dashboard if not already generated
        if selected_file not in st.session_state.ai_dashboard_insights:
            with st.spinner(f"Loading {selected_file} and generating insights..."):
                # Load data (sample first 1000 rows for performance)
                df = load_parquet_to_df(gold_bucket, selected_file, sample_rows=1000)
                
                if df is None or df.empty:
                    st.error("❌ Failed to load the Parquet file or file is empty.")
                    return
                
                # Store in session state for chart rendering
                st.session_state.ai_dashboard_df[selected_file] = df
                
                # Generate schema summary
                with st.spinner("Analyzing table schema..."):
                    schema_summary = generate_schema_summary(df, sample_rows=20)
                
                # Display basic info
                st.success(f"✅ Loaded {selected_file} ({len(df):,} rows, {len(df.columns)} columns)")
                
                # Show schema info in expander
                with st.expander("📊 Table Schema Summary", expanded=False):
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Rows", f"{schema_summary['num_rows']:,}")
                        st.metric("Columns", schema_summary['num_columns'])
                    
                    with col2:
                        numeric_cols = [
                            col["name"] for col in schema_summary["columns"]
                            if col["type_category"] == "numeric"
                        ]
                        categorical_cols = [
                            col["name"] for col in schema_summary["columns"]
                            if col["type_category"] == "categorical"
                        ]
                        st.metric("Numeric Columns", len(numeric_cols))
                        st.metric("Categorical Columns", len(categorical_cols))
                    
                    # Column details
                    st.subheader("Column Details")
                    col_details = pd.DataFrame([
                        {
                            "Column": col["name"],
                            "Type": col["type_category"],
                            "Dtype": col["dtype"]
                        }
                        for col in schema_summary["columns"]
                    ])
                    st.dataframe(col_details, use_container_width=True)
                
                # Generate insights using LLM
                with st.spinner("🤖 AI is analyzing your data and generating insights... (this may take a moment)"):
                    insights = generate_dashboard_insights(
                        table_name=selected_file.split('/')[-1],  # Use filename without path
                        schema_summary=schema_summary,
                        max_insights=10
                    )
                
                if not insights:
                    st.warning("⚠️ No insights generated. Please check your LLM configuration.")
                    return
                
                # Store insights in session state
                st.session_state.ai_dashboard_insights[selected_file] = insights
                
                st.success(f"✅ Generated {len(insights)} dashboard insights!")
        
        # Display generated dashboard
        if selected_file in st.session_state.ai_dashboard_insights:
            insights = st.session_state.ai_dashboard_insights[selected_file]
            df = st.session_state.ai_dashboard_df.get(selected_file)
            
            if df is not None and insights:
                st.markdown("---")
                st.subheader("📊 AI-Generated Dashboard Insights")
                
                # Note about AI generation
                st.info("""
                💡 **Note:** These insights are automatically generated by an LLM (Qwen VL 4B via Ollama) 
                based on your data schema. The AI analyzes column types, distributions, and relationships 
                to suggest meaningful visualizations.
                """)
                
                grid_cols = st.slider(
                    "Cards per row",
                    min_value=1,
                    max_value=3,
                    value=st.session_state.get("ai_dashboard_grid_cols", 2),
                    help="Adjust how many insight cards show per row.",
                    key="ai_dashboard_grid_cols"
                )
                
                # Display insights in a responsive grid using Streamlit columns
                for row_start in range(0, len(insights), grid_cols):
                    row_insights = insights[row_start:row_start + grid_cols]
                    columns = st.columns(len(row_insights))
                    for col_offset, (col_container, insight) in enumerate(zip(columns, row_insights)):
                        insight_idx = row_start + col_offset
                        with col_container:
                            render_insight_card(
                                idx=insight_idx,
                                df=df,
                                insight=insight,
                                expand_default=insight_idx < 3
                            )
                
                # Regenerate button
                if st.button("🔄 Regenerate Insights", type="secondary"):
                    # Clear insights and regenerate
                    if selected_file in st.session_state.ai_dashboard_insights:
                        del st.session_state.ai_dashboard_insights[selected_file]
                    st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        st.info("💡 Make sure MinIO is running and accessible, and that the bucket exists.")


if __name__ == "__main__":
    main()

