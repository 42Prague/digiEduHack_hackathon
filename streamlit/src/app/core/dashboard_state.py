"""
Dashboard state management using Streamlit session_state
"""

import streamlit as st
from typing import List, Dict, Any, Optional


def init_dashboard_state():
    """Initialize dashboard state in session_state if not present"""
    if "dashboard_charts" not in st.session_state:
        st.session_state.dashboard_charts = []


def add_chart_to_dashboard(chart_config: Dict[str, Any]):
    """
    Add a chart configuration to the dashboard
    
    Args:
        chart_config: Dictionary containing chart configuration:
            - type: str (e.g., "line", "bar", "area", "scatter", "hist")
            - x_column: str
            - y_columns: List[str] or str
            - aggregation: Optional[str] (e.g., "sum", "mean", "count", None)
            - title: Optional[str]
    """
    init_dashboard_state()
    st.session_state.dashboard_charts.append(chart_config)


def remove_chart_from_dashboard(index: int):
    """
    Remove a chart from the dashboard by index
    
    Args:
        index: Index of chart to remove
    """
    init_dashboard_state()
    if 0 <= index < len(st.session_state.dashboard_charts):
        st.session_state.dashboard_charts.pop(index)


def clear_dashboard():
    """Clear all charts from the dashboard"""
    init_dashboard_state()
    st.session_state.dashboard_charts = []


def get_dashboard_charts() -> List[Dict[str, Any]]:
    """
    Get all chart configurations in the dashboard
    
    Returns:
        List of chart configuration dictionaries
    """
    init_dashboard_state()
    return st.session_state.dashboard_charts.copy()


def set_current_dataframe(df):
    """
    Store current DataFrame in session_state
    
    Args:
        df: pandas DataFrame
    """
    st.session_state["current_df"] = df


def get_current_dataframe():
    """
    Get current DataFrame from session_state
    
    Returns:
        pandas DataFrame or None
    """
    return st.session_state.get("current_df", None)


def set_current_file(file_name: str):
    """
    Store current file name in session_state
    
    Args:
        file_name: Name of the currently selected file
    """
    st.session_state["current_file"] = file_name


def get_current_file() -> Optional[str]:
    """
    Get current file name from session_state
    
    Returns:
        File name string or None
    """
    return st.session_state.get("current_file", None)

