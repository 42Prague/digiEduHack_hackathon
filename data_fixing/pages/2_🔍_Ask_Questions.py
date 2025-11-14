"""
====================================================================
NATURAL LANGUAGE QUERY PAGE
Ask questions about the data in plain English
====================================================================
"""

import streamlit as st
import sys
import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_utils import get_database_connection, execute_query

st.set_page_config(page_title="Ask Questions", page_icon="🔍", layout="wide")

# ====================================================================
# NATURAL LANGUAGE TO SQL TRANSLATION
# ====================================================================

def natural_language_to_sql(question):
    """
    Convert natural language question to SQL query.
    Uses pattern matching for common queries.
    """
    
    question_lower = question.lower()
    
    # Pattern 1: Average/Mean performance by region
    if any(word in question_lower for word in ['average', 'mean']) and 'region' in question_lower:
        if 'intervention' in question_lower or 'treatment' in question_lower or 'control' in question_lower:
            return """
            SELECT 
                region,
                intervention_status,
                COUNT(*) as num_responses,
                ROUND(AVG(b1_overall_performance), 2) as avg_overall_performance,
                ROUND(AVG(b2_problem_solving), 2) as avg_problem_solving,
                ROUND(AVG(b6_engagement), 2) as avg_engagement
            FROM teacher_survey_responses
            GROUP BY region, intervention_status
            ORDER BY region, intervention_status
            """
        else:
            return """
            SELECT 
                region,
                COUNT(*) as num_responses,
                ROUND(AVG(b1_overall_performance), 2) as avg_overall_performance,
                ROUND(AVG(b2_problem_solving), 2) as avg_problem_solving,
                ROUND(AVG(b6_engagement), 2) as avg_engagement
            FROM teacher_survey_responses
            GROUP BY region
            ORDER BY region
            """
    
    # Pattern 2: Performance by school
    if 'school' in question_lower and any(word in question_lower for word in ['performance', 'compare', 'rank']):
        return """
        SELECT 
            school_name,
            region,
            intervention_status,
            COUNT(*) as num_responses,
            ROUND(AVG(b1_overall_performance), 2) as avg_performance,
            ROUND(AVG((b1_overall_performance + b2_problem_solving + b3_critical_thinking + 
                b4_collaboration + b5_communication + b6_engagement + 
                b7_behavior + b8_persistence) / 8.0), 2) as composite_score
        FROM teacher_survey_responses
        GROUP BY school_name, region, intervention_status
        ORDER BY composite_score DESC
        """
    
    # Pattern 3: Temporal trends / over time
    if any(word in question_lower for word in ['over time', 'trend', 'change', 'progress', 'temporal']):
        return """
        SELECT 
            survey_date,
            intervention_status,
            COUNT(*) as num_responses,
            ROUND(AVG(b1_overall_performance), 2) as avg_performance,
            ROUND(AVG(b6_engagement), 2) as avg_engagement
        FROM teacher_survey_responses
        GROUP BY survey_date, intervention_status
        ORDER BY survey_date
        """
    
    # Pattern 4: Intervention effectiveness
    if any(word in question_lower for word in ['intervention', 'treatment', 'effectiveness', 'impact']):
        return """
        SELECT 
            intervention_status,
            COUNT(*) as num_responses,
            ROUND(AVG(b1_overall_performance), 2) as avg_overall_performance,
            ROUND(AVG(b2_problem_solving), 2) as avg_problem_solving,
            ROUND(AVG(b3_critical_thinking), 2) as avg_critical_thinking,
            ROUND(AVG(b6_engagement), 2) as avg_engagement
        FROM teacher_survey_responses
        GROUP BY intervention_status
        """
    
    # Pattern 5: Specific region analysis
    for region_keyword in ['region 1', 'region 2', 'region 3', 'region_1', 'region_2', 'region_3']:
        if region_keyword in question_lower:
            region_name = region_keyword.replace(' ', '_').title()
            return f"""
            SELECT 
                school_name,
                intervention_status,
                COUNT(*) as num_responses,
                ROUND(AVG(b1_overall_performance), 2) as avg_performance,
                ROUND(AVG(b6_engagement), 2) as avg_engagement
            FROM teacher_survey_responses
            WHERE region = '{region_name}'
            GROUP BY school_name, intervention_status
            ORDER BY avg_performance DESC
            """
    
    # Pattern 6: Engagement analysis
    if 'engagement' in question_lower:
        return """
        SELECT 
            region,
            intervention_status,
            COUNT(*) as num_responses,
            ROUND(AVG(b6_engagement), 2) as avg_engagement,
            ROUND(MIN(b6_engagement), 2) as min_engagement,
            ROUND(MAX(b6_engagement), 2) as max_engagement
        FROM teacher_survey_responses
        GROUP BY region, intervention_status
        ORDER BY avg_engagement DESC
        """
    
    # Pattern 7: Problem-solving analysis
    if 'problem' in question_lower or 'solving' in question_lower:
        return """
        SELECT 
            region,
            intervention_status,
            COUNT(*) as num_responses,
            ROUND(AVG(b2_problem_solving), 2) as avg_problem_solving,
            ROUND(AVG(b3_critical_thinking), 2) as avg_critical_thinking
        FROM teacher_survey_responses
        GROUP BY region, intervention_status
        ORDER BY avg_problem_solving DESC
        """
    
    # Pattern 8: List all schools
    if 'list' in question_lower and 'school' in question_lower:
        return """
        SELECT DISTINCT
            school_id,
            school_name,
            region,
            intervention_status
        FROM teacher_survey_responses
        ORDER BY region, school_name
        """
    
    # Pattern 9: Count/number of responses
    if any(word in question_lower for word in ['how many', 'count', 'number of']):
        if 'teacher' in question_lower:
            return """
            SELECT 
                region,
                COUNT(DISTINCT teacher_id) as num_teachers
            FROM teacher_survey_responses
            GROUP BY region
            ORDER BY num_teachers DESC
            """
        elif 'school' in question_lower:
            return """
            SELECT 
                region,
                COUNT(DISTINCT school_id) as num_schools
            FROM teacher_survey_responses
            GROUP BY region
            ORDER BY num_schools DESC
            """
        else:
            return """
            SELECT 
                region,
                intervention_status,
                COUNT(*) as num_responses
            FROM teacher_survey_responses
            GROUP BY region, intervention_status
            ORDER BY region, num_responses DESC
            """
    
    # Pattern 10: Best/highest performing
    if any(word in question_lower for word in ['best', 'highest', 'top', 'highest performing']):
        if 'school' in question_lower:
            return """
            SELECT 
                school_name,
                region,
                intervention_status,
                COUNT(*) as num_responses,
                ROUND(AVG((b1_overall_performance + b2_problem_solving + b3_critical_thinking + 
                    b4_collaboration + b5_communication + b6_engagement + 
                    b7_behavior + b8_persistence) / 8.0), 2) as composite_score
            FROM teacher_survey_responses
            GROUP BY school_name, region, intervention_status
            ORDER BY composite_score DESC
            LIMIT 10
            """
        else:
            return """
            SELECT 
                region,
                ROUND(AVG(b1_overall_performance), 2) as avg_performance
            FROM teacher_survey_responses
            GROUP BY region
            ORDER BY avg_performance DESC
            """
    
    # Pattern 11: Worst/lowest performing
    if any(word in question_lower for word in ['worst', 'lowest', 'bottom', 'struggling']):
        return """
        SELECT 
            school_name,
            region,
            intervention_status,
            COUNT(*) as num_responses,
            ROUND(AVG((b1_overall_performance + b2_problem_solving + b3_critical_thinking + 
                b4_collaboration + b5_communication + b6_engagement + 
                b7_behavior + b8_persistence) / 8.0), 2) as composite_score
        FROM teacher_survey_responses
        GROUP BY school_name, region, intervention_status
        ORDER BY composite_score ASC
        LIMIT 10
        """
    
    # Pattern 12: All outcomes/dimensions
    if 'all outcomes' in question_lower or 'all dimensions' in question_lower or 'all performance' in question_lower:
        return """
        SELECT 
            intervention_status,
            ROUND(AVG(b1_overall_performance), 2) as overall_performance,
            ROUND(AVG(b2_problem_solving), 2) as problem_solving,
            ROUND(AVG(b3_critical_thinking), 2) as critical_thinking,
            ROUND(AVG(b4_collaboration), 2) as collaboration,
            ROUND(AVG(b5_communication), 2) as communication,
            ROUND(AVG(b6_engagement), 2) as engagement,
            ROUND(AVG(b7_behavior), 2) as behavior,
            ROUND(AVG(b8_persistence), 2) as persistence
        FROM teacher_survey_responses
        GROUP BY intervention_status
        """
    
    # Pattern 13: Recent responses
    if 'recent' in question_lower or 'latest' in question_lower:
        return """
        SELECT 
            survey_date,
            teacher_id,
            school_name,
            region,
            intervention_status,
            b1_overall_performance as performance
        FROM teacher_survey_responses
        ORDER BY survey_date DESC
        LIMIT 20
        """
    
    # Default: Show summary statistics
    return """
    SELECT 
        region,
        intervention_status,
        COUNT(*) as num_responses,
        ROUND(AVG(b1_overall_performance), 2) as avg_performance,
        ROUND(AVG(b6_engagement), 2) as avg_engagement
    FROM teacher_survey_responses
    GROUP BY region, intervention_status
    ORDER BY region, intervention_status
    """

# ====================================================================
# VISUALIZATION FUNCTIONS
# ====================================================================

def create_visualization(df, query_type):
    """Create appropriate visualization based on query results."""
    
    if df is None or df.empty:
        return None
    
    # Check what columns we have
    cols = df.columns.tolist()
    
    # Time series data
    if 'survey_date' in cols:
        fig = px.line(
            df,
            x='survey_date',
            y=[c for c in cols if 'avg' in c or 'performance' in c or 'engagement' in c][:2],
            color='intervention_status' if 'intervention_status' in cols else None,
            markers=True,
            title='Performance Over Time'
        )
        return fig
    
    # Regional comparison
    elif 'region' in cols and any('avg' in c for c in cols):
        value_col = [c for c in cols if 'avg' in c or 'performance' in c][0]
        
        if 'intervention_status' in cols:
            fig = px.bar(
                df,
                x='region',
                y=value_col,
                color='intervention_status',
                barmode='group',
                title='Regional Performance Comparison'
            )
        else:
            fig = px.bar(
                df,
                x='region',
                y=value_col,
                title='Regional Performance'
            )
        return fig
    
    # School comparison
    elif 'school_name' in cols and any('avg' in c or 'composite' in c for c in cols):
        value_col = [c for c in cols if 'avg' in c or 'composite' in c or 'performance' in c][0]
        
        fig = px.bar(
            df.head(15),  # Top 15 schools
            x='school_name',
            y=value_col,
            color='intervention_status' if 'intervention_status' in cols else None,
            title='School Performance Comparison'
        )
        fig.update_xaxes(tickangle=-45)
        return fig
    
    # All outcomes comparison
    elif all(outcome in cols for outcome in ['overall_performance', 'problem_solving', 'engagement']):
        # Reshape data for radar chart
        if 'intervention_status' in cols:
            fig = go.Figure()
            
            outcomes = [c for c in cols if c != 'intervention_status']
            
            for status in df['intervention_status'].unique():
                subset = df[df['intervention_status'] == status]
                values = subset[outcomes].values[0]
                
                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=outcomes,
                    fill='toself',
                    name=status
                ))
            
            fig.update_layout(
                polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
                title='All Performance Dimensions'
            )
            return fig
    
    return None

# ====================================================================
# MAIN PAGE
# ====================================================================

def main():
    st.title("🔍 Ask Questions About Your Data")
    
    # Add refresh button
    col_title, col_refresh = st.columns([3, 1])
    with col_refresh:
        if st.button("🔄 Refresh", help="Query fresh data from database", key="refresh_query", use_container_width=True):
            st.rerun()
    
    st.markdown("""
    ### Natural Language Query Interface
    
    Ask questions about student performance data in plain English, and get instant results!
    
    **Try asking questions like:**
    - *"What is the average performance by region?"*
    - *"Show me performance trends over time"*
    - *"Which schools are performing best?"*
    - *"Compare intervention and control groups"*
    - *"How many responses do we have by region?"*
    """)
    
    st.markdown("---")
    
    # Get database connection
    engine = get_database_connection()
    
    # Query input
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_question = st.text_input(
            "Ask a question:",
            placeholder="e.g., What is the average performance by region?",
            label_visibility="collapsed"
        )
    
    with col2:
        ask_button = st.button("🔍 Ask", use_container_width=True, type="primary")
    
    # Common questions (quick buttons)
    st.markdown("**Quick Questions:**")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📊 Regional Performance"):
            user_question = "What is the average performance by region and intervention status?"
            ask_button = True
        
        if st.button("📈 Performance Trends"):
            user_question = "Show me performance trends over time"
            ask_button = True
    
    with col2:
        if st.button("🏫 School Rankings"):
            user_question = "Which schools are performing best?"
            ask_button = True
        
        if st.button("🎯 Intervention Impact"):
            user_question = "Compare intervention and control groups"
            ask_button = True
    
    with col3:
        if st.button("📋 Response Count"):
            user_question = "How many responses do we have by region?"
            ask_button = True
        
        if st.button("💡 All Outcomes"):
            user_question = "Show all performance dimensions by intervention status"
            ask_button = True
    
    # Process question
    if ask_button and user_question:
        st.markdown("---")
        
        with st.spinner("🤔 Processing your question..."):
            # Convert to SQL
            sql_query = natural_language_to_sql(user_question)
            
            # Show SQL query (expandable)
            with st.expander("📝 See Generated SQL Query"):
                st.code(sql_query, language="sql")
            
            # Execute query
            result_df = execute_query(engine, sql_query)
            
            if result_df is not None and not result_df.empty:
                st.success(f"✅ Found {len(result_df)} results")
                
                # Create tabs for table and visualization
                tab1, tab2 = st.tabs(["📊 Visualization", "📋 Data Table"])
                
                with tab1:
                    # Create visualization
                    fig = create_visualization(result_df, user_question)
                    
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.info("Data table view available in 'Data Table' tab →")
                
                with tab2:
                    st.dataframe(result_df, hide_index=True, use_container_width=True)
                    
                    # Download button
                    csv = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Results as CSV",
                        data=csv,
                        file_name=f"query_results_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}.csv",
                        mime="text/csv"
                    )
                
                # Show insights
                st.markdown("### 💡 Key Insights")
                
                # Generate automated insights
                if 'avg_performance' in result_df.columns:
                    max_perf = result_df['avg_performance'].max()
                    min_perf = result_df['avg_performance'].min()
                    
                    if 'region' in result_df.columns:
                        best_region = result_df.loc[result_df['avg_performance'].idxmax(), 'region']
                        worst_region = result_df.loc[result_df['avg_performance'].idxmin(), 'region']
                        
                        st.markdown(f"""
                        - **Highest performing region:** {best_region} ({max_perf:.2f}/5)
                        - **Lowest performing region:** {worst_region} ({min_perf:.2f}/5)
                        - **Performance gap:** {(max_perf - min_perf):.2f} points
                        """)
                
                if 'intervention_status' in result_df.columns and 'avg_performance' in result_df.columns:
                    intervention_df = result_df.groupby('intervention_status')['avg_performance'].mean()
                    
                    if 'Treatment' in intervention_df.index and 'Control' in intervention_df.index:
                        diff = intervention_df['Treatment'] - intervention_df['Control']
                        st.markdown(f"""
                        - **Treatment group average:** {intervention_df['Treatment']:.2f}/5
                        - **Control group average:** {intervention_df['Control']:.2f}/5
                        - **Intervention effect:** {diff:+.2f} points {'📈' if diff > 0 else '📉' if diff < 0 else '➡️'}
                        """)
                
            else:
                st.warning("No results found. Try rephrasing your question or check if data is available.")
    
    # Help section
    st.markdown("---")
    
    with st.expander("❓ How to Use This Page"):
        st.markdown("""
        ### Query Examples by Category
        
        **Regional Analysis:**
        - "What is the average performance by region?"
        - "Compare regions"
        - "Show performance in Region 1"
        
        **School Comparison:**
        - "Which schools are performing best?"
        - "List all schools"
        - "Rank schools by performance"
        
        **Temporal Analysis:**
        - "Show performance trends over time"
        - "How has performance changed?"
        - "Recent responses"
        
        **Intervention Effectiveness:**
        - "Compare intervention and control groups"
        - "Is the intervention effective?"
        - "Show intervention impact"
        
        **Specific Outcomes:**
        - "Show engagement scores"
        - "Compare problem-solving skills"
        - "Show all performance dimensions"
        
        **Counts and Statistics:**
        - "How many responses do we have?"
        - "How many teachers per region?"
        - "Number of schools by region"
        
        ### Tips:
        - Be specific about what you want to see
        - Mention specific regions, schools, or outcomes if relevant
        - Use keywords like "average", "compare", "trend", "best", "count"
        - Check the generated SQL query to understand what data is being retrieved
        """)

if __name__ == "__main__":
    main()

