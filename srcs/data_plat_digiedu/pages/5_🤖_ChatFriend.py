"""
====================================================================
CHATFRIEND - AI-POWERED QUALITATIVE ANALYSIS
Semantic Search, Theme Extraction, and Insights using Local LLM
====================================================================
"""

import streamlit as st
import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime
from collections import Counter
import re
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_utils import get_database_connection, execute_query

st.set_page_config(page_title="ChatFriend AI", page_icon="🤖", layout="wide")

# ====================================================================
# OLLAMA SETUP AND CONFIGURATION
# ====================================================================

def check_ollama_available():
    """Check if Ollama is installed and running."""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags', timeout=2)
        return response.status_code == 200
    except:
        return False

def get_ollama_models():
    """Get list of available Ollama models."""
    try:
        import requests
        response = requests.get('http://localhost:11434/api/tags')
        if response.status_code == 200:
            models = response.json().get('models', [])
            return [m['name'] for m in models]
        return []
    except:
        return []

def call_ollama(prompt, model="llama3", temperature=0.7):
    """Call Ollama API with a prompt."""
    try:
        import requests
        
        response = requests.post(
            'http://localhost:11434/api/generate',
            json={
                'model': model,
                'prompt': prompt,
                'stream': False,
                'temperature': temperature
            },
            timeout=60
        )
        
        if response.status_code == 200:
            return response.json().get('response', '')
        else:
            return f"Error: {response.status_code}"
    except Exception as e:
        return f"Error calling Ollama: {str(e)}"

def embed_text(text, model="nomic-embed-text"):
    """Generate embeddings for text using Ollama."""
    try:
        import requests
        
        response = requests.post(
            'http://localhost:11434/api/embeddings',
            json={
                'model': model,
                'prompt': text
            },
            timeout=30
        )
        
        if response.status_code == 200:
            return response.json().get('embedding', [])
        return None
    except:
        return None

# ====================================================================
# DATA LOADING
# ====================================================================

@st.cache_data(ttl=300)
def load_qualitative_data(_engine):
    """Load all qualitative responses from database."""
    query = """
    SELECT 
        response_id,
        survey_date,
        teacher_id,
        school_id,
        school_name,
        region,
        intervention_status,
        teaching_experience_years,
        grade_level,
        subject_area,
        intervention_duration_months,
        f1_performance_factors,
        f2_effective_practice,
        f3_challenges,
        f4_additional_comments
    FROM teacher_survey_responses
    ORDER BY survey_date DESC
    """
    
    df = execute_query(_engine, query)
    
    if df is not None and not df.empty:
        df['survey_date'] = pd.to_datetime(df['survey_date'])
        
        # Calculate time from baseline
        min_date = df['survey_date'].min()
        df['months_from_baseline'] = ((df['survey_date'] - min_date).dt.days / 30.44).round(1)
        
        # Create time period labels
        df['time_period'] = pd.cut(
            df['months_from_baseline'],
            bins=[-0.1, 3, 9, 15, 21, 100],
            labels=['Baseline (0-3mo)', '6 Months', '12 Months', '18 Months', '24+ Months']
        )
        
        # Combine all text fields into one searchable field
        df['all_text'] = df.apply(lambda row: ' '.join([
            str(row['f1_performance_factors']) if pd.notna(row['f1_performance_factors']) else '',
            str(row['f2_effective_practice']) if pd.notna(row['f2_effective_practice']) else '',
            str(row['f3_challenges']) if pd.notna(row['f3_challenges']) else '',
            str(row['f4_additional_comments']) if pd.notna(row['f4_additional_comments']) else ''
        ]), axis=1)
    
    return df

# ====================================================================
# SEMANTIC SEARCH (Simple keyword-based with scoring)
# ====================================================================

def semantic_search(df, query, top_k=10):
    """
    Perform semantic search on qualitative responses.
    Uses keyword matching with TF-IDF-like scoring.
    """
    query_terms = query.lower().split()
    
    # Score each response based on query terms
    scores = []
    for idx, row in df.iterrows():
        text = row['all_text'].lower()
        score = 0
        
        for term in query_terms:
            # Count occurrences
            count = text.count(term)
            # Boost score for exact matches
            if term in text:
                score += count * 1.5
            # Check for partial matches
            words = text.split()
            for word in words:
                if term in word:
                    score += 0.5
        
        scores.append(score)
    
    df['relevance_score'] = scores
    
    # Filter to only responses with non-zero scores
    results = df[df['relevance_score'] > 0].sort_values('relevance_score', ascending=False).head(top_k)
    
    return results

# ====================================================================
# THEME EXTRACTION
# ====================================================================

def extract_themes_simple(df, field='all_text'):
    """Extract common themes using keyword frequency analysis."""
    
    # Common stop words to exclude
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'is', 'are', 'was', 'were', 'been', 'be', 'have', 'has',
        'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may',
        'might', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'we',
        'they', 'my', 'your', 'our', 'their', 'it', 'its', 'im', 'ive'
    }
    
    # Extract all words
    all_text = ' '.join(df[field].dropna().astype(str).tolist()).lower()
    words = re.findall(r'\b[a-z]{4,}\b', all_text)
    
    # Filter and count
    filtered_words = [w for w in words if w not in stop_words]
    word_counts = Counter(filtered_words)
    
    return word_counts.most_common(30)

def extract_themes_llm(df, model="llama3"):
    """Extract themes using LLM analysis."""
    
    # Sample responses to analyze (to keep prompt manageable)
    sample_size = min(20, len(df))
    sample_responses = df.sample(sample_size)['all_text'].tolist()
    
    # Create combined text
    combined_text = '\n\n---\n\n'.join([r for r in sample_responses if r and len(r) > 10])
    
    if not combined_text:
        return "No text available for analysis."
    
    prompt = f"""Analyze these teacher survey responses and identify the main themes and patterns.

TEACHER RESPONSES:
{combined_text[:3000]}  

Please identify:
1. Top 5 most common themes
2. Key concerns or challenges mentioned
3. Positive outcomes or successes noted
4. Any patterns related to student performance

Format your response as:
**MAIN THEMES:**
- Theme 1: ...
- Theme 2: ...

**KEY CONCERNS:**
- ...

**POSITIVE OUTCOMES:**
- ...

**PATTERNS:**
- ...
"""
    
    return call_ollama(prompt, model=model, temperature=0.3)

# ====================================================================
# COMPARATIVE ANALYSIS
# ====================================================================

def compare_groups(df, group_by='intervention_status', model="llama3"):
    """Compare responses between different groups."""
    
    groups = df[group_by].unique()
    
    if len(groups) < 2:
        return "Not enough groups to compare."
    
    results = {}
    
    for group in groups:
        group_df = df[df[group_by] == group]
        group_text = ' '.join(group_df['all_text'].dropna().tolist())[:2000]
        results[group] = group_text
    
    # Create comparison prompt
    prompt = f"""Compare and contrast these teacher survey responses from different groups:

GROUP 1 ({groups[0]}):
{results[groups[0]]}

GROUP 2 ({groups[1]}):
{results[groups[1]]}

Please analyze:
1. What are the key differences in teacher perspectives?
2. What themes are unique to each group?
3. What similarities exist between groups?
4. What do these differences suggest about the intervention's impact?

Provide a concise comparative analysis.
"""
    
    return call_ollama(prompt, model=model, temperature=0.4)

# ====================================================================
# TEMPORAL TRENDS
# ====================================================================

def analyze_temporal_trends(df, model="llama3"):
    """Analyze how responses change over time."""
    
    if 'time_period' not in df.columns:
        return "Time period data not available."
    
    time_periods = ['Baseline (0-3mo)', '6 Months', '12 Months', '18 Months', '24+ Months']
    
    temporal_summaries = {}
    
    for period in time_periods:
        period_df = df[df['time_period'] == period]
        if not period_df.empty:
            period_text = ' '.join(period_df['all_text'].dropna().tolist())[:1500]
            temporal_summaries[period] = period_text
    
    if len(temporal_summaries) < 2:
        return "Not enough time periods with data to analyze trends."
    
    # Create temporal analysis prompt
    periods_text = '\n\n'.join([f"**{period}:**\n{text}" for period, text in temporal_summaries.items()])
    
    prompt = f"""Analyze how teacher perspectives evolve over time based on these survey responses:

{periods_text}

Please identify:
1. How do teacher perceptions change from baseline to later time points?
2. What new themes emerge over time?
3. What challenges persist vs. what improves?
4. What does this suggest about the intervention's trajectory?

Provide a concise temporal analysis.
"""
    
    return call_ollama(prompt, model=model, temperature=0.4)

# ====================================================================
# SUMMARY GENERATION
# ====================================================================

def generate_summary(df, focus=None, model="llama3"):
    """Generate a comprehensive summary of qualitative data."""
    
    # Sample responses
    sample_size = min(30, len(df))
    sample_text = ' '.join(df.sample(sample_size)['all_text'].tolist())[:4000]
    
    if focus:
        prompt = f"""Summarize these teacher survey responses with a focus on: {focus}

RESPONSES:
{sample_text}

Provide a comprehensive summary that:
1. Highlights key findings related to {focus}
2. Identifies patterns and themes
3. Notes important quotes or insights
4. Provides actionable recommendations

Be specific and evidence-based.
"""
    else:
        prompt = f"""Summarize these teacher survey responses about student performance and intervention effectiveness:

RESPONSES:
{sample_text}

Provide a comprehensive summary that:
1. Highlights overall patterns and themes
2. Notes key challenges and successes
3. Identifies differences between intervention and control groups (if mentioned)
4. Provides actionable insights

Be specific and evidence-based.
"""
    
    return call_ollama(prompt, model=model, temperature=0.5)

# ====================================================================
# MAIN PAGE
# ====================================================================

def main():
    st.title("🤖 ChatFriend - AI Qualitative Analysis")
    
    st.markdown("""
    ### Your AI Assistant for Qualitative Insights
    
    ChatFriend uses a local LLM to help you analyze teacher narratives and discover meaningful patterns.
    """)
    
    # Check Ollama status
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.markdown("**System Status:**")
    
    with col3:
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.rerun()
    
    ollama_available = check_ollama_available()
    
    if ollama_available:
        st.success("✅ Ollama is running locally")
        available_models = get_ollama_models()
        
        if available_models:
            st.info(f"📦 Available models: {', '.join(available_models)}")
            
            # Model selection
            default_model = 'llama3' if 'llama3' in available_models else available_models[0]
            selected_model = st.selectbox(
                "Select LLM Model:",
                options=available_models,
                index=available_models.index(default_model) if default_model in available_models else 0
            )
        else:
            st.warning("⚠️ No models found. Please install a model: `ollama pull llama3`")
            selected_model = "llama3"
    else:
        st.error("""
        ❌ **Ollama is not running**
        
        To use ChatFriend, you need to:
        1. Install Ollama: https://ollama.ai
        2. Pull a model: `ollama pull llama3`
        3. Start Ollama (it should run automatically)
        
        Then refresh this page.
        """)
        return
    
    st.markdown("---")
    
    # Load data
    engine = get_database_connection()
    
    with st.spinner("Loading qualitative data..."):
        df = load_qualitative_data(engine)
    
    if df is None or df.empty:
        st.warning("⚠️ No qualitative data available. Please submit responses through the Survey Form first.")
        return
    
    # Show data statistics
    st.caption(f"📅 Loaded {len(df)} responses | Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # ====================================================================
    # ANALYSIS TABS
    # ====================================================================
    
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🔍 Semantic Search",
        "🎯 Theme Extraction", 
        "⚖️ Comparative Analysis",
        "⏱️ Temporal Trends",
        "📝 Summary Generation"
    ])
    
    # TAB 1: SEMANTIC SEARCH
    with tab1:
        st.markdown("### 🔍 Semantic Search")
        st.markdown("*Search teacher responses by keywords and relevance*")
        
        search_query = st.text_input(
            "Enter search terms:",
            placeholder="e.g., student engagement, problem solving, time constraints",
            key="search_query"
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            search_filters = st.multiselect(
                "Filter by:",
                options=['intervention_status', 'region', 'time_period'],
                default=[]
            )
        
        with col2:
            top_k = st.number_input("Results to show:", min_value=5, max_value=50, value=10)
        
        if st.button("🔍 Search", type="primary", use_container_width=True):
            if search_query:
                with st.spinner("Searching..."):
                    # Apply filters
                    filtered_df = df.copy()
                    
                    # Perform search
                    results = semantic_search(filtered_df, search_query, top_k=top_k)
                    
                    if not results.empty:
                        st.success(f"✅ Found {len(results)} relevant responses")
                        
                        # Display results
                        for idx, row in results.iterrows():
                            with st.expander(
                                f"📝 {row['survey_date'].strftime('%Y-%m-%d')} | {row['school_name']} | "
                                f"{row['intervention_status']} | Relevance: {row['relevance_score']:.1f}"
                            ):
                                col1, col2 = st.columns([1, 1])
                                
                                with col1:
                                    st.markdown(f"**Teacher:** {row['teacher_id']}")
                                    st.markdown(f"**Region:** {row['region']}")
                                    st.markdown(f"**Time Period:** {row['time_period']}")
                                
                                with col2:
                                    st.markdown(f"**Experience:** {row['teaching_experience_years']} years")
                                    st.markdown(f"**Grade:** {row['grade_level']}")
                                    st.markdown(f"**Subject:** {row['subject_area']}")
                                
                                st.markdown("---")
                                
                                if pd.notna(row['f1_performance_factors']) and row['f1_performance_factors']:
                                    st.markdown("**🎯 Performance Factors:**")
                                    st.markdown(f"> {row['f1_performance_factors']}")
                                
                                if pd.notna(row['f2_effective_practice']) and row['f2_effective_practice']:
                                    st.markdown("**✨ Effective Practices:**")
                                    st.markdown(f"> {row['f2_effective_practice']}")
                                
                                if pd.notna(row['f3_challenges']) and row['f3_challenges']:
                                    st.markdown("**⚠️ Challenges:**")
                                    st.markdown(f"> {row['f3_challenges']}")
                                
                                if pd.notna(row['f4_additional_comments']) and row['f4_additional_comments']:
                                    st.markdown("**💬 Additional Comments:**")
                                    st.markdown(f"> {row['f4_additional_comments']}")
                    else:
                        st.warning("No results found. Try different search terms.")
            else:
                st.warning("Please enter search terms.")
    
    # TAB 2: THEME EXTRACTION
    with tab2:
        st.markdown("### 🎯 Theme Extraction")
        st.markdown("*Identify common themes and patterns across responses*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            theme_method = st.radio(
                "Analysis Method:",
                options=["Keyword Frequency", "AI Analysis (LLM)"],
                help="Keyword: Fast, simple patterns. AI: Deep analysis, slower."
            )
        
        with col2:
            theme_filters = st.multiselect(
                "Filter responses by:",
                options=['Treatment', 'Control'] + df['region'].unique().tolist(),
                default=[]
            )
        
        if st.button("🎯 Extract Themes", type="primary", use_container_width=True):
            with st.spinner("Analyzing themes..."):
                # Apply filters
                filtered_df = df.copy()
                if 'Treatment' in theme_filters:
                    filtered_df = filtered_df[filtered_df['intervention_status'] == 'Treatment']
                if 'Control' in theme_filters:
                    filtered_df = filtered_df[filtered_df['intervention_status'] == 'Control']
                
                region_filters = [f for f in theme_filters if f not in ['Treatment', 'Control']]
                if region_filters:
                    filtered_df = filtered_df[filtered_df['region'].isin(region_filters)]
                
                if theme_method == "Keyword Frequency":
                    themes = extract_themes_simple(filtered_df)
                    
                    st.markdown("#### 📊 Most Common Themes (by keyword frequency)")
                    
                    theme_df = pd.DataFrame(themes, columns=['Theme', 'Frequency'])
                    
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        import plotly.express as px
                        fig = px.bar(
                            theme_df.head(20),
                            x='Frequency',
                            y='Theme',
                            orientation='h',
                            title='Top 20 Themes',
                            labels={'Frequency': 'Count', 'Theme': ''}
                        )
                        fig.update_layout(height=600, yaxis={'categoryorder': 'total ascending'})
                        st.plotly_chart(fig, use_container_width=True)
                    
                    with col2:
                        st.dataframe(theme_df, hide_index=True, height=600)
                
                else:  # AI Analysis
                    themes = extract_themes_llm(filtered_df, model=selected_model)
                    
                    st.markdown("#### 🤖 AI-Generated Theme Analysis")
                    st.markdown(themes)
                    
                    # Download option
                    st.download_button(
                        label="📥 Download Theme Analysis",
                        data=themes,
                        file_name=f"theme_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
    
    # TAB 3: COMPARATIVE ANALYSIS
    with tab3:
        st.markdown("### ⚖️ Comparative Analysis")
        st.markdown("*Compare responses between different groups*")
        
        compare_by = st.selectbox(
            "Compare groups by:",
            options=['intervention_status', 'region', 'time_period'],
            format_func=lambda x: {
                'intervention_status': 'Treatment vs Control',
                'region': 'Regions',
                'time_period': 'Time Periods'
            }[x]
        )
        
        if st.button("⚖️ Run Comparison", type="primary", use_container_width=True):
            with st.spinner("Analyzing differences between groups..."):
                comparison = compare_groups(df, group_by=compare_by, model=selected_model)
                
                st.markdown("#### 🤖 Comparative Analysis Results")
                st.markdown(comparison)
                
                # Download option
                st.download_button(
                    label="📥 Download Comparison",
                    data=comparison,
                    file_name=f"comparative_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
    
    # TAB 4: TEMPORAL TRENDS
    with tab4:
        st.markdown("### ⏱️ Temporal Trends")
        st.markdown("*Analyze how teacher perspectives evolve over time*")
        
        temporal_filter = st.selectbox(
            "Focus on:",
            options=['All Responses', 'Treatment Only', 'Control Only'],
            key="temporal_filter"
        )
        
        if st.button("⏱️ Analyze Trends", type="primary", use_container_width=True):
            with st.spinner("Analyzing temporal patterns..."):
                # Apply filter
                filtered_df = df.copy()
                if temporal_filter == 'Treatment Only':
                    filtered_df = filtered_df[filtered_df['intervention_status'] == 'Treatment']
                elif temporal_filter == 'Control Only':
                    filtered_df = filtered_df[filtered_df['intervention_status'] == 'Control']
                
                trends = analyze_temporal_trends(filtered_df, model=selected_model)
                
                st.markdown("#### 🤖 Temporal Trend Analysis")
                st.markdown(trends)
                
                # Show response counts by time period
                st.markdown("#### 📊 Response Distribution Over Time")
                time_counts = filtered_df.groupby('time_period').size().reset_index(name='count')
                
                import plotly.express as px
                fig = px.bar(
                    time_counts,
                    x='time_period',
                    y='count',
                    title='Number of Responses by Time Period',
                    labels={'time_period': 'Time Period', 'count': 'Response Count'}
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Download option
                st.download_button(
                    label="📥 Download Temporal Analysis",
                    data=trends,
                    file_name=f"temporal_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )
    
    # TAB 5: SUMMARY GENERATION
    with tab5:
        st.markdown("### 📝 Summary Generation")
        st.markdown("*Generate comprehensive summaries of qualitative data*")
        
        col1, col2 = st.columns(2)
        
        with col1:
            summary_focus = st.text_input(
                "Focus area (optional):",
                placeholder="e.g., student engagement, intervention challenges",
                help="Leave blank for general summary"
            )
        
        with col2:
            summary_filter = st.selectbox(
                "Filter by:",
                options=['All Responses', 'Treatment Only', 'Control Only'],
                key="summary_filter"
            )
        
        if st.button("📝 Generate Summary", type="primary", use_container_width=True):
            with st.spinner("Generating comprehensive summary..."):
                # Apply filter
                filtered_df = df.copy()
                if summary_filter == 'Treatment Only':
                    filtered_df = filtered_df[filtered_df['intervention_status'] == 'Treatment']
                elif summary_filter == 'Control Only':
                    filtered_df = filtered_df[filtered_df['intervention_status'] == 'Control']
                
                summary = generate_summary(
                    filtered_df, 
                    focus=summary_focus if summary_focus else None,
                    model=selected_model
                )
                
                st.markdown("#### 🤖 Generated Summary")
                st.markdown(summary)
                
                # Statistics
                st.markdown("---")
                st.markdown("#### 📊 Summary Statistics")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Total Responses", len(filtered_df))
                with col2:
                    st.metric("Schools", filtered_df['school_id'].nunique())
                with col3:
                    st.metric("Teachers", filtered_df['teacher_id'].nunique())
                with col4:
                    response_rate = (filtered_df['f1_performance_factors'].notna().sum() / len(filtered_df) * 100)
                    st.metric("Response Rate", f"{response_rate:.0f}%")
                
                # Download option
                full_report = f"""CHATFRIEND QUALITATIVE SUMMARY
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Filter: {summary_filter}
Focus: {summary_focus if summary_focus else 'General'}

{summary}

---
STATISTICS:
- Total Responses: {len(filtered_df)}
- Schools: {filtered_df['school_id'].nunique()}
- Teachers: {filtered_df['teacher_id'].nunique()}
- Time Range: {filtered_df['survey_date'].min().strftime('%Y-%m-%d')} to {filtered_df['survey_date'].max().strftime('%Y-%m-%d')}
"""
                
                st.download_button(
                    label="📥 Download Full Report",
                    data=full_report,
                    file_name=f"summary_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                    mime="text/plain"
                )

if __name__ == "__main__":
    main()

