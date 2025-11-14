"""
====================================================================
STATISTICAL ANALYSIS PAGE
Mixed Effects Models - Interactive Analysis
====================================================================
"""

import streamlit as st
import sys
import os
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database_utils import get_database_connection, get_all_responses

st.set_page_config(page_title="Statistical Analysis", page_icon="📈", layout="wide")

# Custom CSS
st.markdown("""
    <style>
    .model-box {
        padding: 20px;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 10px 0;
    }
    .result-box {
        padding: 15px;
        border-radius: 5px;
        background-color: #e8f4f8;
        border-left: 5px solid #1f77b4;
        margin: 10px 0;
    }
    </style>
    """, unsafe_allow_html=True)

# ====================================================================
# MIXED EFFECTS MODEL FUNCTIONS
# ====================================================================

@st.cache_data(ttl=600)
def prepare_analysis_data(_engine):
    """Load and prepare data for mixed effects analysis."""
    
    df = get_all_responses(_engine)
    
    if df is None or df.empty:
        return None
    
    # Convert dates
    df['survey_date'] = pd.to_datetime(df['survey_date'])
    
    # Create time variable
    min_date = df['survey_date'].min()
    df['time_years'] = (df['survey_date'] - min_date).dt.days / 365.25
    df['time_months'] = (df['survey_date'] - min_date).dt.days / 30.44
    
    # Intervention binary
    df['intervention'] = (df['intervention_status'] == 'Treatment').astype(int)
    
    # Center continuous predictors
    df['teaching_exp_centered'] = df['teaching_experience_years'] - df['teaching_experience_years'].mean()
    df['class_size_centered'] = df['class_size'] - df['class_size'].mean()
    
    # Create composite score
    outcome_cols = [
        'b1_overall_performance', 'b2_problem_solving', 
        'b3_critical_thinking', 'b4_collaboration',
        'b5_communication', 'b6_engagement', 
        'b7_behavior', 'b8_persistence'
    ]
    df['composite_score'] = df[outcome_cols].mean(axis=1)
    
    return df

def calculate_icc(df, outcome='b1_overall_performance'):
    """Calculate Intraclass Correlation Coefficient."""
    
    # Calculate variance components using ANOVA approach
    # Between-school variance
    school_means = df.groupby('school_id')[outcome].mean()
    grand_mean = df[outcome].mean()
    between_school_var = ((school_means - grand_mean) ** 2).mean()
    
    # Within-school variance
    within_school_var = df.groupby('school_id')[outcome].var().mean()
    
    # ICC
    total_var = between_school_var + within_school_var
    icc = between_school_var / total_var if total_var > 0 else 0
    
    return {
        'icc': icc,
        'between_var': between_school_var,
        'within_var': within_school_var,
        'total_var': total_var
    }

def run_mixed_effects_model(df, outcome='b1_overall_performance', model_type='interaction'):
    """Run mixed effects model using statsmodels."""
    
    try:
        from statsmodels.regression.mixed_linear_model import MixedLM
        from statsmodels.formula.api import mixedlm
        
        # Prepare formula based on model type
        if model_type == 'null':
            formula = f"{outcome} ~ 1"
        elif model_type == 'main':
            formula = f"{outcome} ~ intervention + time_years"
        elif model_type == 'interaction':
            formula = f"{outcome} ~ intervention * time_years"
        elif model_type == 'full':
            formula = f"{outcome} ~ intervention * time_years + C(region) + teaching_exp_centered + class_size_centered"
        else:
            formula = f"{outcome} ~ intervention * time_years"
        
        # Fit model
        model = mixedlm(formula, data=df, groups=df["school_id"])
        result = model.fit(method='powell')
        
        return result
        
    except ImportError:
        st.error("⚠️ statsmodels package required. Install with: pip install statsmodels")
        return None
    except Exception as e:
        st.error(f"❌ Model fitting error: {str(e)}")
        return None

def interpret_coefficient(coef, se, p_value, coef_name):
    """Generate interpretation text for coefficient."""
    
    if p_value < 0.001:
        sig_text = "highly significant (p < 0.001)"
        emoji = "🌟🌟🌟"
    elif p_value < 0.01:
        sig_text = "very significant (p < 0.01)"
        emoji = "🌟🌟"
    elif p_value < 0.05:
        sig_text = "significant (p < 0.05)"
        emoji = "🌟"
    elif p_value < 0.10:
        sig_text = "marginally significant (p < 0.10)"
        emoji = "⭐"
    else:
        sig_text = "not significant"
        emoji = "○"
    
    direction = "positive" if coef > 0 else "negative"
    
    return f"{emoji} {coef_name}: {direction} effect ({coef:.3f} ± {se:.3f}), {sig_text}"

# ====================================================================
# MAIN PAGE
# ====================================================================

def main():
    st.title("📈 Statistical Analysis")
    
    # Add refresh button
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.markdown("### Mixed Effects Models for Longitudinal Data")
    with col3:
        if st.button("🔄 Refresh Data", help="Clear cache and reload latest data", key="refresh_stats", use_container_width=True):
            st.cache_data.clear()
            st.success("Cache cleared! Reloading...")
            st.rerun()
    
    st.markdown("""
    This page performs **hierarchical linear modeling** (mixed effects models) to analyze:
    - Intervention effectiveness
    - Changes over time
    - Regional differences
    - Accounting for nested data structure (teachers → schools → regions)
    """)
    
    # Load data
    engine = get_database_connection()
    
    with st.spinner("Loading data..."):
        df = prepare_analysis_data(engine)
    
    # Show data freshness info
    if df is not None and not df.empty:
        st.caption(f"📅 Data loaded: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Cached for 10 minutes")
    
    if df is None or df.empty:
        st.warning("⚠️ No data available for analysis. Please collect survey responses first.")
        st.info("Navigate to the **Survey Form** to start collecting data.")
        return
    
    # Check if adequate for analysis
    n_schools = df['school_id'].nunique()
    n_teachers = df['teacher_id'].nunique()
    n_timepoints = df['survey_date'].nunique()
    
    st.markdown("---")
    
    # Data summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Responses", len(df))
    with col2:
        st.metric("Schools", n_schools)
    with col3:
        st.metric("Teachers", n_teachers)
    with col4:
        st.metric("Time Points", n_timepoints)
    
    # Check minimum requirements
    if n_schools < 10:
        st.warning(f"⚠️ You have {n_schools} schools. Recommend at least 10-20 schools for reliable mixed effects models.")
    
    if n_timepoints < 2:
        st.warning(f"⚠️ You have {n_timepoints} time point(s). Need at least 2 time points for temporal analysis.")
    
    st.markdown("---")
    
    # Analysis tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Variance Partitioning",
        "🔬 Model Fitting",
        "📈 Results & Interpretation",
        "📋 Model Comparison"
    ])
    
    # ================================================================
    # TAB 1: VARIANCE PARTITIONING (ICC)
    # ================================================================
    with tab1:
        st.header("Intraclass Correlation (ICC)")
        
        st.markdown("""
        **ICC** shows how much variance is due to clustering (schools/regions).
        - **High ICC (>0.15)**: Strong clustering, mixed effects model essential
        - **Moderate ICC (0.05-0.15)**: Some clustering, mixed effects recommended
        - **Low ICC (<0.05)**: Weak clustering, but still use mixed effects for robustness
        """)
        
        # Select outcome
        outcome_options = {
            'b1_overall_performance': 'Overall Performance',
            'b2_problem_solving': 'Problem-Solving',
            'b3_critical_thinking': 'Critical Thinking',
            'b4_collaboration': 'Collaboration',
            'b5_communication': 'Communication',
            'b6_engagement': 'Engagement',
            'b7_behavior': 'Behavior',
            'b8_persistence': 'Persistence',
            'composite_score': 'Composite Score'
        }
        
        selected_outcome = st.selectbox(
            "Select Outcome Variable",
            options=list(outcome_options.keys()),
            format_func=lambda x: outcome_options[x],
            key='icc_outcome'
        )
        
        if st.button("Calculate ICC", key='calc_icc'):
            with st.spinner("Calculating..."):
                icc_results = calculate_icc(df, selected_outcome)
                
                st.markdown('<div class="result-box">', unsafe_allow_html=True)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("ICC", f"{icc_results['icc']:.3f}")
                    st.metric("Between-School Variance", f"{icc_results['between_var']:.3f}")
                    st.metric("Within-School Variance", f"{icc_results['within_var']:.3f}")
                
                with col2:
                    # Create pie chart
                    fig = go.Figure(data=[go.Pie(
                        labels=['Between Schools', 'Within Schools'],
                        values=[icc_results['between_var'], icc_results['within_var']],
                        hole=.3,
                        marker_colors=['#2ecc71', '#3498db']
                    )])
                    fig.update_layout(
                        title='Variance Decomposition',
                        height=300
                    )
                    st.plotly_chart(fig, use_container_width=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Interpretation
                icc = icc_results['icc']
                if icc > 0.15:
                    st.success(f"✅ **High ICC ({icc:.3f})**: Strong school-level clustering. Mixed effects model is essential!")
                elif icc > 0.05:
                    st.info(f"ℹ️ **Moderate ICC ({icc:.3f})**: Some school-level clustering. Mixed effects model recommended.")
                else:
                    st.warning(f"⚠️ **Low ICC ({icc:.3f})**: Weak clustering, but still use mixed effects for robustness.")
                
                # Show what ICC means
                st.markdown(f"""
                **Interpretation:**
                - **{icc*100:.1f}%** of variance in {outcome_options[selected_outcome]} is between schools
                - **{(1-icc)*100:.1f}%** of variance is within schools (between teachers)
                - This justifies accounting for school-level clustering in your model
                """)
    
    # ================================================================
    # TAB 2: MODEL FITTING
    # ================================================================
    with tab2:
        st.header("Fit Mixed Effects Models")
        
        st.markdown("""
        Select a model to fit based on your research questions:
        - **Main Effects**: Tests if intervention and time affect performance
        - **Interaction Model**: Tests if intervention effect changes over time (KEY MODEL)
        - **Full Model (MOST ROBUST)**: Includes teaching experience, class size, and regional differences
        
        📊 **Recommendation:** Use the **Full Model** for the most accurate and robust results, as it controls for teacher characteristics and regional variation.
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            model_type = st.selectbox(
                "Model Type",
                options=['main', 'interaction', 'full'],
                format_func=lambda x: {
                    'main': 'Main Effects Only',
                    'interaction': 'Intervention × Time Interaction',
                    'full': 'Full Model with Covariates'
                }[x]
            )
        
        with col2:
            outcome_for_model = st.selectbox(
                "Outcome Variable",
                options=list(outcome_options.keys()),
                format_func=lambda x: outcome_options[x],
                key='outcome_selector'
            )
        
        # Show model formula
        st.markdown("**Model Formula:**")
        if model_type == 'main':
            st.code(f"{outcome_options[outcome_for_model]} ~ Intervention + Time + (1 | School)", language='r')
            st.caption("Simple additive effects, no interaction")
        elif model_type == 'interaction':
            st.code(f"{outcome_options[outcome_for_model]} ~ Intervention × Time + (1 | School)", language='r')
            st.caption("Tests if intervention effect grows/shrinks over time")
        else:
            st.code(f"{outcome_options[outcome_for_model]} ~ Intervention × Time + Region + Teaching_Experience + Class_Size + (1 | School)", language='r')
            st.caption("🔬 Full model controls for teacher characteristics, class size, and regional differences")
        
        if st.button("🚀 Fit Model", type="primary"):
            with st.spinner("Fitting mixed effects model..."):
                result = run_mixed_effects_model(df, outcome_for_model, model_type)
                
                if result is not None:
                    # Store in session state
                    st.session_state['model_result'] = result
                    st.session_state['model_outcome'] = outcome_for_model
                    st.session_state['model_type'] = model_type
                    
                    st.success("✅ Model fitted successfully! View detailed interpretations in the 'Results & Interpretation' tab →")
                    
                    # Natural language summary (brief)
                    params = result.params
                    pvalues = result.pvalues
                    
                    st.markdown("### 📝 Quick Summary")
                    
                    # Key finding - Intervention x Time interaction
                    if 'intervention:time_years' in params.index:
                        if pvalues['intervention:time_years'] < 0.05:
                            direction = "increases" if params['intervention:time_years'] > 0 else "decreases"
                            effectiveness = "more" if params['intervention:time_years'] > 0 else "less"
                            st.markdown(f"""
                            <div class="result-box" style="border-left-color: #2ecc71; background-color: #eafaf1;">
                            <strong>🌟 Key Finding:</strong><br>
                            The intervention effect <strong>{direction}</strong> over time, meaning it becomes <strong>{effectiveness} effective</strong> 
                            the longer students participate in the program.
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.markdown("""
                            <div class="result-box">
                            <strong>📊 Key Finding:</strong><br>
                            The intervention effect remains consistent over time - it doesn't significantly increase or decrease.
                            </div>
                            """, unsafe_allow_html=True)
                    
                    st.info("👉 Go to the **'Results & Interpretation'** tab for detailed natural language explanations")
                    
                    # Technical details in expander (for experts)
                    with st.expander("📊 View Technical Details (Coefficients, P-values, Model Fit)", expanded=False):
                        st.markdown("### Statistical Output")
                        
                        # Extract coefficients
                        summary_df = pd.DataFrame({
                            'Coefficient': result.params.index,
                            'Estimate': result.params.values,
                            'Std Error': result.bse.values,
                            'z-value': result.tvalues.values,
                            'p-value': result.pvalues.values
                        })
                        
                        # Format p-values
                        summary_df['Significance'] = summary_df['p-value'].apply(
                            lambda p: '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
                        )
                        
                        st.dataframe(
                            summary_df.style.format({
                                'Estimate': '{:.4f}',
                                'Std Error': '{:.4f}',
                                'z-value': '{:.3f}',
                                'p-value': '{:.4f}'
                            }),
                            hide_index=True,
                            use_container_width=True
                        )
                        
                        st.caption("Significance codes: *** p<0.001, ** p<0.01, * p<0.05")
                        
                        # Random effects
                        st.markdown("### Random Effects")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("School-level Variance", f"{result.cov_re.iloc[0, 0]:.4f}")
                        with col2:
                            st.metric("Residual Variance", f"{result.scale:.4f}")
                        
                        # Log likelihood
                        st.markdown("### Model Fit Statistics")
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Log-Likelihood", f"{result.llf:.2f}")
                        with col2:
                            st.metric("AIC", f"{result.aic:.2f}")
                        
                        # Download button for technical results
                        csv_data = summary_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            label="📥 Download Statistical Results (CSV)",
                            data=csv_data,
                            file_name=f"statistical_results_{outcome_for_model}_{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            help="Download the detailed statistical output including coefficients, standard errors, and p-values"
                        )
    
    # ================================================================
    # TAB 3: RESULTS & INTERPRETATION
    # ================================================================
    with tab3:
        st.header("Results & Interpretation")
        
        if 'model_result' not in st.session_state:
            st.info("👈 Fit a model in the 'Model Fitting' tab first!")
        else:
            result = st.session_state['model_result']
            outcome = st.session_state['model_outcome']
            model_type = st.session_state['model_type']
            
            st.markdown(f"### Results for: **{outcome_options[outcome]}**")
            st.markdown(f"**Model Type:** {model_type.replace('_', ' ').title()}")
            
            # Key findings
            st.markdown("### 🔍 Key Findings")
            
            params = result.params
            pvalues = result.pvalues
            se = result.bse
            
            # Interpret each coefficient
            interpretations = []
            
            if 'intervention' in params.index:
                interp = interpret_coefficient(
                    params['intervention'],
                    se['intervention'],
                    pvalues['intervention'],
                    "**Intervention Effect**"
                )
                interpretations.append(interp)
                
                if pvalues['intervention'] < 0.05:
                    direction = "higher" if params['intervention'] > 0 else "lower"
                    st.markdown(f"""
                    <div class="result-box">
                    <strong>Intervention Impact:</strong><br>
                    Students in intervention schools score <strong>{abs(params['intervention']):.3f} points {direction}</strong> 
                    on {outcome_options[outcome]} compared to control schools (p = {pvalues['intervention']:.4f})
                    </div>
                    """, unsafe_allow_html=True)
            
            if 'time_years' in params.index:
                interp = interpret_coefficient(
                    params['time_years'],
                    se['time_years'],
                    pvalues['time_years'],
                    "**Time Trend**"
                )
                interpretations.append(interp)
                
                if pvalues['time_years'] < 0.05:
                    direction = "increases" if params['time_years'] > 0 else "decreases"
                    st.markdown(f"""
                    <div class="result-box">
                    <strong>Temporal Trend:</strong><br>
                    Performance {direction} by <strong>{abs(params['time_years']):.3f} points per year</strong> 
                    (p = {pvalues['time_years']:.4f})
                    </div>
                    """, unsafe_allow_html=True)
            
            if 'intervention:time_years' in params.index:
                interp = interpret_coefficient(
                    params['intervention:time_years'],
                    se['intervention:time_years'],
                    pvalues['intervention:time_years'],
                    "**Intervention × Time Interaction**"
                )
                interpretations.append(interp)
                
                st.markdown("### 🌟 CRITICAL FINDING: Intervention × Time Interaction")
                
                if pvalues['intervention:time_years'] < 0.05:
                    direction = "increases" if params['intervention:time_years'] > 0 else "decreases"
                    st.markdown(f"""
                    <div class="result-box" style="border-left-color: #e74c3c; background-color: #fdecea;">
                    <strong>⭐ Significant Interaction!</strong><br>
                    The intervention effect <strong>{direction} by {abs(params['intervention:time_years']):.3f} points per year</strong> 
                    (p = {pvalues['intervention:time_years']:.4f})<br><br>
                    <strong>Interpretation:</strong> The intervention becomes {"more" if params['intervention:time_years'] > 0 else "less"} 
                    effective over time. This suggests that the intervention has a <strong>cumulative effect</strong>.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="result-box">
                    <strong>No Significant Interaction</strong> (p = {pvalues['intervention:time_years']:.4f})<br>
                    The intervention effect does not significantly change over time.
                    The intervention has a consistent effect regardless of duration.
                    </div>
                    """, unsafe_allow_html=True)
            
            # Interpret covariates (Full model only)
            if model_type == 'full':
                st.markdown("### 🎓 Control Variables (Covariates)")
                
                # Teaching experience
                if 'teaching_exp_centered' in params.index:
                    if pvalues['teaching_exp_centered'] < 0.05:
                        direction = "higher" if params['teaching_exp_centered'] > 0 else "lower"
                        st.markdown(f"""
                        <div class="result-box">
                        <strong>📚 Teaching Experience:</strong><br>
                        Each additional year of teaching experience is associated with 
                        <strong>{abs(params['teaching_exp_centered']):.3f} points {direction}</strong> performance 
                        (p = {pvalues['teaching_exp_centered']:.4f})
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info(f"📚 **Teaching Experience:** Not significantly associated with performance (p = {pvalues['teaching_exp_centered']:.3f})")
                
                # Class size
                if 'class_size_centered' in params.index:
                    if pvalues['class_size_centered'] < 0.05:
                        direction = "higher" if params['class_size_centered'] > 0 else "lower"
                        st.markdown(f"""
                        <div class="result-box">
                        <strong>👥 Class Size:</strong><br>
                        Each additional student in class is associated with 
                        <strong>{abs(params['class_size_centered']):.3f} points {direction}</strong> performance 
                        (p = {pvalues['class_size_centered']:.4f})
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        st.info(f"👥 **Class Size:** Not significantly associated with performance (p = {pvalues['class_size_centered']:.3f})")
                
                # Regional effects
                region_params = [p for p in params.index if 'C(region)' in p]
                if region_params:
                    st.markdown("**🌍 Regional Differences:**")
                    region_significant = False
                    for region_param in region_params:
                        if pvalues[region_param] < 0.05:
                            region_name = region_param.replace('C(region)[T.', '').replace(']', '')
                            direction = "higher" if params[region_param] > 0 else "lower"
                            st.markdown(f"- **{region_name}:** {abs(params[region_param]):.3f} points {direction} than baseline region (p = {pvalues[region_param]:.3f})")
                            region_significant = True
                    
                    if not region_significant:
                        st.info("No significant regional differences detected")
            
            # Show all interpretations
            st.markdown("### 📊 All Coefficients")
            for interp in interpretations:
                st.markdown(interp)
            
            # Download natural language summary
            st.markdown("---")
            st.markdown("### 📥 Export Results")
            
            # Create natural language summary for download
            summary_text = f"""
STATISTICAL ANALYSIS RESULTS - NATURAL LANGUAGE SUMMARY
=========================================================

Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Outcome Variable: {outcome_options[outcome]}
Model Type: {model_type.replace('_', ' ').title()}

=========================================================
KEY FINDINGS
=========================================================

"""
            
            # Add intervention effect
            if 'intervention' in params.index:
                if pvalues['intervention'] < 0.05:
                    direction = "higher" if params['intervention'] > 0 else "lower"
                    summary_text += f"✓ INTERVENTION EFFECT (at baseline):\n"
                    summary_text += f"  Students in intervention schools score {abs(params['intervention']):.3f} points {direction}\n"
                    summary_text += f"  than control schools (p = {pvalues['intervention']:.4f}).\n"
                    summary_text += f"  This effect is statistically significant.\n\n"
                else:
                    summary_text += f"✓ INTERVENTION EFFECT (at baseline):\n"
                    summary_text += f"  No significant difference at baseline (p = {pvalues['intervention']:.4f}).\n\n"
            
            # Add time effect
            if 'time_years' in params.index:
                if pvalues['time_years'] < 0.05:
                    direction = "increases" if params['time_years'] > 0 else "decreases"
                    summary_text += f"✓ TEMPORAL TREND:\n"
                    summary_text += f"  Performance {direction} by {abs(params['time_years']):.3f} points per year\n"
                    summary_text += f"  (p = {pvalues['time_years']:.4f}).\n\n"
                else:
                    summary_text += f"✓ TEMPORAL TREND:\n"
                    summary_text += f"  No significant natural time trend (p = {pvalues['time_years']:.4f}).\n\n"
            
            # Add interaction effect (most important!)
            if 'intervention:time_years' in params.index:
                summary_text += f"⭐ INTERVENTION × TIME INTERACTION (CRITICAL):\n"
                if pvalues['intervention:time_years'] < 0.05:
                    direction = "increases" if params['intervention:time_years'] > 0 else "decreases"
                    effectiveness = "MORE" if params['intervention:time_years'] > 0 else "LESS"
                    summary_text += f"  The intervention effect {direction} by {abs(params['intervention:time_years']):.3f} points per year\n"
                    summary_text += f"  (p = {pvalues['intervention:time_years']:.4f}).\n"
                    summary_text += f"  \n"
                    summary_text += f"  INTERPRETATION: The intervention becomes {effectiveness} effective over time.\n"
                    summary_text += f"  This suggests a CUMULATIVE BENEFIT - the longer students participate,\n"
                    summary_text += f"  the {'greater' if params['intervention:time_years'] > 0 else 'smaller'} the impact on their performance.\n\n"
                else:
                    summary_text += f"  The intervention effect does NOT significantly change over time\n"
                    summary_text += f"  (p = {pvalues['intervention:time_years']:.4f}).\n"
                    summary_text += f"  The intervention has a consistent effect regardless of duration.\n\n"
            
            # Add covariates (Full model only)
            if model_type == 'full':
                summary_text += f"=========================================================\n"
                summary_text += f"CONTROL VARIABLES (COVARIATES)\n"
                summary_text += f"=========================================================\n\n"
                
                if 'teaching_exp_centered' in params.index:
                    if pvalues['teaching_exp_centered'] < 0.05:
                        direction = "higher" if params['teaching_exp_centered'] > 0 else "lower"
                        summary_text += f"✓ TEACHING EXPERIENCE:\n"
                        summary_text += f"  Each additional year of experience is associated with\n"
                        summary_text += f"  {abs(params['teaching_exp_centered']):.3f} points {direction} performance (p = {pvalues['teaching_exp_centered']:.4f}).\n\n"
                    else:
                        summary_text += f"✓ TEACHING EXPERIENCE:\n"
                        summary_text += f"  Not significantly associated with performance (p = {pvalues['teaching_exp_centered']:.3f}).\n\n"
                
                if 'class_size_centered' in params.index:
                    if pvalues['class_size_centered'] < 0.05:
                        direction = "higher" if params['class_size_centered'] > 0 else "lower"
                        summary_text += f"✓ CLASS SIZE:\n"
                        summary_text += f"  Each additional student is associated with\n"
                        summary_text += f"  {abs(params['class_size_centered']):.3f} points {direction} performance (p = {pvalues['class_size_centered']:.4f}).\n\n"
                    else:
                        summary_text += f"✓ CLASS SIZE:\n"
                        summary_text += f"  Not significantly associated with performance (p = {pvalues['class_size_centered']:.3f}).\n\n"
                
                region_params = [p for p in params.index if 'C(region)' in p]
                if region_params:
                    summary_text += f"✓ REGIONAL DIFFERENCES:\n"
                    for region_param in region_params:
                        region_name = region_param.replace('C(region)[T.', '').replace(']', '')
                        if pvalues[region_param] < 0.05:
                            direction = "higher" if params[region_param] > 0 else "lower"
                            summary_text += f"  {region_name}: {abs(params[region_param]):.3f} points {direction} than baseline (p = {pvalues[region_param]:.3f})\n"
                        else:
                            summary_text += f"  {region_name}: No significant difference (p = {pvalues[region_param]:.3f})\n"
            
            summary_text += f"\n=========================================================\n"
            summary_text += f"CONCLUSIONS\n"
            summary_text += f"=========================================================\n\n"
            
            # Add conclusion
            if 'intervention:time_years' in params.index and pvalues['intervention:time_years'] < 0.05:
                if params['intervention:time_years'] > 0:
                    summary_text += "The intervention shows POSITIVE results. The effect grows stronger over time,\n"
                    summary_text += "indicating that longer participation leads to better outcomes. This suggests\n"
                    summary_text += "the intervention should be continued and potentially expanded.\n\n"
                else:
                    summary_text += "The intervention shows DECLINING effectiveness over time. This suggests\n"
                    summary_text += "the intervention may lose impact with longer duration, potentially due to\n"
                    summary_text += "diminishing novelty or other factors. Consider revising the program.\n\n"
            else:
                summary_text += "The intervention effect is consistent over time (no significant interaction).\n"
                summary_text += "The program maintains stable effectiveness regardless of duration.\n\n"
            
            summary_text += f"Report generated by Mixed Effects Model Analysis\n"
            summary_text += f"Model: {model_type.replace('_', ' ').title()}\n"
            
            # Download button
            st.download_button(
                label="📥 Download Full Natural Language Report (TXT)",
                data=summary_text.encode('utf-8'),
                file_name=f"analysis_report_{outcome}_{model_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain",
                help="Download a detailed natural language summary of all results"
            )
            
            # Visualize predicted trajectories
            st.markdown("### 📈 Predicted Trajectories")
            
            # Create prediction data
            time_range = np.linspace(df['time_years'].min(), df['time_years'].max(), 50)
            
            # Predict for treatment and control
            pred_data = []
            for intervention in [0, 1]:
                for time in time_range:
                    pred_data.append({
                        'time_years': time,
                        'intervention': intervention,
                        'intervention_status': 'Treatment' if intervention == 1 else 'Control'
                    })
            
            pred_df = pd.DataFrame(pred_data)
            
            # Add other variables (set to mean/mode)
            if 'teaching_exp_centered' in df.columns:
                pred_df['teaching_exp_centered'] = 0  # Mean
            if 'class_size_centered' in df.columns:
                pred_df['class_size_centered'] = 0  # Mean
            if 'region' in df.columns:
                pred_df['region'] = df['region'].mode()[0]  # Most common
            
            try:
                # Get predictions
                pred_df['predicted'] = result.predict(pred_df)
                
                # Plot
                fig = px.line(
                    pred_df,
                    x='time_years',
                    y='predicted',
                    color='intervention_status',
                    title=f'Predicted {outcome_options[outcome]} Over Time',
                    labels={'time_years': 'Time (Years)', 'predicted': 'Predicted Performance'},
                    color_discrete_map={'Treatment': '#2ecc71', 'Control': '#e74c3c'}
                )
                fig.update_layout(height=500, hovermode='x unified')
                st.plotly_chart(fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Could not generate predictions: {str(e)}")
    
    # ================================================================
    # TAB 4: MODEL COMPARISON
    # ================================================================
    with tab4:
        st.header("Compare Multiple Models")
        
        st.markdown("""
        Fit models for **all 8 performance outcomes** and compare effect sizes.
        """)
        
        if st.button("🔬 Run Analysis for All Outcomes", type="primary"):
            with st.spinner("Fitting models for all outcomes... This may take a minute..."):
                
                results_list = []
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for i, (outcome_key, outcome_name) in enumerate(outcome_options.items()):
                    if outcome_key == 'composite_score':
                        continue  # Skip composite for individual analysis
                    
                    status_text.text(f"Fitting model for {outcome_name}...")
                    
                    try:
                        result = run_mixed_effects_model(df, outcome_key, 'interaction')
                        
                        if result is not None:
                            results_list.append({
                                'Outcome': outcome_name,
                                'Intervention': result.params.get('intervention', np.nan),
                                'Intervention_p': result.pvalues.get('intervention', np.nan),
                                'Time': result.params.get('time_years', np.nan),
                                'Time_p': result.pvalues.get('time_years', np.nan),
                                'Interaction': result.params.get('intervention:time_years', np.nan),
                                'Interaction_p': result.pvalues.get('intervention:time_years', np.nan)
                            })
                    except:
                        pass
                    
                    progress_bar.progress((i + 1) / 8)
                
                status_text.text("Analysis complete!")
                progress_bar.empty()
                
                # Create results table
                results_df = pd.DataFrame(results_list)
                
                st.markdown("### Effect Sizes Across All Outcomes")
                
                # Format display
                display_df = results_df.copy()
                for col in ['Intervention', 'Time', 'Interaction']:
                    if col in display_df.columns:
                        display_df[f'{col}_sig'] = display_df[f'{col}_p'].apply(
                            lambda p: '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else ''
                        )
                        display_df[col] = display_df[col].apply(lambda x: f"{x:.3f}")
                
                st.dataframe(display_df, hide_index=True, use_container_width=True)
                
                # Heatmap
                st.markdown("### Effect Size Heatmap")
                
                heatmap_data = results_df[['Outcome', 'Intervention', 'Time', 'Interaction']].set_index('Outcome')
                
                fig = px.imshow(
                    heatmap_data.T,
                    labels=dict(x="Outcome", y="Effect Type", color="Effect Size"),
                    x=heatmap_data.index,
                    y=['Intervention', 'Time', 'Interaction'],
                    color_continuous_scale='RdBu_r',
                    color_continuous_midpoint=0,
                    aspect="auto",
                    title="Effect Sizes Across All Outcomes"
                )
                fig.update_layout(height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # Download results
                csv = results_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    label="📥 Download Results Table",
                    data=csv,
                    file_name="mixed_effects_results.csv",
                    mime="text/csv"
                )

if __name__ == "__main__":
    main()


