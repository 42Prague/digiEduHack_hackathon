"""
Comprehensive dashboard rendering module with visualizations
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os
import requests


def get_available_tables(conn):
    """Get list of available tables in the database"""
    try:
        tables = conn.execute("SHOW TABLES").fetchdf()
        if not tables.empty:
            return tables['name'].tolist()
        return []
    except Exception:
        return []


def get_key_metrics(conn):
    """Get key performance indicators"""
    metrics = {}
    try:
        # Total schools
        try:
            schools_count = conn.execute("SELECT COUNT(DISTINCT school_id) FROM schools").fetchone()[0]
            metrics['total_schools'] = schools_count
        except:
            metrics['total_schools'] = 0
        
        # Total students
        try:
            students_count = conn.execute("SELECT COUNT(DISTINCT student_id_hash) FROM students").fetchone()[0]
            metrics['total_students'] = students_count
        except:
            metrics['total_students'] = 0
        
        # Total assessments
        try:
            assessments_count = conn.execute("SELECT COUNT(*) FROM assessments").fetchone()[0]
            metrics['total_assessments'] = assessments_count
        except:
            metrics['total_assessments'] = 0
        
        # Average score
        try:
            avg_score = conn.execute("SELECT AVG(score) FROM assessments").fetchone()[0]
            metrics['avg_score'] = round(avg_score, 2) if avg_score else 0
        except:
            metrics['avg_score'] = 0
        
        # Total interventions
        try:
            interventions_count = conn.execute("SELECT COUNT(*) FROM interventions").fetchone()[0]
            metrics['total_interventions'] = interventions_count
        except:
            metrics['total_interventions'] = 0
        
    except Exception as e:
        st.warning(f"Error calculating metrics: {str(e)}")
    
    return metrics


def get_scores_by_region(conn):
    """Get average scores by region"""
    try:
        query = """
        SELECT 
            s.region,
            AVG(a.score) as avg_score,
            COUNT(*) as assessment_count,
            COUNT(DISTINCT a.student_id_hash) as student_count
        FROM assessments a
        JOIN students st ON a.student_id_hash = st.student_id_hash
        JOIN schools s ON st.school_id = s.school_id
        GROUP BY s.region
        ORDER BY avg_score DESC
        """
        return conn.execute(query).fetchdf()
    except Exception as e:
        st.warning(f"Error fetching scores by region: {str(e)}")
        return pd.DataFrame()


def get_scores_by_subject(conn):
    """Get average scores by subject"""
    try:
        query = """
        SELECT 
            subject,
            AVG(score) as avg_score,
            COUNT(*) as assessment_count,
            COUNT(DISTINCT student_id_hash) as student_count
        FROM assessments
        GROUP BY subject
        ORDER BY avg_score DESC
        """
        return conn.execute(query).fetchdf()
    except Exception as e:
        st.warning(f"Error fetching scores by subject: {str(e)}")
        return pd.DataFrame()


def get_equity_analysis(conn):
    """Get equity analysis by deprivation quintile"""
    try:
        query = """
        WITH quintiles AS (
            SELECT 
                s.school_id,
                s.deprivation_index,
                NTILE(5) OVER (ORDER BY s.deprivation_index) as quintile
            FROM schools s
        )
        SELECT 
            q.quintile,
            AVG(a.score) as avg_score,
            COUNT(*) as assessment_count,
            COUNT(DISTINCT st.student_id_hash) as student_count,
            AVG(s.deprivation_index) as avg_deprivation
        FROM assessments a
        JOIN students st ON a.student_id_hash = st.student_id_hash
        JOIN quintiles q ON st.school_id = q.school_id
        JOIN schools s ON st.school_id = s.school_id
        GROUP BY q.quintile
        ORDER BY q.quintile
        """
        return conn.execute(query).fetchdf()
    except Exception as e:
        st.warning(f"Error fetching equity analysis: {str(e)}")
        return pd.DataFrame()


def get_intervention_effectiveness(conn):
    """Get intervention effectiveness metrics"""
    try:
        query = """
        SELECT 
            i.type,
            COUNT(DISTINCT i.intervention_id) as intervention_count,
            COUNT(DISTINCT i.school_id) as school_count,
            AVG(i.participant_count) as avg_participants,
            AVG(i.budget) as avg_budget
        FROM interventions i
        GROUP BY i.type
        ORDER BY intervention_count DESC
        """
        return conn.execute(query).fetchdf()
    except Exception as e:
        st.warning(f"Error fetching intervention data: {str(e)}")
        return pd.DataFrame()


def get_scores_over_time(conn):
    """Get average scores over time"""
    try:
        query = """
        SELECT 
            DATE_TRUNC('month', date) as month,
            AVG(score) as avg_score,
            COUNT(*) as assessment_count
        FROM assessments
        WHERE date IS NOT NULL
        GROUP BY DATE_TRUNC('month', date)
        ORDER BY month
        """
        return conn.execute(query).fetchdf()
    except Exception as e:
        st.warning(f"Error fetching time series data: {str(e)}")
        return pd.DataFrame()


def get_regional_comparison(conn):
    """Get comprehensive regional comparison"""
    try:
        query = """
        SELECT 
            s.region,
            COUNT(DISTINCT s.school_id) as school_count,
            COUNT(DISTINCT st.student_id_hash) as student_count,
            AVG(a.score) as avg_score,
            AVG(s.deprivation_index) as avg_deprivation,
            AVG(s.enrollment) as avg_enrollment,
            AVG(s.free_reduced_lunch_pct) as avg_frl_pct
        FROM schools s
        LEFT JOIN students st ON s.school_id = st.school_id
        LEFT JOIN assessments a ON st.student_id_hash = a.student_id_hash
        GROUP BY s.region
        ORDER BY avg_score DESC
        """
        return conn.execute(query).fetchdf()
    except Exception as e:
        st.warning(f"Error fetching regional comparison: {str(e)}")
        return pd.DataFrame()


def render_overview_tab(conn):
    """Render the comprehensive dashboard with visualizations"""
    if conn is None:
        st.error("❌ Database connection not available")
        return
    
    # Get available tables
    tables = get_available_tables(conn)
    
    if not tables:
        st.warning("⚠️ No tables found in the database")
        st.info("💡 **To load data:**\n"
               "1. Go to the '📂 Data Source' page\n"
               "2. Upload or load Parquet files from MinIO\n"
               "3. The tables will be automatically created in DuckDB")
        return
    
    # Check if we have the required tables
    required_tables = ['schools', 'students', 'assessments']
    has_required = all(table in tables for table in required_tables)
    
    if not has_required:
        st.warning("⚠️ Missing required tables for dashboard. Showing basic overview.")
        # Show basic table overview
        st.subheader("📋 Available Tables")
        cols = st.columns(min(len(tables), 4))
        for idx, table in enumerate(tables):
            with cols[idx % len(cols)]:
                try:
                    count_result = conn.execute(f"SELECT COUNT(*) as count FROM {table}").fetchone()
                    row_count = count_result[0] if count_result else 0
                    schema = conn.execute(f"DESCRIBE {table}").fetchdf()
                    col_count = len(schema)
                    st.metric(
                        label=f"**{table}**",
                        value=f"{row_count:,} rows",
                        delta=f"{col_count} columns"
                    )
                except Exception as e:
                    st.error(f"Error reading {table}: {str(e)}")
        return
    
    # ========== KEY METRICS SECTION ==========
    st.subheader("📊 Key Performance Indicators")
    metrics = get_key_metrics(conn)
    
    kpi_cols = st.columns(5)
    with kpi_cols[0]:
        st.metric("🏫 Total Schools", f"{metrics.get('total_schools', 0):,}")
    with kpi_cols[1]:
        st.metric("👥 Total Students", f"{metrics.get('total_students', 0):,}")
    with kpi_cols[2]:
        st.metric("📝 Total Assessments", f"{metrics.get('total_assessments', 0):,}")
    with kpi_cols[3]:
        st.metric("⭐ Average Score", f"{metrics.get('avg_score', 0):.2f}")
    with kpi_cols[4]:
        st.metric("🎯 Interventions", f"{metrics.get('total_interventions', 0):,}")
    
    st.markdown("---")
    
    # ========== PERFORMANCE VISUALIZATIONS ==========
    st.subheader("📈 Performance Analysis")
    
    # Row 1: Scores by Region and Subject
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🗺️ Average Scores by Region")
        region_scores = get_scores_by_region(conn)
        if not region_scores.empty:
            fig = px.bar(
                region_scores,
                x='region',
                y='avg_score',
                color='avg_score',
                color_continuous_scale='Viridis',
                title="Average Assessment Scores by Region",
                labels={'region': 'Region', 'avg_score': 'Average Score'},
                text='avg_score'
            )
            fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No regional data available")
    
    with col2:
        st.markdown("#### 📚 Average Scores by Subject")
        subject_scores = get_scores_by_subject(conn)
        if not subject_scores.empty:
            fig = px.pie(
                subject_scores,
                values='avg_score',
                names='subject',
                title="Score Distribution by Subject",
                hole=0.4
            )
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No subject data available")
    
    st.markdown("---")
    
    # ========== EQUITY ANALYSIS ==========
    st.subheader("⚖️ Equity Analysis")
    
    equity_data = get_equity_analysis(conn)
    if not equity_data.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Scores by Deprivation Quintile")
            fig = px.bar(
                equity_data,
                x='quintile',
                y='avg_score',
                color='avg_deprivation',
                color_continuous_scale='RdBu_r',
                title="Average Scores by Deprivation Quintile (1=Least Deprived, 5=Most Deprived)",
                labels={'quintile': 'Deprivation Quintile', 'avg_score': 'Average Score', 'avg_deprivation': 'Avg Deprivation Index'},
                text='avg_score'
            )
            fig.update_traces(texttemplate='%{text:.1f}', textposition='outside')
            fig.update_layout(showlegend=True, height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 📈 Student Count by Quintile")
            fig = px.bar(
                equity_data,
                x='quintile',
                y='student_count',
                title="Student Count by Deprivation Quintile",
                labels={'quintile': 'Deprivation Quintile', 'student_count': 'Number of Students'},
                color='quintile',
                color_continuous_scale='Blues'
            )
            fig.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No equity data available")
    
    st.markdown("---")
    
    # ========== INTERVENTIONS ==========
    st.subheader("🎯 Intervention Analysis")
    
    intervention_data = get_intervention_effectiveness(conn)
    if not intervention_data.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### 📊 Interventions by Type")
            fig = px.bar(
                intervention_data,
                x='type',
                y='intervention_count',
                title="Number of Interventions by Type",
                labels={'type': 'Intervention Type', 'intervention_count': 'Count'},
                color='intervention_count',
                color_continuous_scale='Greens'
            )
            fig.update_xaxes(tickangle=45)
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.markdown("#### 💰 Average Budget by Intervention Type")
            if 'avg_budget' in intervention_data.columns and intervention_data['avg_budget'].notna().any():
                fig = px.bar(
                    intervention_data,
                    x='type',
                    y='avg_budget',
                    title="Average Budget by Intervention Type",
                    labels={'type': 'Intervention Type', 'avg_budget': 'Average Budget'},
                    color='avg_budget',
                    color_continuous_scale='Oranges'
                )
                fig.update_xaxes(tickangle=45)
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.info("Budget data not available")
    else:
        st.info("No intervention data available")
    
    st.markdown("---")
    
    # ========== TIME SERIES ==========
    st.subheader("📅 Performance Over Time")
    
    time_data = get_scores_over_time(conn)
    if not time_data.empty and len(time_data) > 1:
        fig = px.line(
            time_data,
            x='month',
            y='avg_score',
            markers=True,
            title="Average Assessment Scores Over Time",
            labels={'month': 'Month', 'avg_score': 'Average Score'},
            color_discrete_sequence=['#667eea']
        )
        fig.update_traces(line_width=3, marker_size=8)
        fig.update_layout(height=400, hovermode='x unified')
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Insufficient time series data available")
    
    st.markdown("---")
    
    # ========== REGIONAL COMPARISON TABLE ==========
    st.subheader("🌍 Regional Comparison")
    
    regional_data = get_regional_comparison(conn)
    if not regional_data.empty:
        # Format the dataframe for better display
        display_df = regional_data.copy()
        if 'avg_score' in display_df.columns:
            display_df['avg_score'] = display_df['avg_score'].round(2)
        if 'avg_deprivation' in display_df.columns:
            display_df['avg_deprivation'] = display_df['avg_deprivation'].round(2)
        if 'avg_enrollment' in display_df.columns:
            display_df['avg_enrollment'] = display_df['avg_enrollment'].round(0)
        if 'avg_frl_pct' in display_df.columns:
            display_df['avg_frl_pct'] = display_df['avg_frl_pct'].round(1)
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No regional comparison data available")
    
    st.markdown("---")
    
    # ========== TABLE OVERVIEW (Collapsible) ==========
    with st.expander("📋 Database Tables Overview"):
        st.subheader("Available Tables")
        cols = st.columns(min(len(tables), 4))
        
        for idx, table in enumerate(tables):
            with cols[idx % len(cols)]:
                try:
                    count_result = conn.execute(f"SELECT COUNT(*) as count FROM {table}").fetchone()
                    row_count = count_result[0] if count_result else 0
                    schema = conn.execute(f"DESCRIBE {table}").fetchdf()
                    col_count = len(schema)
                    st.metric(
                        label=f"**{table}**",
                        value=f"{row_count:,} rows",
                        delta=f"{col_count} columns"
                    )
                except Exception as e:
                    st.error(f"Error reading {table}: {str(e)}")
        
        # Show table details
        for table in tables:
            with st.expander(f"📊 {table} - Schema"):
                try:
                    schema = conn.execute(f"DESCRIBE {table}").fetchdf()
                    st.dataframe(schema, use_container_width=True)
                except Exception as e:
                    st.error(f"Error reading table schema: {str(e)}")

