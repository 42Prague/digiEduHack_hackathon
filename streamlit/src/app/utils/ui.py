"""
UI utilities and custom styling for the dashboard
"""

import streamlit as st


def apply_custom_css():
    """Apply custom CSS styling with modern education-focused design"""
    # Inject CSS using st.markdown with unsafe_allow_html=True
    # The CSS should be applied as styles, NOT displayed as text
    
    # Load Google Fonts
    st.markdown(
        """<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Poppins:wght@500;600&display=swap" rel="stylesheet">""",
        unsafe_allow_html=True
    )
    
    # Inject all CSS rules
    st.markdown("""<style>
    /* Ensure scrolling works properly */
    html, body {
        overflow-y: auto !important;
        overflow-x: hidden !important;
        height: auto !important;
    }
    
    .main {
        overflow-y: auto !important;
        overflow-x: hidden !important;
        height: auto !important;
        background: linear-gradient(135deg, #f8fbff 0%, #eef2f7 100%);
    }
    
    [data-testid="stAppViewContainer"] {
        overflow-y: auto !important;
        overflow-x: hidden !important;
        height: auto !important;
    }
    
    [data-testid="stAppViewContainer"] > div {
        overflow-y: auto !important;
        overflow-x: hidden !important;
        height: auto !important;
    }
    
    /* Global Typography */
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container spacing */
    .main .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        overflow-y: visible !important;
        height: auto !important;
    }
    
    /* Headings with Poppins */
    h1, h2, h3 {
        font-family: 'Poppins', sans-serif;
        font-weight: 600;
        color: #2c3e50;
    }
    
    h1 {
        border-bottom: 3px solid #4A90E2;
        padding-bottom: 0.5rem;
    }
    
    h2 {
        margin-top: 1.5rem;
        color: #2c3e50;
    }
    
    h3 {
        color: #34495e;
    }
    
    /* KPI Cards - Glassmorphism Style */
    .kpi-card {
        background: rgba(255, 255, 255, 0.75);
        backdrop-filter: blur(8px);
        border-radius: 15px;
        padding: 1rem 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    
    .kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 18px rgba(0,0,0,0.1);
        background: rgba(255, 255, 255, 0.85);
    }
    
    /* KPI Metrics styling */
    [data-testid="stMetricValue"] {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2c3e50;
        font-family: 'Poppins', sans-serif;
    }
    
    [data-testid="stMetricLabel"] {
        font-size: 1rem;
        color: #7f8c8d;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
    }
    
    [data-testid="stMetricDelta"] {
        font-size: 0.95rem;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
    }
    
    /* Chart area styling */
    [data-testid="stPlotlyChart"] {
        border-radius: 12px;
        background: white;
        padding: 1rem;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        border: 1px solid rgba(0,0,0,0.05);
    }
    
    /* Sidebar styling - Glassmorphism (excluding chat area) */
    [data-testid="stSidebar"] {
        background: linear-gradient(135deg, #f8fbff 0%, #eef2f7 100%);
        backdrop-filter: blur(12px);
    }
    
    [data-testid="stSidebar"] .css-1d391kg {
        padding-top: 2rem;
    }
    
    /* Exclude chat-related sidebar elements from styling */
    [data-testid="stSidebar"] .stAlert {
        background: inherit !important;
        backdrop-filter: none !important;
        border-radius: 0 !important;
        box-shadow: none !important;
    }
    
    /* Tabs styling - Clean and modern */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: transparent;
    }
    
    .stTabs [data-baseweb="tab"] {
        padding: 12px 24px;
        border-radius: 8px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: rgba(102, 126, 234, 0.1);
    }
    
    /* Button improvements - Soft education colors */
    button[kind="primary"] {
        background: linear-gradient(135deg, #4A90E2 0%, #357ABD 100%);
        border: none;
        border-radius: 8px;
        font-weight: 600;
        font-family: 'Inter', sans-serif;
        transition: all 0.3s ease;
    }
    
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #357ABD 0%, #4A90E2 100%);
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.3);
    }
    
    /* Secondary buttons */
    button[kind="secondary"] {
        border-radius: 8px;
        font-family: 'Inter', sans-serif;
    }
    
    /* Info/Warning/Success boxes - Soft colors (excluding sidebar chat) */
    .stAlert:not([data-testid="stSidebar"] .stAlert) {
        border-radius: 12px;
        border-left: 4px solid;
        font-family: 'Inter', sans-serif;
    }
    
    /* Reset chat alert boxes in sidebar */
    [data-testid="stSidebar"] .stAlert {
        border-radius: 0 !important;
        border-left: none !important;
    }
    
    /* Dataframe styling */
    [data-testid="stDataFrame"] {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Code blocks */
    .stCodeBlock {
        border-radius: 10px;
        border: 1px solid rgba(0,0,0,0.1);
        font-family: 'Monaco', 'Courier New', monospace;
    }
    
    /* Footer styling */
    .footer {
        margin-top: 3rem;
        padding-top: 2rem;
        border-top: 2px solid rgba(0,0,0,0.05);
        font-family: 'Inter', sans-serif;
    }
    
    /* Custom info boxes - Education theme */
    .info-box {
        background: rgba(79, 172, 254, 0.1);
        padding: 1.2rem;
        border-radius: 12px;
        border-left: 4px solid #4FACFE;
        margin: 1rem 0;
        font-family: 'Inter', sans-serif;
    }
    
    .success-box {
        background: rgba(46, 213, 115, 0.1);
        padding: 1.2rem;
        border-radius: 12px;
        border-left: 4px solid #2ED573;
        margin: 1rem 0;
        font-family: 'Inter', sans-serif;
    }
    
    /* Loading spinner */
    .stSpinner > div {
        border-top-color: #4A90E2;
    }
    
    /* Empty state styling */
    .empty-state {
        text-align: center;
        padding: 3rem;
        color: #95a5a6;
        font-family: 'Inter', sans-serif;
    }
    
    /* Improved spacing */
    .stMarkdown {
        margin-bottom: 1rem;
    }
    .stMainBlockContainer {
        max-width: 100% !important;
    }
    
    .st-emotion-cache-1w723zb {
        max-width: 100% !important;
    }
    
    /* Sidebar buttons - use default Streamlit styling (chat excluded) */
    [data-testid="stSidebar"] button {
        background: inherit !important;
        border-radius: 4px !important;
        font-family: inherit !important;
        width: auto !important;
    }
    
    /* Exclude chat message containers from custom styling */
    [data-testid="stChatMessage"],
    [data-testid="stChatInput"] {
        font-family: inherit !important;
    }
    
    /* Reset chat headers in sidebar - use default styling */
    [data-testid="stSidebar"] h2 {
        background: none !important;
        -webkit-background-clip: unset !important;
        -webkit-text-fill-color: unset !important;
        background-clip: unset !important;
        color: inherit !important;
        margin-top: 0 !important;
    }
    
    /* Metric containers - Subtle elevation */
    [data-testid="stMetricContainer"] {
        background: rgba(255, 255, 255, 0.6);
        padding: 1rem;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
        transition: all 0.3s ease;
    }
    
    [data-testid="stMetricContainer"]:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.08);
        transform: translateY(-2px);
    }
    
    /* Chart title styling */
    .js-plotly-plot .plotly .gtitle {
        font-family: 'Poppins', sans-serif !important;
        font-weight: 600 !important;
        color: #2c3e50 !important;
    }
    </style>""", unsafe_allow_html=True)


def render_metric_with_icon(icon: str, label: str, value: str, delta: str = None, delta_color: str = "normal"):
    """Render a metric with icon in a glassmorphism-styled container"""
    st.markdown('<div class="kpi-card">', unsafe_allow_html=True)
    col1, col2 = st.columns([1, 5])
    with col1:
        st.markdown(f"<div style='font-size: 2.5rem; text-align: center; line-height: 1;'>{icon}</div>", unsafe_allow_html=True)
    with col2:
        if delta:
            st.metric(
                label=label,
                value=value,
                delta=delta,
                delta_color=delta_color
            )
        else:
            st.metric(
                label=label,
                value=value
            )
    st.markdown('</div>', unsafe_allow_html=True)


def create_info_card(title: str, content: str, icon: str = "ℹ️"):
    """Create a styled info card"""
    st.markdown(f"""
    <div class="info-box">
        <strong>{icon} {title}</strong><br>
        {content}
    </div>
    """, unsafe_allow_html=True)


def create_success_card(title: str, content: str):
    """Create a styled success card"""
    st.markdown(f"""
    <div class="success-box">
        <strong>✅ {title}</strong><br>
        {content}
    </div>
    """, unsafe_allow_html=True)


def create_section_header(title: str, description: str = None):
    """Create a styled section header"""
    st.markdown(f"### {title}")
    if description:
        st.caption(description)
    st.markdown("---")


def styled_plotly_chart(fig, title: str = "", height: int = None):
    """
    Style a Plotly figure with education theme
    
    Args:
        fig: Plotly figure object
        title: Chart title
        height: Optional chart height
    """
    fig.update_layout(
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter", size=13, color="#2c3e50"),
        title_font=dict(size=18, family="Poppins", color="#2c3e50", weight=600),
        title=title if title else None,
        margin=dict(t=50 if title else 20, l=10, r=10, b=40),
        xaxis=dict(
            showgrid=False,
            linecolor="rgba(0,0,0,0.1)",
            gridcolor="rgba(0,0,0,0.05)"
        ),
        yaxis=dict(
            gridcolor="rgba(0,0,0,0.05)",
            linecolor="rgba(0,0,0,0.1)"
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5,
            font=dict(family="Inter", size=12)
        ),
        height=height,
        hovermode="closest",
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.9)",
            font_size=12,
            font_family="Inter"
        )
    )
    return fig

