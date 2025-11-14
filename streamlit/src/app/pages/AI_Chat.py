"""
AI Chat Page - Preserved AI chatbot integration for natural language SQL queries
This page maintains the existing AI chat functionality exactly as it was.
"""

import streamlit as st
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from auth import require_auth
from database import init_database, check_tables_exist
from ai_chatbot import render_chat_interface

# Require authentication
require_auth()

# Database path - Education dataset
DB_PATH = "/app/data/education.duckdb"


def get_db_connection():
    """Get database connection using session state"""
    if 'db_conn' not in st.session_state:
        try:
            st.session_state.db_conn = init_database(DB_PATH)
        except Exception as e:
            st.error(f"⚠️ Database connection failed: {str(e)}")
            st.info("💡 Try refreshing the page. Database features will be unavailable.")
            st.session_state.db_conn = None
    
    return st.session_state.db_conn


def main():
    st.title("🤖 AI-Powered SQL Query Assistant")
    
    # Get database connection
    conn = get_db_connection()
    
    if conn is None:
        st.error("❌ Unable to initialize database connection. Please check logs.")
        return
    
    # Render chat interface (no warnings, just the chat)
    render_chat_interface(conn)


if __name__ == "__main__":
    main()

