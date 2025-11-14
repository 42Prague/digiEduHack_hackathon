"""
====================================================================
CHATFRIEND - AI-POWERED QUALITATIVE ANALYSIS
Semantic Search, Theme Extraction, and Insights using Cloud LLM
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
from llm_service import check_llm_available, call_llm_simple, call_llm_chat, get_service_status

st.set_page_config(page_title="ChatFriend AI", page_icon="🤖", layout="wide")

# ====================================================================
# LLM SERVICE CONFIGURATION
# ====================================================================

# The actual LLM functions are now imported from llm_service.py
# This provides a unified interface to the Hugging Face API

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

def extract_themes_llm(df):
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
    
    return call_llm_simple(prompt, temperature=0.3)

# ====================================================================
# COMPARATIVE ANALYSIS
# ====================================================================

def compare_groups(df, group_by='intervention_status'):
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
    
    return call_llm_simple(prompt, temperature=0.4)

# ====================================================================
# TEMPORAL TRENDS
# ====================================================================

def analyze_temporal_trends(df):
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
    
    return call_llm_simple(prompt, temperature=0.4)

# ====================================================================
# SUMMARY GENERATION
# ====================================================================

def generate_summary(df, focus=None):
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
    
    return call_llm_simple(prompt, temperature=0.5)

# ====================================================================
# MAIN PAGE
# ====================================================================

def main():
    # Custom CSS for beautiful UI
    st.markdown("""
    <style>
    /* Main title styling */
    .main-title {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: 800;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    
    .subtitle {
        text-align: center;
        color: #6c757d;
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }
    
    /* Status badge */
    .status-badge {
        display: inline-block;
        padding: 0.5rem 1rem;
        border-radius: 20px;
        font-size: 0.9rem;
        font-weight: 600;
        margin: 0.5rem;
    }
    
    .status-connected {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    /* Chat container styling */
    .chat-container {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        border-radius: 15px;
        padding: 2rem;
        margin: 1rem 0;
    }
    
    /* Example questions */
    .stButton button {
        border-radius: 10px;
        border: 2px solid #667eea;
        transition: all 0.3s ease;
    }
    
    .stButton button:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    
    /* Chat input */
    .stChatInput {
        border-radius: 15px;
    }
    
    /* Metrics */
    [data-testid="stMetricValue"] {
        font-size: 2rem;
        color: #667eea;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Beautiful header
    st.markdown('<h1 class="main-title">💬 ChatFriend AI</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Your intelligent assistant for analyzing teacher survey responses</p>', unsafe_allow_html=True)
    
    # Check LLM service status
    llm_available = check_llm_available()
    service_status = get_service_status()
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if llm_available:
            st.markdown(
                f'<div style="text-align: center;"><span class="status-badge status-connected">✅ Connected to {service_status["provider"]}</span></div>',
                unsafe_allow_html=True
            )
        else:
            st.error(f"""
            ❌ **LLM Service Unavailable**
            
            Please ensure the LLM service is running with a valid HF_API_KEY.
            """)
            return
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Load data
    engine = get_database_connection()
    
    with st.spinner("Loading qualitative data..."):
        df = load_qualitative_data(engine)
    
    if df is None or df.empty:
        st.warning("⚠️ No qualitative data available. Please submit responses through the Survey Form first.")
        return
    
    # Show data statistics with nice formatting
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Responses", len(df), help="Number of teacher survey responses")
    with col2:
        st.metric("Schools", df['school_id'].nunique(), help="Unique schools in dataset")
    with col3:
        st.metric("Teachers", df['teacher_id'].nunique(), help="Unique teachers surveyed")
    with col4:
        st.metric("Regions", df['region'].nunique(), help="Geographic regions covered")
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # ====================================================================
    # CHAT ASSISTANT
    # ====================================================================
    
    # Initialize chat history in session state
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []
    
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = []
    
    # No filters - analyze all data
    chat_filters = []
        
    # Display chat messages
    st.markdown("### 💬 Conversation")
    
    if st.session_state.chat_messages:
        for msg in st.session_state.chat_messages:
            with st.chat_message(msg["role"], avatar="🧑‍🏫" if msg["role"] == "user" else "🤖"):
                st.markdown(msg["content"])
    else:
        st.info("👋 **Welcome!** Ask me anything about the teacher survey data. I'll analyze the responses and provide insights.")
        
    # Chat input
    user_question = st.chat_input("💭 Ask a question about the teacher survey data...", key="chat_input")
        
    if user_question:
        # Add user message to display
        st.session_state.chat_messages.append({"role": "user", "content": user_question})
        
        # Filter data based on selections
        filtered_df = df.copy()
        if 'Treatment' in chat_filters:
            filtered_df = filtered_df[filtered_df['intervention_status'] == 'Treatment']
        if 'Control' in chat_filters:
            filtered_df = filtered_df[filtered_df['intervention_status'] == 'Control']
        
        region_filters = [f for f in chat_filters if f not in ['Treatment', 'Control']]
        if region_filters:
            filtered_df = filtered_df[filtered_df['region'].isin(region_filters)]
        
        # Prepare context from data - filter out empty responses first
        non_empty_df = filtered_df[filtered_df['all_text'].str.len() > 50].copy()
        
        if len(non_empty_df) == 0:
            st.warning("No qualitative responses found with the selected filters.")
            st.stop()
        
        sample_size = min(50, len(non_empty_df))
        sampled_responses = non_empty_df.sample(sample_size)
        
        # Create context with more space and better formatting
        context_parts = []
        for i, (idx, row) in enumerate(sampled_responses.iterrows(), 1):
            text = row['all_text'][:600].strip()  # Increased from 500 to 600 chars
            if text:
                context_parts.append(f"[Response {i} - {row['intervention_status']} - {row['region']}]\n{text}")
        
        # Increased context limit to 15000 characters
        context_text = '\n\n---\n\n'.join(context_parts)[:15000]
        
        # Build system prompt with context
        system_prompt = f"""You are an AI assistant analyzing teacher survey data about student performance and educational interventions.

CONTEXT - Teacher Survey Responses:
{context_text}

Your role:
- Answer questions based on the survey data provided above
- Be specific and cite patterns you see in the responses
- If you don't see relevant information in the data, say so
- Provide actionable insights when possible
- Keep responses concise but informative
- Use bullet points for clarity when appropriate

Dataset info:
- Total responses in database: {len(filtered_df)}
- Non-empty responses: {len(non_empty_df)}
- Sample size provided: {len(context_parts)} responses
- Filters applied: {', '.join(chat_filters) if chat_filters else 'None (analyzing all data)'}
"""
        
        # Call LLM with chat history
        with st.spinner("🤔 Analyzing responses..."):
            assistant_response = call_llm_chat(
                message=user_question,
                history=st.session_state.chat_history,
                system_prompt=system_prompt
            )
        
        # Add to chat history for continuity
        st.session_state.chat_history.append({"role": "user", "content": user_question})
        st.session_state.chat_history.append({"role": "assistant", "content": assistant_response})
        
        # Add assistant message to display
        st.session_state.chat_messages.append({"role": "assistant", "content": assistant_response})
        
        # Rerun to show new messages
        st.rerun()
        

if __name__ == "__main__":
    main()
