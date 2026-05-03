import streamlit as st
import requests
import json
import re
from datetime import datetime
from urllib.parse import urlparse
import html
from typing import Dict, List, Any, Optional

# Import analysis engine and config
from summarizer import TextSummarizer, AnalysisEngine
from config import Config

# Page configuration
st.set_page_config(
    page_title="Article Analysis System",
    page_icon="🔍", 
    layout="wide",
    initial_sidebar_state="expanded"
)

def initialize_session_state():
    """Initialize session state variables safely."""
    defaults = {
        'config': None,
        'analysis_engine': None,
        'last_results': None,
        'articles': [],
        'api_key_valid': False,
        'processing': False
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

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
    
    word_count = len(text.split())
    sentences = len([s for s in re.split(r'[.!?]+', text) if s.strip()])
    
    # Quality scoring
    if word_count < 50:
        return 0.3, "Low"
    elif word_count < 200:
        return 0.6, "Medium"
    elif word_count < 1000:
        return 0.8, "High"
    else:
        return 0.9, "Excellent"

def auto_detect_language(text: str) -> str:
    """Simple language detection."""
    if not text:
        return "Unknown"
    
    # Simple heuristics for common languages
    common_english_words = ['the', 'and', 'is', 'in', 'to', 'of', 'a', 'that', 'it', 'with']
    words = text.lower().split()[:100]  # Check first 100 words
    
    english_count = sum(1 for word in words if word in common_english_words)
    if english_count > len(words) * 0.1:  # If >10% are common English words
        return "English"
    return "Other"

def validate_api_key(provider: str, api_key: str) -> bool:
    """Validate API key format."""
    if not api_key or len(api_key.strip()) < 10:
        return False
    
    if provider == "openai":
        return api_key.startswith("sk-") and len(api_key) > 40
    elif provider == "anthropic":
        return api_key.startswith("sk-ant-") and len(api_key) > 40
    
    return False

def fetch_article_from_url(url: str) -> tuple:
    """Fetch article content from URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Simple content extraction (in production, use newspaper3k or similar)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text
        text = soup.get_text()
        
        # Clean up text
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = ' '.join(chunk for chunk in chunks if chunk)
        
        # Try to extract title
        title = soup.find('title')
        title_text = title.get_text() if title else "Article"
        
        return text, title_text, None
        
    except Exception as e:
        return "", "", str(e)

def setup_sidebar():
    """Setup enhanced sidebar configuration."""
    st.sidebar.markdown("## ⚙️ Configuration")
    st.sidebar.markdown("**Step 1:** Configure your analysis")
    
    # Model Settings
    with st.sidebar.expander("🤖 Model Settings", expanded=True):
        st.markdown("**Choose AI Model:**")
        
        model_options = [
            ("openai", "🚀 OpenAI GPT", "Most advanced, requires API key"),
            ("anthropic", "🧠 Anthropic Claude", "Great reasoning, requires API key"),
            ("local", "💻 Local Analysis", "Basic analysis, no API key needed")
        ]
        
        selected_model = st.selectbox(
            "AI Model",
            options=[opt[0] for opt in model_options],
            format_func=lambda x: next(opt[1] for opt in model_options if opt[0] == x),
            key="model_selection"
        )
        
        # Show model info
        model_info = next(opt[2] for opt in model_options if opt[0] == selected_model)
        st.info(f"ℹ️ {model_info}")
        
        # API Key input for cloud models
        api_key = None
        api_key_valid = False
        
        if selected_model != "local":
            show_key = st.checkbox("Show API key", key="show_api_key")
            key_label = f"{'OpenAI' if selected_model == 'openai' else 'Anthropic'} API Key"
            
            api_key = st.text_input(
                key_label,
                type="text" if show_key else "password",
                placeholder="sk-..." if selected_model == "openai" else "sk-ant-...",
                key="api_key_input"
            )
            
            if api_key:
                api_key_valid = validate_api_key(selected_model, api_key)
                if api_key_valid:
                    st.success("✅ API key format valid")
                else:
                    st.error("❌ Invalid API key format")
            
            st.warning("🔒 **Security:** API keys are used locally and never stored on servers.")
    
    # Analysis Settings
    with st.sidebar.expander("🎯 Analysis Settings", expanded=True):
        analysis_mode = st.selectbox(
            "Analysis Type",
            options=[
                "Single Summary",
                "Bias Analysis", 
                "Multi-Source Comparison",
                "Source Convergence Analysis"
            ],
            key="analysis_mode"
        )
        
        # Mode descriptions
        mode_descriptions = {
            "Single Summary": "📝 Extract key points and summary from one article",
            "Bias Analysis": "🎯 Detect political bias and missing perspectives",
            "Multi-Source Comparison": "📊 Compare articles from different sources",
            "Source Convergence Analysis": "🔍 Find consensus vs disputed claims"
        }
        
        st.info(mode_descriptions.get(analysis_mode, ""))
    
    # Output Settings  
    with st.sidebar.expander("📋 Output Settings"):
        output_format = st.selectbox(
            "Export Format",
            ["JSON", "Markdown", "Plain Text"],
            key="output_format"
        )
        
        include_metadata = st.checkbox("Include metadata", value=True, key="include_metadata")
        include_raw_text = st.checkbox("Include raw text", value=False, key="include_raw_text")
    
    # Update session state
    st.session_state.api_key_valid = api_key_valid
    
    return {
        'model': selected_model,
        'api_key': api_key,
        'api_key_valid': api_key_valid,
        'analysis_mode': analysis_mode,
        'output_format': output_format,
        'include_metadata': include_metadata,
        'include_raw_text': include_raw_text
    }

def show_workflow_guide():
    """Display workflow guide."""
    st.markdown("### 📋 Analysis Workflow")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.info("🎯 **1. Configure**\nSet model & API key")
    with col2:
        st.info("🎯 **2. Provide**\nAdd your article")
    with col3:
        st.info("🎯 **3. Analyze**\nChoose analysis type")
    with col4:
        st.info("🎯 **4. Results**\nView & download")

def create_analysis_engine(settings):
    """Create analysis engine based on settings."""
    try:
        if settings['model'] == 'local':
            return AnalysisEngine('local')
        elif settings['api_key_valid']:
            # Create a temporary config object with the API key
            class TempConfig:
                def __init__(self, openai_key=None, anthropic_key=None):
                    self.openai_key = openai_key
                    self.anthropic_key = anthropic_key
                
                def get_openai_api_key(self):
                    return self.openai_key
                
                def get_anthropic_api_key(self):
                    return self.anthropic_key
            
            # Create config with appropriate API key
            if settings['model'] == 'openai':
                config = TempConfig(openai_key=settings['api_key'])
            else:  # anthropic
                config = TempConfig(anthropic_key=settings['api_key'])
            
            return AnalysisEngine(settings['model'], config=config)
        else:
            return None
    except Exception as e:
        st.error(f"Error creating analysis engine: {str(e)}")
        return None

def display_analysis_results(results, settings):
    """Display analysis results in tabs."""
    if not results:
        st.warning("No results to display")
        return
    
    # Create tabs for results
    tab_names = ["📄 Summary", "📊 Analysis", "📋 Details"]
    if settings['analysis_mode'] == "Bias Analysis":
        tab_names.append("🎯 Bias Report")
    
    tabs = st.tabs(tab_names)
    
    # Summary tab
    with tabs[0]:
        if 'summary' in results:
            st.markdown("### Summary")
            st.write(results['summary'])
        
        if 'key_points' in results:
            st.markdown("### Key Points")
            for i, point in enumerate(results['key_points'], 1):
                st.markdown(f"{i}. {point}")
    
    # Analysis tab
    with tabs[1]:
        if 'analysis' in results:
            st.markdown("### Analysis")
            st.write(results['analysis'])
        
        # Show metrics
        col1, col2, col3 = st.columns(3)
        
        if 'quality_score' in results:
            with col1:
                st.metric("Quality Score", f"{results['quality_score']:.1%}")
        
        if 'word_count' in results:
            with col2:
                st.metric("Word Count", f"{results['word_count']:,}")
        
        if 'confidence' in results:
            with col3:
                st.metric("Confidence", f"{results['confidence']:.1%}")
    
    # Details tab
    with tabs[2]:
        st.markdown("### Analysis Details")
        
        if 'metadata' in results:
            st.json(results['metadata'])
        
        # Download button
        if st.button("📥 Download Results"):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"analysis_{timestamp}.json"
            
            st.download_button(
                label="Download JSON",
                data=json.dumps(results, indent=2),
                file_name=filename,
                mime="application/json"
            )

def main():
    """Main application with enhanced features."""
    initialize_session_state()
    
    # Header
    st.markdown("# 🔍 Article Analysis System")
    st.markdown("**AI-Powered Analysis • Bias Detection • Multi-Source Comparison**")
    
    # Workflow guide
    show_workflow_guide()
    
    # Setup sidebar and get settings
    settings = setup_sidebar()
    
    # Quick status bar
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.markdown(f"**Current Mode:** {settings['analysis_mode']}")
    with col2:
        st.markdown(f"**Model:** {settings['model'].title()}")
    with col3:
        status = "✅ Valid" if settings['api_key_valid'] or settings['model'] == 'local' else "❌ Invalid"
        st.markdown(f"**API Key:** {status}")
    with col4:
        if st.button("🔄 Reset", help="Reset all settings"):
            for key in st.session_state.keys():
                if key not in ['config', 'analysis_engine']:  # Keep essential state
                    del st.session_state[key]
            st.experimental_rerun()
    
    # Main content tabs
    tab1, tab2 = st.tabs(["📄 Single Article Analysis", "📊 Results"])
    
    with tab1:
        st.success("📄 **Article Input** - Step 2: Provide your article content")
        
        # Input method selection
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            text_input_selected = st.checkbox("📝 Text Input", value=True, key="text_input_cb")
        with col2:
            file_input_selected = st.checkbox("📁 File Upload", value=False, key="file_input_cb")
        with col3:
            url_input_selected = st.checkbox("🌐 URL Fetch", value=False, key="url_input_cb")
        with col4:
            sample_selected = st.checkbox("📋 Sample Article", value=False, key="sample_cb")
        
        text_content = ""
        article_title = ""
        source_url = ""
        
        # Text input
        if text_input_selected:
            st.markdown("**📝 Direct Text Input**")
            st.markdown("*💡 Paste any article text here to begin analysis*")
            
            text_content = st.text_area(
                "Article Text",
                placeholder="Paste your article text here for analysis...\n\nTip: Include the full article text for best results. The system can handle articles of any length.",
                height=200,
                key="article_text_input"
            )
        
        # File upload
        if file_input_selected:
            st.markdown("**📁 File Upload**")
            st.info("📁 **File Upload** - Drag and drop files here, or click to browse\n\nSupports: TXT, MD, HTML, JSON, PDF, DOC")
            
            uploaded_file = st.file_uploader(
                "Choose a file",
                type=['txt', 'md', 'py', 'js', 'html', 'css', 'json'],
                help="Upload any text-based file for analysis",
                label_visibility="collapsed",
                key="file_uploader"
            )
            
            if uploaded_file is not None:
                try:
                    content = uploaded_file.read().decode('utf-8')
                    text_content = content
                    article_title = uploaded_file.name
                    st.success(f"✅ File loaded: {len(content)} characters")
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
        
        # URL fetch
        if url_input_selected:
            st.markdown("**🌐 URL Article Fetch**")
            
            url_input = st.text_input(
                "Article URL",
                placeholder="https://example.com/article",
                help="Enter a URL to automatically fetch article content",
                key="url_input"
            )
            
            if url_input and st.button("🔍 Fetch Article", key="fetch_btn"):
                with st.spinner("Fetching article..."):
                    fetched_text, fetched_title, error = fetch_article_from_url(url_input)
                    
                    if error:
                        st.error(f"Error fetching article: {error}")
                    else:
                        text_content = fetched_text
                        article_title = fetched_title
                        source_url = url_input
                        st.success(f"✅ Article fetched: {len(fetched_text)} characters")
        
        # Sample article
        if sample_selected:
            st.markdown("**📋 Sample Article**")
            
            sample_articles = {
                "Tech News": "Apple announced its latest iPhone model featuring advanced AI capabilities and improved battery life. The new device includes a revolutionary camera system and enhanced security features.",
                "Political Article": "The recent policy changes have sparked debate among lawmakers about the future direction of healthcare reform. Supporters argue it will improve access while critics raise concerns about costs.",
                "Science Article": "Researchers at MIT have developed a new method for producing clean energy that could revolutionize how we power our cities. The breakthrough uses advanced materials science principles."
            }
            
            selected_sample = st.selectbox("Choose sample:", list(sample_articles.keys()), key="sample_select")
            
            if st.button("📋 Load Sample", key="load_sample_btn"):
                text_content = sample_articles[selected_sample]
                article_title = selected_sample
                st.success(f"✅ Sample loaded: {selected_sample}")
        
        # Analysis ready section
        if text_content:
            st.info("🎯 **Analysis Ready** - Step 3: Run your analysis with AI")
            
            # Pre-analysis metrics
            quality_score, quality_level = calculate_quality_score(text_content, settings['analysis_mode'])
            counts = get_character_counts(text_content)
            detected_lang = auto_detect_language(text_content)
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("📊 Content Quality", f"{quality_level}", f"{quality_score:.1%} confidence")
            with col2:
                st.metric("📝 Word Count", counts['words_display'])
            with col3:
                st.metric("🌐 Language", detected_lang)
            with col4:
                ready_status = "✅ Ready" if settings['api_key_valid'] or settings['model'] == 'local' else "❌ Not Ready"
                st.metric("🚀 Model Status", ready_status)
            
            # Quality feedback
            if quality_score < 0.5:
                st.warning("⚠️ **Quality Notice:** Text appears short or simple. Consider adding more content for better analysis.")
            elif quality_score >= 0.8:
                st.success("✨ **High Quality:** Excellent content for comprehensive analysis!")
            
            # Analysis button
            can_analyze = (settings['api_key_valid'] or settings['model'] == 'local') and not st.session_state.get('processing', False)
            
            if st.button(
                "📝 Generate Analysis" if settings['analysis_mode'] == "Single Summary" else f"🎯 Run {settings['analysis_mode']}",
                disabled=not can_analyze,
                type="primary",
                key="analyze_btn"
            ):
                if not can_analyze:
                    st.error("❌ Please configure a valid API key or use local mode before analyzing.")
                else:
                    # Set processing state
                    st.session_state.processing = True
                    
                    with st.spinner(f"Running {settings['analysis_mode']}..."):
                        try:
                            # Create analysis engine
                            engine = create_analysis_engine(settings)
                            
                            if engine:
                                # Run real analysis
                                if settings['analysis_mode'] == "Single Summary":
                                    results = engine.analyze_single_article(
                                        text_content, 
                                        mode='summary',
                                        source_url=source_url,
                                        article_title=article_title
                                    )
                                elif settings['analysis_mode'] == "Bias Analysis":
                                    results = engine.analyze_single_article(
                                        text_content,
                                        mode='bias', 
                                        source_url=source_url,
                                        article_title=article_title
                                    )
                                else:
                                    # For other modes, use full analysis
                                    results = engine.analyze_single_article(
                                        text_content,
                                        mode='full',
                                        source_url=source_url,
                                        article_title=article_title
                                    )
                                
                                # Add metadata
                                results['metadata'] = {
                                    'model': settings['model'],
                                    'analysis_mode': settings['analysis_mode'],
                                    'timestamp': datetime.now().isoformat(),
                                    'language': detected_lang,
                                    'quality_score': quality_score,
                                    'word_count': counts['words']
                                }
                                
                                # Store results
                                st.session_state.last_results = results
                                
                                st.success("✅ Analysis completed successfully!")
                                st.info("📊 View results in the Results tab")
                                
                            else:
                                st.error("❌ Failed to create analysis engine")
                        
                        except Exception as e:
                            st.error(f"❌ Analysis failed: {str(e)}")
                        
                        finally:
                            st.session_state.processing = False
        else:
            st.info("👆 Please provide article content above to begin analysis")
    
    with tab2:
        if st.session_state.get('last_results'):
            st.success("📊 **Analysis Results** - Your analysis is complete")
            display_analysis_results(st.session_state.last_results, settings)
        else:
            st.info("📊 Results will appear here after analysis")
            st.write("Analysis results and downloadable reports will be displayed in this tab.")
    
    # Footer
    st.markdown("---")
    st.caption("Built with ❤️ using Streamlit | Article Analysis System v2.0")

if __name__ == "__main__":
    main()