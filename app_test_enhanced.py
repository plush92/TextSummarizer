import streamlit as st
from datetime import datetime
import re

# Test: Add the problematic import
from summarizer import TextSummarizer, AnalysisEngine

# Basic page config
st.set_page_config(
    page_title="Article Analysis System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables."""
    if 'config' not in st.session_state:
        st.session_state.config = None
    if 'analysis_engine' not in st.session_state:
        st.session_state.analysis_engine = None
    if 'last_results' not in st.session_state:
        st.session_state.last_results = None

def get_character_counts(text: str) -> dict:
    """Get character and word counts for text."""
    if not text:
        return {"chars": 0, "words": 0, "chars_display": "0", "words_display": "0"}
    
    char_count = len(text)
    word_count = len(text.split())
    
    return {
        "chars": char_count,
        "words": word_count, 
        "chars_display": f"{char_count:,}",
        "words_display": f"{word_count:,}"
    }

def calculate_quality_score(text: str, mode: str) -> tuple:
    """Calculate content quality score."""
    if not text or len(text.strip()) == 0:
        return 0.0, "Empty"
    
    # Simple quality metrics
    word_count = len(text.split())
    char_count = len(text)
    
    if word_count < 50:
        return 0.3, "Low"
    elif word_count < 200:  
        return 0.6, "Medium"
    else:
        return 0.9, "High"

def main():
    """Enhanced Article Analysis Application - Gradual Testing."""
    initialize_session_state()
    
    # Safe enhanced header using native Streamlit components
    st.markdown("# 🔍 Article Analysis System")
    st.markdown("**AI-Powered Analysis • Bias Detection • Multi-Source Comparison**")
    
    # Basic sidebar
    st.sidebar.markdown("## ⚙️ Configuration")
    st.sidebar.markdown("**Step 1:** Configure your analysis")
    
    # Simple model selection
    model = st.sidebar.selectbox(
        "AI Model",
        ["openai", "anthropic", "local"],
        format_func=lambda x: {
            "openai": "🚀 OpenAI GPT",
            "anthropic": "🧠 Anthropic Claude", 
            "local": "💻 Local Analysis"
        }[x]
    )
    
    # Analysis mode selection
    analysis_mode = st.sidebar.selectbox(
        "Analysis Type",
        ["Single Summary", "Bias Analysis", "Multi-Source Comparison"]
    )
    
    # Main content area with tabs
    tab1, tab2 = st.tabs(["📄 Single Article Analysis", "📊 Results"])
    
    with tab1:
        st.success("📄 **Article Input** - Step 2: Provide your article content")
        
        # Simple text input
        text_content = st.text_area(
            "Article Text",
            placeholder="Paste your article text here for analysis...\n\nTip: Include the full article text for best results. The system can handle articles of any length.",
            height=200
        )
        
        # Content quality metrics
        if text_content:
            quality_score, quality_level = calculate_quality_score(text_content, analysis_mode)
            counts = get_character_counts(text_content)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📊 Content Quality", f"{quality_level}", f"{quality_score:.1%} confidence")
            with col2:
                st.metric("📝 Word Count", counts['words_display'])
            with col3:
                st.metric("🚀 Model Status", model.upper())
        
        # Generate button
        if st.button("📝 Generate Summary", type="primary"):
            if text_content and len(text_content.strip()) > 0:
                st.success(f"✅ Analysis started for {len(text_content)} characters of text using {model}")
                st.info("This is a test - actual analysis engine not connected yet")
            else:
                st.warning("⚠️ Please provide article text before generating analysis.")
    
    with tab2:
        st.info("📊 Results will appear here after analysis")
        st.write("Analysis results and downloadable reports will be displayed in this tab.")

if __name__ == "__main__":
    main()