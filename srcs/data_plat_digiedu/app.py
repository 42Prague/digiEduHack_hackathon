"""
====================================================================
STUDENT PERFORMANCE SURVEY SYSTEM
Main Application Entry Point
====================================================================

Multi-page Streamlit application with:
- Survey questionnaire for data collection
- Natural language query interface
- Interactive dashboard and analytics

To run:
    streamlit run app.py

Requirements:
    pip install -r requirements.txt
"""

import streamlit as st

# ====================================================================
# PAGE CONFIGURATION
# ====================================================================

st.set_page_config(
    page_title="Student Performance Survey System",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'mailto:support@example.com',
        'Report a bug': 'mailto:support@example.com',
        'About': '# Student Performance Survey System\nVersion 1.0'
    }
)

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stButton>button {
        width: 100%;
    }
    h1 {
        color: #1f77b4;
        padding-bottom: 10px;
        border-bottom: 2px solid #1f77b4;
    }
    h2 {
        color: #2c3e50;
        padding-top: 20px;
    }
    .success-box {
        padding: 20px;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 20px 0;
    }
    .info-box {
        padding: 20px;
        border-radius: 5px;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# ====================================================================
# MAIN PAGE CONTENT
# ====================================================================

def main():
    # Title and welcome message
    st.title("📚 Student Performance Survey System")
    
    st.markdown("""
    ### Welcome to the Student Performance Assessment Platform
    
    This comprehensive system helps you collect, analyze, and visualize teacher perceptions 
    of student performance across schools and regions.
    """)
    
    # Navigation info
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        ### 📝 Survey Form
        **For Teachers**
        
        Complete the questionnaire to assess student performance. Your responses will be 
        securely stored in the database for analysis.
        
        ➡️ Go to **1_📝_Survey_Form** in the sidebar
        """)
        
    with col2:
        st.markdown("""
        ### 🔍 Ask Questions
        **Natural Language Queries**
        
        Ask questions about the data in plain English. Our system will translate your 
        questions into database queries and show results.
        
        ➡️ Go to **2_🔍_Ask_Questions** in the sidebar
        """)
        
    with col3:
        st.markdown("""
        ### 📊 Dashboard
        **Interactive Analytics**
        
        Explore comprehensive visualizations, compare schools and regions, and track 
        performance trends over time.
        
        ➡️ Go to **3_📊_Dashboard** in the sidebar
        """)
    
    st.markdown("---")
    
    st.markdown("### 📈 Advanced Analysis")
    
    st.markdown("""
    #### 🔬 Statistical Analysis (NEW!)
    **Mixed Effects Models**
    
    Run hierarchical linear models directly in your browser:
    - Calculate ICC (variance partitioning)
    - Test intervention effectiveness
    - Analyze temporal trends
    - Intervention × Time interactions
    - Compare all outcomes simultaneously
    
    ➡️ Go to **4_📈_Statistical_Analysis** in the sidebar
    """)
    
    st.markdown("""
    #### 🤖 ChatFriend - AI Assistant (NEW!)
    **Your AI-Powered Qualitative Analysis Partner**
    
    Uses local LLM (Ollama) to analyze teacher narratives:
    - 🔍 **Semantic Search** - Find responses by meaning, not just keywords
    - 🎯 **Theme Extraction** - Auto-identify patterns across responses
    - ⚖️ **Comparative Analysis** - Compare Treatment vs Control perspectives
    - ⏱️ **Temporal Trends** - Track how perceptions evolve over time
    - 📝 **Summary Generation** - Generate comprehensive insights
    
    ➡️ Go to **5_🤖_ChatFriend** in the sidebar
    
    *Requires Ollama (free, runs locally)*
    """)
    
    st.markdown("---")
    
    # Quick stats
    st.markdown("### 📈 System Overview")
    
    try:
        from database_utils import get_database_connection, execute_query
        
        engine = get_database_connection()
        
        if engine:
            # Get quick stats
            stats_query = """
            SELECT 
                COUNT(*) as total_responses,
                COUNT(DISTINCT teacher_id) as total_teachers,
                COUNT(DISTINCT school_id) as total_schools,
                COUNT(DISTINCT region) as total_regions
            FROM teacher_survey_responses
            """
            
            stats = execute_query(engine, stats_query)
            
            if stats is not None and not stats.empty:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Responses", f"{stats['total_responses'].iloc[0]:,}")
                
                with col2:
                    st.metric("Teachers", f"{stats['total_teachers'].iloc[0]:,}")
                
                with col3:
                    st.metric("Schools", f"{stats['total_schools'].iloc[0]:,}")
                
                with col4:
                    st.metric("Regions", f"{stats['total_regions'].iloc[0]:,}")
                    
                # Latest surveys
                st.markdown("### 🕒 Recent Activity")
                
                recent_query = """
                SELECT 
                    survey_date,
                    region,
                    school_name,
                    intervention_status,
                    b1_overall_performance as performance
                FROM teacher_survey_responses
                ORDER BY survey_date DESC
                LIMIT 10
                """
                
                recent = execute_query(engine, recent_query)
                
                if recent is not None and not recent.empty:
                    st.dataframe(recent, hide_index=True, use_container_width=True)
            else:
                st.info("No data available yet. Start by completing the survey form!")
        else:
            st.info("Database connection not configured. Using demo mode.")
            
    except Exception as e:
        st.info("Welcome! Complete the survey form to get started, or explore the demo dashboard.")
    
    # Footer
    st.markdown("---")
    
    st.markdown("""
    ### 🚀 Getting Started
    
    **First Time Here?**
    1. **Teachers:** Navigate to the Survey Form to submit your assessment
    2. **Administrators:** Use the Dashboard to view analytics
    3. **Researchers:** Use Ask Questions for custom analysis
    
    **Need Help?**
    - Check the documentation in each section
    - Contact support: support@example.com
    
    ---
    
    <div style='text-align: center; color: gray; padding: 20px;'>
    📚 Student Performance Survey System v1.0<br>
    For research and educational improvement purposes
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

