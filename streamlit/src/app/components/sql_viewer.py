"""
SQL Viewer component for displaying SQL queries with collapsible UI
"""

import streamlit as st


def sql_viewer(sql: str, show_by_default: bool = False):
    """
    Render a collapsible SQL query viewer
    
    Args:
        sql: SQL query string to display
        show_by_default: Whether to show SQL by default (expanded)
    """
    with st.expander("📋 View Generated SQL", expanded=show_by_default):
        st.code(sql, language="sql")
        st.caption("⚠️ Verify this SQL query before relying on results. AI may make mistakes.")

