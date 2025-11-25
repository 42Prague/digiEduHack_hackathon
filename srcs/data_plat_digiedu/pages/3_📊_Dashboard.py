"""
====================================================================
DASHBOARD PAGE
Interactive Analytics and Visualizations
====================================================================
"""

import streamlit as st
import sys
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_utils import (
    get_database_connection, 
    get_all_responses,
    get_unique_values,
    execute_query
)

st.set_page_config(page_title="Dashboard", page_icon="📊", layout="wide")

# ====================================================================
# DATA PREPARATION
# ====================================================================

@st.cache_data(ttl=300)
def load_and_prepare_data(_engine):
    """Load data from database and prepare for analysis."""
    df = get_all_responses(_engine)
    
    if df is None or df.empty:
        return None
    
    # Convert dates
    df['survey_date'] = pd.to_datetime(df['survey_date'])
    
    # Calculate time variables
    min_date = df['survey_date'].min()
    df['time_years'] = (df['survey_date'] - min_date).dt.days / 365.25
    df['time_months'] = (df['survey_date'] - min_date).dt.days / 30.44
    
    # Create composite score
    outcome_cols = [
        'b1_overall_performance', 'b2_problem_solving', 
        'b3_critical_thinking', 'b4_collaboration',
        'b5_communication', 'b6_engagement', 
        'b7_behavior', 'b8_persistence'
    ]
    df['composite_score'] = df[outcome_cols].mean(axis=1)
    
    return df

# ====================================================================
# VISUALIZATION FUNCTIONS
# ====================================================================

def plot_regional_comparison(df, outcome='b1_overall_performance'):
    """Create regional comparison chart."""
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
        title='Performance by Region',
        color_discrete_map={'Treatment': '#2ecc71', 'Control': '#e74c3c'}
    )
    fig.update_layout(height=500)
    return fig

def plot_temporal_trends(df, outcome='b1_overall_performance'):
    """Create temporal trend chart."""
    grouped = df.groupby(['survey_date', 'intervention_status']).agg({
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
        title='Performance Over Time',
        color_discrete_map={'Treatment': '#2ecc71', 'Control': '#e74c3c'}
    )
    fig.update_layout(height=500)
    return fig

def plot_school_comparison(df, region, outcome='composite_score'):
    """Compare schools within a region."""
    region_df = df[df['region'] == region].copy()
    
    grouped = region_df.groupby(['school_name', 'intervention_status']).agg({
        outcome: ['mean', 'count']
    }).reset_index()
    
    grouped.columns = ['school_name', 'intervention_status', 'mean', 'count']
    grouped = grouped.sort_values('mean', ascending=False)
    
    fig = px.bar(
        grouped,
        x='school_name',
        y='mean',
        color='intervention_status',
        title=f'School Performance in {region}',
        color_discrete_map={'Treatment': '#2ecc71', 'Control': '#e74c3c'}
    )
    fig.update_xaxes(tickangle=-45)
    fig.update_layout(height=500)
    return fig

def plot_radar_chart(df, region=None):
    """Create radar chart for all outcomes."""
    outcome_cols = [
        'b1_overall_performance', 'b2_problem_solving', 
        'b3_critical_thinking', 'b4_collaboration',
        'b5_communication', 'b6_engagement', 
        'b7_behavior', 'b8_persistence'
    ]
    
    labels = ['Overall', 'Problem Solving', 'Critical Thinking', 'Collaboration',
             'Communication', 'Engagement', 'Behavior', 'Persistence']
    
    filtered_df = df if region is None else df[df['region'] == region]
    
    fig = go.Figure()
    
    for status in filtered_df['intervention_status'].unique():
        subset = filtered_df[filtered_df['intervention_status'] == status]
        values = subset[outcome_cols].mean().values
        
        fig.add_trace(go.Scatterpolar(
            r=values,
            theta=labels,
            fill='toself',
            name=status
        ))
    
    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
        title='All Performance Dimensions',
        height=600
    )
    return fig

# ====================================================================
# MAIN DASHBOARD
# ====================================================================

def main():
    st.title("📊 Performance Dashboard")
    
    # Add refresh button and info
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("### Interactive Analytics and Visualizations")
    with col3:
        if st.button("🔄 Refresh Data", help="Clear cache and reload latest data from database", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache cleared! Reloading...")
            st.rerun()
    
    # Load data
    engine = get_database_connection()
    
    with st.spinner("Loading data..."):
        df = load_and_prepare_data(engine)
    
    # Show data freshness info
    if df is not None and not df.empty:
        st.caption(f"📅 Data loaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Total responses: {len(df)} | Cached for 5 minutes")
    
    if df is None or df.empty:
        st.warning("⚠️ No data available. Please submit responses through the Survey Form first.")
        st.info("Navigate to the **Survey Form** page to start collecting data.")
        return
    
    # Sidebar filters
    st.sidebar.header("🔍 Filters")
    
    # Date range
    min_date = df['survey_date'].min().date()
    max_date = df['survey_date'].max().date()
    
    date_range = st.sidebar.date_input(
        "Date Range",
        value=(min_date, max_date),
        min_value=min_date,
        max_value=max_date
    )
    
    # Apply date filter
    if len(date_range) == 2:
        df = df[(df['survey_date'].dt.date >= date_range[0]) & 
                (df['survey_date'].dt.date <= date_range[1])]
    
    # Region filter
    regions = ['All Regions'] + sorted(df['region'].unique().tolist())
    selected_region = st.sidebar.selectbox("Region", regions)
    
    # Intervention filter
    intervention_options = st.sidebar.multiselect(
        "Intervention Status",
        options=df['intervention_status'].unique().tolist(),
        default=df['intervention_status'].unique().tolist()
    )
    
    # Apply filters
    filtered_df = df[df['intervention_status'].isin(intervention_options)].copy()
    
    if selected_region != 'All Regions':
        filtered_df = filtered_df[filtered_df['region'] == selected_region]
    
    # Summary stats
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 Data Summary")
    st.sidebar.metric("Total Responses", len(filtered_df))
    st.sidebar.metric("Schools", filtered_df['school_id'].nunique())
    st.sidebar.metric("Teachers", filtered_df['teacher_id'].nunique())
    st.sidebar.metric("Regions", filtered_df['region'].nunique())
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📈 Overview",
        "🌍 Regional Analysis",
        "🏫 School Analysis",
        "📊 Temporal Trends"
    ])
    
    # ================================================================
    # TAB 1: OVERVIEW
    # ================================================================
    with tab1:
        st.header("Key Performance Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            avg_perf = filtered_df['b1_overall_performance'].mean()
            st.metric("Avg Overall Performance", f"{avg_perf:.2f}/5")
        
        with col2:
            avg_engage = filtered_df['b6_engagement'].mean()
            st.metric("Avg Engagement", f"{avg_engage:.2f}/5")
        
        with col3:
            avg_problem = filtered_df['b2_problem_solving'].mean()
            st.metric("Avg Problem Solving", f"{avg_problem:.2f}/5")
        
        with col4:
            avg_composite = filtered_df['composite_score'].mean()
            st.metric("Composite Score", f"{avg_composite:.2f}/5")
        
        st.markdown("---")
        
        # Radar chart
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Performance Across All Dimensions")
            fig_radar = plot_radar_chart(filtered_df, None if selected_region == 'All Regions' else selected_region)
            st.plotly_chart(fig_radar, use_container_width=True)
        
        with col2:
            st.subheader("Summary by Group")
            
            if len(intervention_options) > 1:
                comparison = filtered_df.groupby('intervention_status')[[
                    'b1_overall_performance', 'b6_engagement', 'composite_score'
                ]].mean().round(2)
                
                comparison.columns = ['Overall', 'Engagement', 'Composite']
                st.dataframe(comparison, use_container_width=True)
                
                # Calculate effect size
                if 'Treatment' in comparison.index and 'Control' in comparison.index:
                    effect = comparison.loc['Treatment'] - comparison.loc['Control']
                    st.markdown("**Intervention Effect:**")
                    for col in effect.index:
                        st.metric(col, f"{effect[col]:+.2f}", delta_color="normal")
    
    # ================================================================
    # TAB 2: REGIONAL ANALYSIS
    # ================================================================
    with tab2:
        st.header("Regional Performance Comparison")
        
        outcome_select = st.selectbox(
            "Select Outcome",
            options=[
                ('b1_overall_performance', 'Overall Performance'),
                ('b2_problem_solving', 'Problem Solving'),
                ('b3_critical_thinking', 'Critical Thinking'),
                ('b6_engagement', 'Engagement'),
                ('composite_score', 'Composite Score')
            ],
            format_func=lambda x: x[1]
        )
        
        fig_regional = plot_regional_comparison(df, outcome_select[0])
        st.plotly_chart(fig_regional, use_container_width=True)
        
        st.markdown("---")
        
        # Regional statistics table
        st.subheader("Detailed Statistics by Region")
        
        regional_stats = df.groupby(['region', 'intervention_status']).agg({
            'b1_overall_performance': ['mean', 'std', 'count'],
            'composite_score': 'mean'
        }).round(2)
        
        regional_stats.columns = ['Mean Performance', 'Std Dev', 'N Responses', 'Composite']
        st.dataframe(regional_stats, use_container_width=True)
    
    # ================================================================
    # TAB 3: SCHOOL ANALYSIS
    # ================================================================
    with tab3:
        st.header("School-Level Analysis")
        
        if selected_region == 'All Regions':
            st.info("👈 Select a specific region from the sidebar to view school comparisons.")
        else:
            outcome_select_school = st.selectbox(
                "Select Outcome for School Comparison",
                options=[
                    ('composite_score', 'Composite Score'),
                    ('b1_overall_performance', 'Overall Performance'),
                    ('b6_engagement', 'Engagement')
                ],
                format_func=lambda x: x[1]
            )
            
            fig_schools = plot_school_comparison(df, selected_region, outcome_select_school[0])
            st.plotly_chart(fig_schools, use_container_width=True)
            
            st.markdown("---")
            
            # School details table
            st.subheader("School Details")
            
            school_stats = df[df['region'] == selected_region].groupby('school_name').agg({
                'teacher_id': 'nunique',
                'response_id': 'count',
                'intervention_status': lambda x: x.mode()[0] if len(x) > 0 else 'Unknown',
                'composite_score': ['mean', 'std']
            }).round(2)
            
            school_stats.columns = ['N Teachers', 'N Responses', 'Status', 'Mean Score', 'Std Dev']
            st.dataframe(school_stats, use_container_width=True)
    
    # ================================================================
    # TAB 4: TEMPORAL TRENDS
    # ================================================================
    with tab4:
        st.header("Performance Trends Over Time")
        
        n_timepoints = filtered_df['survey_date'].nunique()
        
        if n_timepoints < 2:
            st.warning("⚠️ Temporal analysis requires data from multiple time points.")
        else:
            outcome_select_time = st.selectbox(
                "Select Outcome for Temporal Analysis",
                options=[
                    ('b1_overall_performance', 'Overall Performance'),
                    ('b6_engagement', 'Engagement'),
                    ('b2_problem_solving', 'Problem Solving'),
                    ('composite_score', 'Composite Score')
                ],
                format_func=lambda x: x[1]
            )
            
            fig_temporal = plot_temporal_trends(df, outcome_select_time[0])
            st.plotly_chart(fig_temporal, use_container_width=True)
            
            st.markdown("---")
            
            # Growth analysis
            st.subheader("Growth Analysis")
            
            first_date = df['survey_date'].min()
            last_date = df['survey_date'].max()
            
            first_period = df[df['survey_date'] == first_date].groupby('intervention_status')[outcome_select_time[0]].mean()
            last_period = df[df['survey_date'] == last_date].groupby('intervention_status')[outcome_select_time[0]].mean()
            
            growth_df = pd.DataFrame({
                'Initial': first_period,
                'Final': last_period,
                'Change': last_period - first_period,
                'Growth %': ((last_period - first_period) / first_period * 100).round(1)
            }).round(2)
            
            st.dataframe(growth_df, use_container_width=True)
    
    # Footer
    st.markdown("---")
    st.markdown(f"""
    <div style='text-align: center; color: gray;'>
    Last updated: {df['survey_date'].max().strftime('%Y-%m-%d')} | 
    Total responses: {len(df):,}
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

