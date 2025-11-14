"""
====================================================================
STREAMLIT DASHBOARD: Teacher Perception Survey Analysis
Student Performance Monitoring System
====================================================================

This dashboard provides interactive visualizations for:
1. Regional comparisons of student performance
2. School-level performance tracking
3. Temporal progression analysis
4. Intervention effectiveness monitoring

To run:
    streamlit run streamlit_dashboard.py

Requirements:
    pip install streamlit pandas numpy plotly sqlalchemy psycopg2-binary pymysql
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import sqlalchemy
from sqlalchemy import create_engine
import warnings
warnings.filterwarnings('ignore')

# ====================================================================
# PAGE CONFIGURATION
# ====================================================================

st.set_page_config(
    page_title="Student Performance Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 5px;
    }
    h1 {
        color: #1f77b4;
        padding-bottom: 10px;
    }
    h2 {
        color: #2c3e50;
        padding-top: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# ====================================================================
# DATABASE CONNECTION
# ====================================================================

@st.cache_resource
def get_database_connection():
    """
    Create database connection based on configuration.
    Modify this function based on your database type.
    """
    
    # Get database configuration from sidebar or config file
    db_type = st.session_state.get('db_type', 'sqlite')
    
    if db_type == 'sqlite':
        # SQLite (for testing with local file)
        engine = create_engine('sqlite:///teacher_survey.db')
        
    elif db_type == 'postgresql':
        # PostgreSQL
        host = st.secrets.get("db_host", "localhost")
        port = st.secrets.get("db_port", "5432")
        database = st.secrets.get("db_name", "survey_db")
        username = st.secrets.get("db_user", "user")
        password = st.secrets.get("db_password", "password")
        
        engine = create_engine(
            f'postgresql://{username}:{password}@{host}:{port}/{database}'
        )
        
    elif db_type == 'mysql':
        # MySQL
        host = st.secrets.get("db_host", "localhost")
        port = st.secrets.get("db_port", "3306")
        database = st.secrets.get("db_name", "survey_db")
        username = st.secrets.get("db_user", "user")
        password = st.secrets.get("db_password", "password")
        
        engine = create_engine(
            f'mysql+pymysql://{username}:{password}@{host}:{port}/{database}'
        )
    
    else:  # CSV fallback for demo
        return None
    
    return engine

@st.cache_data(ttl=300)  # Cache for 5 minutes
def load_data_from_db(_engine, query=None):
    """
    Load data from database with optional custom query.
    """
    if _engine is None:
        # Fallback: load from CSV
        try:
            df = pd.read_csv('data_structure_template.csv')
            df['survey_date'] = pd.to_datetime(df['survey_date'])
            return df
        except:
            st.error("No database connection and no CSV file found!")
            return None
    
    # Default query to get all survey data
    if query is None:
        query = """
        SELECT * FROM teacher_survey_responses
        ORDER BY survey_date DESC
        """
    
    try:
        df = pd.read_sql(query, _engine)
        df['survey_date'] = pd.to_datetime(df['survey_date'])
        return df
    except Exception as e:
        st.error(f"Error loading data: {str(e)}")
        return None

# ====================================================================
# DATA PROCESSING FUNCTIONS
# ====================================================================

def prepare_data(df):
    """Prepare and clean data for analysis."""
    
    # Create time variables
    min_date = df['survey_date'].min()
    df['time_years'] = (df['survey_date'] - min_date).dt.days / 365.25
    df['time_months'] = (df['survey_date'] - min_date).dt.days / 30.44
    
    # Create intervention binary
    df['intervention'] = (df['intervention_status'] == 'Treatment').astype(int)
    
    # Outcome variables
    outcome_cols = [
        'b1_overall_performance', 'b2_problem_solving', 
        'b3_critical_thinking', 'b4_collaboration',
        'b5_communication', 'b6_engagement', 
        'b7_behavior', 'b8_persistence'
    ]
    
    # Create composite score (average of all outcomes)
    df['composite_score'] = df[outcome_cols].mean(axis=1)
    
    return df

def calculate_summary_stats(df, group_by='region'):
    """Calculate summary statistics by group."""
    
    outcome_cols = [
        'b1_overall_performance', 'b2_problem_solving', 
        'b3_critical_thinking', 'b4_collaboration',
        'b5_communication', 'b6_engagement', 
        'b7_behavior', 'b8_persistence'
    ]
    
    summary = df.groupby(group_by)[outcome_cols].agg(['mean', 'std', 'count'])
    return summary

# ====================================================================
# VISUALIZATION FUNCTIONS
# ====================================================================

def plot_regional_comparison(df, outcome='b1_overall_performance'):
    """Create bar chart comparing regions."""
    
    outcome_names = {
        'b1_overall_performance': 'Overall Performance',
        'b2_problem_solving': 'Problem Solving',
        'b3_critical_thinking': 'Critical Thinking',
        'b4_collaboration': 'Collaboration',
        'b5_communication': 'Communication',
        'b6_engagement': 'Engagement',
        'b7_behavior': 'Behavior',
        'b8_persistence': 'Persistence',
        'composite_score': 'Composite Score'
    }
    
    # Group by region and intervention status
    grouped = df.groupby(['region', 'intervention_status']).agg({
        outcome: ['mean', 'std', 'count']
    }).reset_index()
    
    grouped.columns = ['region', 'intervention_status', 'mean', 'std', 'count']
    grouped['se'] = grouped['std'] / np.sqrt(grouped['count'])
    
    fig = px.bar(
        grouped,
        x='region',
        y='mean',
        color='intervention_status',
        error_y='se',
        barmode='group',
        title=f'{outcome_names.get(outcome, outcome)} by Region and Intervention Status',
        labels={'mean': 'Average Rating', 'region': 'Region', 'intervention_status': 'Group'},
        color_discrete_map={'Treatment': '#2ecc71', 'Control': '#e74c3c'}
    )
    
    fig.update_layout(
        height=500,
        hovermode='x unified',
        legend=dict(title='Group', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig

def plot_temporal_progression(df, outcome='b1_overall_performance', region=None, school=None):
    """Create line chart showing progression over time."""
    
    outcome_names = {
        'b1_overall_performance': 'Overall Performance',
        'b2_problem_solving': 'Problem Solving',
        'b3_critical_thinking': 'Critical Thinking',
        'b4_collaboration': 'Collaboration',
        'b5_communication': 'Communication',
        'b6_engagement': 'Engagement',
        'b7_behavior': 'Behavior',
        'b8_persistence': 'Persistence',
        'composite_score': 'Composite Score'
    }
    
    # Filter data if needed
    filtered_df = df.copy()
    title_suffix = ""
    
    if region and region != 'All Regions':
        filtered_df = filtered_df[filtered_df['region'] == region]
        title_suffix += f" - {region}"
    
    if school and school != 'All Schools':
        filtered_df = filtered_df[filtered_df['school_id'] == school]
        title_suffix += f" - {school}"
    
    # Group by date and intervention status
    grouped = filtered_df.groupby(['survey_date', 'intervention_status']).agg({
        outcome: ['mean', 'std', 'count']
    }).reset_index()
    
    grouped.columns = ['survey_date', 'intervention_status', 'mean', 'std', 'count']
    grouped['se'] = grouped['std'] / np.sqrt(grouped['count'])
    
    fig = px.line(
        grouped,
        x='survey_date',
        y='mean',
        color='intervention_status',
        error_y='se',
        markers=True,
        title=f'{outcome_names.get(outcome, outcome)} Over Time{title_suffix}',
        labels={'mean': 'Average Rating', 'survey_date': 'Survey Date', 'intervention_status': 'Group'},
        color_discrete_map={'Treatment': '#2ecc71', 'Control': '#e74c3c'}
    )
    
    fig.update_layout(
        height=500,
        hovermode='x unified',
        legend=dict(title='Group', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig

def plot_school_comparison_within_region(df, region, outcome='composite_score'):
    """Compare schools within a specific region."""
    
    outcome_names = {
        'b1_overall_performance': 'Overall Performance',
        'b2_problem_solving': 'Problem Solving',
        'b3_critical_thinking': 'Critical Thinking',
        'b4_collaboration': 'Collaboration',
        'b5_communication': 'Communication',
        'b6_engagement': 'Engagement',
        'b7_behavior': 'Behavior',
        'b8_persistence': 'Persistence',
        'composite_score': 'Composite Score'
    }
    
    # Filter by region
    region_df = df[df['region'] == region].copy()
    
    # Group by school
    grouped = region_df.groupby(['school_id', 'school_name', 'intervention_status']).agg({
        outcome: ['mean', 'std', 'count']
    }).reset_index()
    
    grouped.columns = ['school_id', 'school_name', 'intervention_status', 'mean', 'std', 'count']
    grouped['se'] = grouped['std'] / np.sqrt(grouped['count'])
    
    # Sort by mean performance
    grouped = grouped.sort_values('mean', ascending=False)
    
    fig = px.bar(
        grouped,
        x='school_name',
        y='mean',
        color='intervention_status',
        error_y='se',
        title=f'{outcome_names.get(outcome, outcome)} by School in {region}',
        labels={'mean': 'Average Rating', 'school_name': 'School'},
        color_discrete_map={'Treatment': '#2ecc71', 'Control': '#e74c3c'}
    )
    
    fig.update_layout(
        height=500,
        xaxis_tickangle=-45,
        hovermode='x unified',
        legend=dict(title='Group', orientation='h', yanchor='bottom', y=1.02, xanchor='right', x=1)
    )
    
    return fig

def plot_all_outcomes_comparison(df, region=None):
    """Create radar chart comparing all outcomes."""
    
    outcome_cols = [
        'b1_overall_performance', 'b2_problem_solving', 
        'b3_critical_thinking', 'b4_collaboration',
        'b5_communication', 'b6_engagement', 
        'b7_behavior', 'b8_persistence'
    ]
    
    outcome_labels = [
        'Overall', 'Problem<br>Solving', 'Critical<br>Thinking', 'Collaboration',
        'Communication', 'Engagement', 'Behavior', 'Persistence'
    ]
    
    # Filter by region if specified
    filtered_df = df.copy() if region == 'All Regions' or region is None else df[df['region'] == region]
    
    # Calculate means by intervention status
    means_treatment = filtered_df[filtered_df['intervention_status'] == 'Treatment'][outcome_cols].mean().values
    means_control = filtered_df[filtered_df['intervention_status'] == 'Control'][outcome_cols].mean().values
    
    fig = go.Figure()
    
    # Treatment group
    fig.add_trace(go.Scatterpolar(
        r=means_treatment,
        theta=outcome_labels,
        fill='toself',
        name='Treatment',
        line_color='#2ecc71'
    ))
    
    # Control group
    fig.add_trace(go.Scatterpolar(
        r=means_control,
        theta=outcome_labels,
        fill='toself',
        name='Control',
        line_color='#e74c3c'
    ))
    
    title_suffix = "" if region == 'All Regions' or region is None else f" - {region}"
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 5]
            )
        ),
        showlegend=True,
        title=f'All Performance Dimensions{title_suffix}',
        height=600
    )
    
    return fig

def plot_intervention_effect_over_time(df, outcome='composite_score'):
    """Plot intervention effect (Treatment - Control) over time."""
    
    outcome_names = {
        'b1_overall_performance': 'Overall Performance',
        'b2_problem_solving': 'Problem Solving',
        'b3_critical_thinking': 'Critical Thinking',
        'b4_collaboration': 'Collaboration',
        'b5_communication': 'Communication',
        'b6_engagement': 'Engagement',
        'b7_behavior': 'Behavior',
        'b8_persistence': 'Persistence',
        'composite_score': 'Composite Score'
    }
    
    # Group by date and intervention status
    grouped = df.groupby(['survey_date', 'intervention_status'])[outcome].mean().reset_index()
    
    # Pivot to calculate difference
    pivoted = grouped.pivot(index='survey_date', columns='intervention_status', values=outcome).reset_index()
    
    if 'Treatment' in pivoted.columns and 'Control' in pivoted.columns:
        pivoted['intervention_effect'] = pivoted['Treatment'] - pivoted['Control']
        
        fig = go.Figure()
        
        # Add intervention effect line
        fig.add_trace(go.Scatter(
            x=pivoted['survey_date'],
            y=pivoted['intervention_effect'],
            mode='lines+markers',
            name='Intervention Effect',
            line=dict(color='#3498db', width=3),
            marker=dict(size=10)
        ))
        
        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", 
                     annotation_text="No effect", annotation_position="right")
        
        fig.update_layout(
            title=f'Intervention Effect Over Time: {outcome_names.get(outcome, outcome)}',
            xaxis_title='Survey Date',
            yaxis_title='Effect Size (Treatment - Control)',
            height=500,
            hovermode='x unified'
        )
        
        return fig
    else:
        return None

def plot_heatmap_schools_outcomes(df, region=None):
    """Create heatmap of schools x outcomes."""
    
    outcome_cols = [
        'b1_overall_performance', 'b2_problem_solving', 
        'b3_critical_thinking', 'b4_collaboration',
        'b5_communication', 'b6_engagement', 
        'b7_behavior', 'b8_persistence'
    ]
    
    outcome_labels = [
        'Overall', 'Problem<br>Solving', 'Critical<br>Thinking', 'Collaboration',
        'Communication', 'Engagement', 'Behavior', 'Persistence'
    ]
    
    # Filter by region if specified
    filtered_df = df.copy() if region == 'All Regions' or region is None else df[df['region'] == region]
    
    # Group by school
    grouped = filtered_df.groupby('school_name')[outcome_cols].mean()
    
    fig = px.imshow(
        grouped.T,
        labels=dict(x="School", y="Outcome", color="Rating"),
        x=grouped.index,
        y=outcome_labels,
        color_continuous_scale='RdYlGn',
        aspect="auto",
        title=f"Performance Heatmap by School{'' if region == 'All Regions' or region is None else f' - {region}'}"
    )
    
    fig.update_layout(height=500)
    
    return fig

# ====================================================================
# MAIN DASHBOARD
# ====================================================================

def main():
    
    # Title and description
    st.title("📊 Student Performance Dashboard")
    st.markdown("""
    **Monitor and analyze teacher perceptions of student performance across schools and regions.**
    
    This dashboard provides real-time insights into:
    - Regional performance comparisons
    - School-level tracking
    - Temporal trends
    - Intervention effectiveness
    """)
    
    # Sidebar for database configuration and filters
    st.sidebar.header("⚙️ Configuration")
    
    # Database selection
    db_type = st.sidebar.selectbox(
        "Database Type",
        ['CSV (Demo)', 'SQLite', 'PostgreSQL', 'MySQL'],
        help="Select your database type"
    )
    
    # Map selection to key
    db_type_map = {
        'CSV (Demo)': 'csv',
        'SQLite': 'sqlite',
        'PostgreSQL': 'postgresql',
        'MySQL': 'mysql'
    }
    st.session_state['db_type'] = db_type_map[db_type]
    
    # Load data
    with st.spinner("Loading data from database..."):
        engine = get_database_connection() if db_type != 'CSV (Demo)' else None
        df = load_data_from_db(engine)
    
    if df is None or df.empty:
        st.error("No data available. Please check database connection.")
        return
    
    # Prepare data
    df = prepare_data(df)
    
    # Data info
    st.sidebar.success(f"✓ Loaded {len(df)} survey responses")
    st.sidebar.info(f"📅 Date range: {df['survey_date'].min().date()} to {df['survey_date'].max().date()}")
    
    # Filters
    st.sidebar.header("🔍 Filters")
    
    # Date range filter
    min_date = df['survey_date'].min().date()
    max_date = df['survey_date'].max().date()
    
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        df = df[(df['survey_date'].dt.date >= date_range[0]) & 
                (df['survey_date'].dt.date <= date_range[1])]
    
    # Region filter
    regions = ['All Regions'] + sorted(df['region'].unique().tolist())
    selected_region = st.sidebar.selectbox("Region", regions)
    
    # School filter (depends on region)
    if selected_region != 'All Regions':
        schools_in_region = ['All Schools'] + sorted(
            df[df['region'] == selected_region]['school_id'].unique().tolist()
        )
        selected_school = st.sidebar.selectbox("School", schools_in_region)
    else:
        selected_school = 'All Schools'
    
    # Intervention filter
    intervention_filter = st.sidebar.multiselect(
        "Intervention Status",
        options=df['intervention_status'].unique().tolist(),
        default=df['intervention_status'].unique().tolist()
    )
    
    # Apply filters
    filtered_df = df[df['intervention_status'].isin(intervention_filter)].copy()
    
    if selected_region != 'All Regions':
        filtered_df = filtered_df[filtered_df['region'] == selected_region]
    
    if selected_school != 'All Schools':
        filtered_df = filtered_df[filtered_df['school_id'] == selected_school]
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview", 
        "🌍 Regional Comparison", 
        "🏫 School Analysis",
        "📊 Temporal Trends",
        "📋 Data Table"
    ])
    
    # ================================================================
    # TAB 1: OVERVIEW
    # ================================================================
    with tab1:
        st.header("Key Performance Indicators")
        
        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_performance = filtered_df['b1_overall_performance'].mean()
            st.metric(
                "Average Overall Performance",
                f"{avg_performance:.2f}",
                delta=None,
                help="Average rating on 5-point scale"
            )
        
        with col2:
            n_schools = filtered_df['school_id'].nunique()
            st.metric(
                "Schools",
                n_schools,
                help="Number of schools in filtered data"
            )
        
        with col3:
            n_teachers = filtered_df['teacher_id'].nunique()
            st.metric(
                "Teachers",
                n_teachers,
                help="Number of teachers responding"
            )
        
        with col4:
            n_responses = len(filtered_df)
            st.metric(
                "Total Responses",
                n_responses,
                help="Number of survey responses"
            )
        
        st.markdown("---")
        
        # All outcomes comparison (radar chart)
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Performance Across All Dimensions")
            fig_radar = plot_all_outcomes_comparison(filtered_df, selected_region)
            st.plotly_chart(fig_radar, use_container_width=True)
        
        with col2:
            st.subheader("Summary Statistics")
            
            outcome_cols = [
                'b1_overall_performance', 'b2_problem_solving', 
                'b3_critical_thinking', 'b4_collaboration',
                'b5_communication', 'b6_engagement', 
                'b7_behavior', 'b8_persistence'
            ]
            
            summary_data = []
            for col in outcome_cols:
                col_name = col.replace('b1_', '').replace('b2_', '').replace('b3_', '').replace('b4_', '').replace('b5_', '').replace('b6_', '').replace('b7_', '').replace('b8_', '').replace('_', ' ').title()
                summary_data.append({
                    'Outcome': col_name,
                    'Mean': f"{filtered_df[col].mean():.2f}",
                    'Std': f"{filtered_df[col].std():.2f}"
                })
            
            summary_df = pd.DataFrame(summary_data)
            st.dataframe(summary_df, hide_index=True)
        
        st.markdown("---")
        
        # Intervention comparison
        if len(filtered_df['intervention_status'].unique()) > 1:
            st.subheader("Intervention vs Control Comparison")
            
            comparison_data = filtered_df.groupby('intervention_status')[[
                'b1_overall_performance', 'b2_problem_solving', 
                'b3_critical_thinking', 'b6_engagement'
            ]].mean().round(2)
            
            comparison_data.columns = [
                'Overall Performance', 'Problem Solving',
                'Critical Thinking', 'Engagement'
            ]
            
            st.dataframe(comparison_data, use_container_width=True)
    
    # ================================================================
    # TAB 2: REGIONAL COMPARISON
    # ================================================================
    with tab2:
        st.header("Regional Performance Comparison")
        
        # Outcome selector
        outcome_selector = st.selectbox(
            "Select Outcome to Compare",
            options=[
                ('b1_overall_performance', 'Overall Performance'),
                ('b2_problem_solving', 'Problem Solving'),
                ('b3_critical_thinking', 'Critical Thinking'),
                ('b4_collaboration', 'Collaboration'),
                ('b5_communication', 'Communication'),
                ('b6_engagement', 'Engagement'),
                ('b7_behavior', 'Behavior'),
                ('b8_persistence', 'Persistence'),
                ('composite_score', 'Composite Score')
            ],
            format_func=lambda x: x[1],
            key='regional_outcome'
        )
        
        # Regional comparison bar chart
        fig_regional = plot_regional_comparison(df, outcome_selector[0])
        st.plotly_chart(fig_regional, use_container_width=True)
        
        st.markdown("---")
        
        # Regional statistics table
        st.subheader("Detailed Regional Statistics")
        
        regional_stats = df.groupby(['region', 'intervention_status']).agg({
            outcome_selector[0]: ['mean', 'std', 'count'],
            'school_id': 'nunique'
        }).round(2)
        
        regional_stats.columns = ['Mean', 'Std Dev', 'N Responses', 'N Schools']
        st.dataframe(regional_stats, use_container_width=True)
    
    # ================================================================
    # TAB 3: SCHOOL ANALYSIS
    # ================================================================
    with tab3:
        st.header("School-Level Analysis")
        
        if selected_region == 'All Regions':
            st.info("👈 Please select a specific region from the sidebar to view school comparisons.")
        else:
            # Outcome selector
            outcome_selector_school = st.selectbox(
                "Select Outcome to Compare",
                options=[
                    ('composite_score', 'Composite Score'),
                    ('b1_overall_performance', 'Overall Performance'),
                    ('b2_problem_solving', 'Problem Solving'),
                    ('b3_critical_thinking', 'Critical Thinking'),
                    ('b4_collaboration', 'Collaboration'),
                    ('b5_communication', 'Communication'),
                    ('b6_engagement', 'Engagement'),
                    ('b7_behavior', 'Behavior'),
                    ('b8_persistence', 'Persistence')
                ],
                format_func=lambda x: x[1],
                key='school_outcome'
            )
            
            # School comparison within region
            fig_schools = plot_school_comparison_within_region(
                df, selected_region, outcome_selector_school[0]
            )
            st.plotly_chart(fig_schools, use_container_width=True)
            
            st.markdown("---")
            
            # Heatmap of schools x outcomes
            st.subheader("Performance Heatmap: All Outcomes by School")
            fig_heatmap = plot_heatmap_schools_outcomes(df, selected_region)
            st.plotly_chart(fig_heatmap, use_container_width=True)
            
            st.markdown("---")
            
            # School details
            st.subheader("School Details")
            
            school_details = df[df['region'] == selected_region].groupby('school_name').agg({
                'teacher_id': 'nunique',
                'response_id': 'count',
                'intervention_status': lambda x: x.mode()[0] if len(x) > 0 else 'Unknown',
                'composite_score': ['mean', 'std']
            }).round(2)
            
            school_details.columns = ['N Teachers', 'N Responses', 'Status', 'Mean Score', 'Std Dev']
            st.dataframe(school_details, use_container_width=True)
    
    # ================================================================
    # TAB 4: TEMPORAL TRENDS
    # ================================================================
    with tab4:
        st.header("Performance Over Time")
        
        # Check if we have multiple time points
        n_timepoints = filtered_df['survey_date'].nunique()
        
        if n_timepoints < 2:
            st.warning("⚠️ Temporal analysis requires data from multiple time points. Current filter shows only one time point.")
        else:
            # Outcome selector
            outcome_selector_time = st.selectbox(
                "Select Outcome to Track",
                options=[
                    ('composite_score', 'Composite Score'),
                    ('b1_overall_performance', 'Overall Performance'),
                    ('b2_problem_solving', 'Problem Solving'),
                    ('b3_critical_thinking', 'Critical Thinking'),
                    ('b4_collaboration', 'Collaboration'),
                    ('b5_communication', 'Communication'),
                    ('b6_engagement', 'Engagement'),
                    ('b7_behavior', 'Behavior'),
                    ('b8_persistence', 'Persistence')
                ],
                format_func=lambda x: x[1],
                key='temporal_outcome'
            )
            
            # Temporal progression plot
            fig_temporal = plot_temporal_progression(
                df, outcome_selector_time[0], 
                selected_region if selected_region != 'All Regions' else None,
                selected_school if selected_school != 'All Schools' else None
            )
            st.plotly_chart(fig_temporal, use_container_width=True)
            
            st.markdown("---")
            
            # Intervention effect over time
            if len(df['intervention_status'].unique()) > 1:
                st.subheader("Intervention Effect Over Time")
                st.markdown("*This shows the difference between Treatment and Control groups over time.*")
                
                fig_effect = plot_intervention_effect_over_time(df, outcome_selector_time[0])
                if fig_effect:
                    st.plotly_chart(fig_effect, use_container_width=True)
                else:
                    st.warning("Unable to calculate intervention effect. Ensure both Treatment and Control groups have data.")
            
            st.markdown("---")
            
            # Growth rates
            st.subheader("Growth Analysis")
            
            # Calculate change from first to last observation
            first_date = df['survey_date'].min()
            last_date = df['survey_date'].max()
            
            first_period = df[df['survey_date'] == first_date].groupby('intervention_status')[outcome_selector_time[0]].mean()
            last_period = df[df['survey_date'] == last_date].groupby('intervention_status')[outcome_selector_time[0]].mean()
            
            growth_df = pd.DataFrame({
                'Initial': first_period,
                'Final': last_period,
                'Change': last_period - first_period,
                'Growth %': ((last_period - first_period) / first_period * 100).round(1)
            }).round(2)
            
            st.dataframe(growth_df, use_container_width=True)
    
    # ================================================================
    # TAB 5: DATA TABLE
    # ================================================================
    with tab5:
        st.header("Raw Data View")
        
        # Column selector
        display_cols = st.multiselect(
            "Select columns to display",
            options=filtered_df.columns.tolist(),
            default=[
                'survey_date', 'region', 'school_name', 'teacher_id',
                'intervention_status', 'b1_overall_performance',
                'b2_problem_solving', 'b6_engagement', 'composite_score'
            ]
        )
        
        if display_cols:
            st.dataframe(
                filtered_df[display_cols].sort_values('survey_date', ascending=False),
                hide_index=True,
                use_container_width=True
            )
            
            # Download button
            csv = filtered_df[display_cols].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Filtered Data as CSV",
                data=csv,
                file_name=f"survey_data_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("Please select at least one column to display.")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: gray; padding: 20px;'>
    📊 Student Performance Dashboard | Data updated: {}<br>
    For questions or issues, contact the research team
    </div>
    """.format(df['survey_date'].max().strftime('%Y-%m-%d %H:%M')), unsafe_allow_html=True)

# ====================================================================
# RUN APP
# ====================================================================

if __name__ == "__main__":
    main()




