#!/usr/bin/env python3
"""
Article Analysis System - Streamlit Web UI
Advanced text analysis including summarization, bias detection, comparison, and synthesis.
"""

import streamlit as st
import tempfile
import os
from datetime import datetime
from pathlib import Path
import json
import traceback

# Import analysis components  
from summarizer import TextSummarizer, AnalysisEngine
from config import Config

# Page configuration
st.set_page_config(
    page_title="Article Analysis System",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .section-header {
        font-size: 1.5rem;
        color: #2c3e50;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #3498db;
        padding-bottom: 0.5rem;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #e2f3ff;
        border: 1px solid #b8daff;
        color: #004085;
    }
    .bias-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        color: #856404;
    }
    .comparison-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        color: #495057;
    }
    .synthesis-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #e7f3ff;
        border: 1px solid #b8daff;
        color: #0c5460;
    }
</style>""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'config' not in st.session_state:
        st.session_state.config = None
    if 'analysis_engine' not in st.session_state:
        st.session_state.analysis_engine = None
    if 'last_results' not in st.session_state:
        st.session_state.last_results = None
    if 'articles' not in st.session_state:
        st.session_state.articles = []


def setup_sidebar():
    """Setup sidebar with configuration options."""
    st.sidebar.markdown("## ⚙️ Configuration")
    
    # Analysis mode selection
    st.sidebar.markdown("### 🎯 Analysis Mode")
    analysis_mode = st.sidebar.selectbox(
        "Choose Analysis Type",
        options=[
            "Single Summary", 
            "Bias Analysis", 
            "Multi-Article Comparison", 
            "Neutral Synthesis",
            "Full Report"
        ],
        help="Select the type of analysis to perform"
    )
    
    # Model selection
    model_options = ["openai", "anthropic", "local"]
    selected_model = st.sidebar.selectbox(
        "Select AI Model",
        options=model_options,
        index=0,
        help="Choose the AI model for analysis"
    )
    
    # API Key configuration
    st.sidebar.markdown("### 🔑 API Keys")
    
    openai_key = ""
    anthropic_key = ""
    
    if selected_model == "openai":
        openai_key = st.sidebar.text_input(
            "OpenAI API Key",
            type="password",
            help="Your OpenAI API key for GPT models"
        )
    elif selected_model == "anthropic":
        anthropic_key = st.sidebar.text_input(
            "Anthropic API Key",
            type="password",
            help="Your Anthropic API key for Claude models"
        )
    else:
        st.sidebar.info("Local model doesn't require an API key")
    
    # Additional settings
    st.sidebar.markdown("### 📋 Output Settings")
    save_output = st.sidebar.checkbox("Save output to file", value=True)
    verbose_mode = st.sidebar.checkbox("Verbose output", value=False)
    
    return {
        'analysis_mode': analysis_mode,
        'model': selected_model,
        'openai_key': openai_key,
        'anthropic_key': anthropic_key,
        'save_output': save_output,
        'verbose_mode': verbose_mode
    }


def create_temp_config(settings):
    """Create a temporary configuration with the provided settings."""
    try:
        # Create a temporary config object
        config = Config()
        
        # Override with UI settings
        if settings['openai_key']:
            os.environ['OPENAI_API_KEY'] = settings['openai_key']
        if settings['anthropic_key']:
            os.environ['ANTHROPIC_API_KEY'] = settings['anthropic_key']
        
        # Set model preference
        os.environ['SUMMARIZER_DEFAULT_MODEL'] = settings['model']
        
        return config
    except Exception as e:
        st.error(f"Configuration error: {str(e)}")
        return None


def validate_inputs(text_content, settings):
    """Validate user inputs before processing."""
    if not text_content.strip():
        st.error("Please provide some text to analyze.")
        return False
    
    if len(text_content.strip()) < 50:
        st.warning("Text seems quite short. You might get better results with longer text.")
    
    selected_model = settings['model']
    if selected_model in ["openai", "anthropic"]:
        key_field = f"{selected_model}_key"
        if not settings.get(key_field):
            st.error(f"Please provide your {selected_model.title()} API key in the sidebar.")
            return False
    
    return True


def format_summary_display(result):
    """Format and display the summary results with proper styling."""
    if not result:
        return
    
    try:
        # Parse result if it's a string
        if isinstance(result, str):
            # Try to extract structured data from the formatted output
            lines = result.strip().split('\n')
            summary = ""
            key_points = []
            action_items = []
            
            current_section = None
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                if line.startswith('📝') and 'SUMMARY' in line.upper():
                    current_section = 'summary'
                    continue
                elif line.startswith('🔑') and 'KEY POINTS' in line.upper():
                    current_section = 'key_points'
                    continue
                elif line.startswith('✅') and 'ACTION ITEMS' in line.upper():
                    current_section = 'action_items'
                    continue
                
                if current_section == 'summary':
                    summary += line + " "
                elif current_section == 'key_points' and line.startswith('-'):
                    key_points.append(line[1:].strip())
                elif current_section == 'action_items' and line.startswith('-'):
                    action_items.append(line[1:].strip())
            
            result = {
                'summary': summary.strip(),
                'key_points': key_points,
                'action_items': action_items
            }
        
        # Display formatted results
        st.markdown('<div class="section-header">📝 Summary</div>', unsafe_allow_html=True)
        if result.get('summary'):
            st.markdown(f'<div class="success-box">{result["summary"]}</div>', unsafe_allow_html=True)
        else:
            st.write("No summary available")
        
        st.markdown('<div class="section-header">🔑 Key Points</div>', unsafe_allow_html=True)
        if result.get('key_points'):
            for point in result['key_points']:
                st.markdown(f"• {point}")
        else:
            st.write("No key points available")
        
        st.markdown('<div class="section-header">✅ Action Items</div>', unsafe_allow_html=True)
        if result.get('action_items'):
            for item in result['action_items']:
                st.markdown(f"• {item}")
        else:
            st.write("No action items available")
            
    except Exception as e:
        st.error(f"Error formatting results: {str(e)}")
        # Fallback: display raw result
        st.text(str(result))


def display_bias_analysis(result):
    """Display bias analysis results with proper styling."""
    if not result or result.get('error'):
        st.error(f"Bias analysis failed: {result.get('error', 'Unknown error')}")
        return
    
    st.markdown('<div class="section-header">🎯 Bias Analysis</div>', unsafe_allow_html=True)
    
    # Bias score with color coding
    bias_score = result.get('bias_score', 0)
    confidence = result.get('confidence', 0)
    direction = result.get('bias_direction', 'neutral')
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if bias_score > 2:
            st.error(f"**Bias Score:** {bias_score}/10 (Right-leaning)")
        elif bias_score < -2:
            st.error(f"**Bias Score:** {bias_score}/10 (Left-leaning)")
        else:
            st.success(f"**Bias Score:** {bias_score}/10 (Neutral)")
    
    with col2:
        st.metric("Confidence", f"{confidence}%")
    
    with col3:
        objectivity = result.get('objectivity_score', 0)
        st.metric("Objectivity", f"{objectivity}%")
    
    # Bias indicators
    if result.get('bias_indicators'):
        st.markdown("**🔍 Bias Indicators:**")
        for indicator in result['bias_indicators']:
            st.markdown(f"• {indicator}")
    
    # Emotional language
    if result.get('emotional_language'):
        st.markdown("**😤 Emotional Language:**")
        for emotion in result['emotional_language']:
            st.markdown(f"• {emotion}")
    
    # Recommendations
    if result.get('recommendations'):
        st.markdown('<div class="bias-box">', unsafe_allow_html=True)
        st.markdown(f"**💡 Interpretation Guide:** {result['recommendations']}")
        st.markdown('</div>', unsafe_allow_html=True)


def display_comparison_results(result):
    """Display article comparison results."""
    if not result or result.get('error'):
        st.error(f"Comparison failed: {result.get('error', 'Unknown error')}")
        return
    
    st.markdown('<div class="section-header">🔄 Article Comparison</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📋 Similarities**")
        similarities = result.get('similarities', [])
        for sim in similarities:
            st.markdown(f"✅ {sim}")
        
        st.markdown("**🤝 Factual Agreements**")
        agreements = result.get('factual_agreements', [])
        for agree in agreements:
            st.markdown(f"✅ {agree}")
    
    with col2:
        st.markdown("**⚡ Key Differences**")
        differences = result.get('differences', [])
        for diff in differences:
            st.markdown(f"❌ {diff}")
        
        st.markdown("**⚠️ Factual Disagreements**")
        disagreements = result.get('factual_disagreements', [])
        for disagree in disagreements:
            st.markdown(f"❌ {disagree}")
    
    # Main topic and bias comparison
    st.markdown('<div class="comparison-box">', unsafe_allow_html=True)
    st.markdown(f"**🎯 Main Topic:** {result.get('main_topic', 'Not identified')}")
    st.markdown(f"**⚖️ Bias Analysis:** {result.get('bias_comparison', 'Not available')}")
    st.markdown(f"**📝 Recommendation:** {result.get('recommendation', 'No guidance available')}")
    st.markdown('</div>', unsafe_allow_html=True)


def display_synthesis_results(result):
    """Display neutral synthesis results."""
    if not result or result.get('error'):
        st.error(f"Synthesis failed: {result.get('error', 'Unknown error')}")
        return
    
    st.markdown('<div class="section-header">🔗 Neutral Synthesis</div>', unsafe_allow_html=True)
    
    # Title and summary
    title = result.get('title', 'Synthesis Report')
    st.markdown(f"### {title}")
    
    summary = result.get('neutral_summary', 'No summary available')
    st.markdown('<div class="synthesis-box">', unsafe_allow_html=True)
    st.markdown(summary)
    st.markdown('</div>', unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**📊 Key Facts (Verified)**")
        facts = result.get('key_facts', [])
        for fact in facts:
            st.markdown(f"• {fact}")
        
        st.markdown("**🤝 Areas of Consensus**")
        consensus = result.get('areas_of_consensus', [])
        for item in consensus:
            st.markdown(f"✅ {item}")
    
    with col2:
        st.markdown("**👥 Different Perspectives**")
        perspectives = result.get('different_perspectives', [])
        for perspective in perspectives:
            st.markdown(f"• {perspective}")
        
        st.markdown("**⚠️ Areas of Disagreement**")
        disagreements = result.get('areas_of_disagreement', [])
        for item in disagreements:
            st.markdown(f"❌ {item}")
    
    # Confidence and limitations
    st.markdown("**📈 Quality Assessment**")
    confidence = result.get('confidence_assessment', 'Not assessed')
    limitations = result.get('limitations', 'None specified')
    
    st.info(f"**Confidence:** {confidence}")
    if limitations != 'None specified':
        st.warning(f"**Limitations:** {limitations}")


def manage_articles():
    """Handle multiple article input and management."""
    st.markdown("## 📚 Article Management")
    
    # Add new article
    with st.expander("➕ Add New Article", expanded=len(st.session_state.articles) == 0):
        title = st.text_input("Article Title (optional)")
        
        input_method = st.radio("Input method:", ["Direct Text", "File Upload"], key="article_input")
        
        content = ""
        if input_method == "Direct Text":
            content = st.text_area("Article Content", height=200)
        else:
            uploaded_file = st.file_uploader("Upload Article File", type=['txt', 'md'])
            if uploaded_file:
                content = str(uploaded_file.read(), "utf-8")
                if not title:
                    title = uploaded_file.name
        
        if st.button("Add Article") and content.strip():
            article = {
                'title': title or f"Article {len(st.session_state.articles) + 1}",
                'content': content.strip()
            }
            st.session_state.articles.append(article)
            st.success(f"Added article: {article['title']}")
            st.rerun()
    
    # Display existing articles
    if st.session_state.articles:
        st.markdown("### 📄 Loaded Articles")
        for i, article in enumerate(st.session_state.articles):
            with st.expander(f"{i+1}. {article['title']} ({len(article['content'])} chars)"):
                st.text(article['content'][:300] + "..." if len(article['content']) > 300 else article['content'])
                if st.button(f"Remove", key=f"remove_{i}"):
                    st.session_state.articles.pop(i)
                    st.rerun()
        
        if st.button("Clear All Articles"):
            st.session_state.articles = []
            st.rerun()
    
    return len(st.session_state.articles) > 0


def save_results_to_file(result, settings):
    """Save results to a timestamped file."""
    if not settings['save_output']:
        return None
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"summary_{timestamp}.txt"
        filepath = Path(filename)
        
        # Convert result to string format
        if isinstance(result, dict):
            content = f"""📝 SHORT SUMMARY
{result.get('summary', 'No summary available')}

🔑 KEY POINTS
"""
            for point in result.get('key_points', []):
                content += f"- {point}\n"
            
            content += "\n✅ ACTION ITEMS\n"
            for item in result.get('action_items', []):
                content += f"- {item}\n"
        else:
            content = str(result)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return filepath
    except Exception as e:
        st.error(f"Error saving file: {str(e)}")
        return None


def create_download_content(result):
    """Create downloadable content from the results."""
    if isinstance(result, dict):
        content = f"""TEXT SUMMARY REPORT
Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

📝 SUMMARY
{result.get('summary', 'No summary available')}

🔑 KEY POINTS
"""
        for point in result.get('key_points', []):
            content += f"• {point}\n"
        
        content += "\n✅ ACTION ITEMS\n"
        for item in result.get('action_items', []):
            content += f"• {item}\n"
    else:
        content = str(result)
    
    return content


def main():
    """Main Article Analysis Application."""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">🔍 Article Analysis System</h1>', unsafe_allow_html=True)
    st.markdown("Advanced text analysis: Summarization, bias detection, comparison, and synthesis")
    
    # Setup sidebar
    settings = setup_sidebar()
    analysis_mode = settings['analysis_mode']
    
    # Create tabs for different interfaces
    if analysis_mode in ["Single Summary", "Bias Analysis", "Full Report"]:
        tab1, tab2 = st.tabs(["📄 Single Article Analysis", "📊 Results"])
        
        with tab1:
            # Single article input
            st.markdown("## 📄 Article Input")
            
            input_method = st.radio(
                "Choose input method:",
                ["Direct Text Input", "File Upload"],
                horizontal=True
            )
            
            text_content = ""
            
            if input_method == "Direct Text Input":
                text_content = st.text_area(
                    "Enter or paste your article here:",
                    height=300,
                    placeholder="Paste your article text here for analysis..."
                )
            else:
                uploaded_file = st.file_uploader(
                    "Choose a text file",
                    type=['txt', 'md', 'py', 'js', 'html', 'css', 'json'],
                    help="Upload a text file to analyze"
                )
                
                if uploaded_file is not None:
                    try:
                        text_content = str(uploaded_file.read(), "utf-8")
                        st.success(f"File '{uploaded_file.name}' loaded successfully!")
                        
                        with st.expander("📋 File Preview"):
                            st.text(text_content[:1000] + "..." if len(text_content) > 1000 else text_content)
                            
                    except Exception as e:
                        st.error(f"Error reading file: {str(e)}")
            
            # Analysis button
            analysis_label = {
                "Single Summary": "📝 Generate Summary",
                "Bias Analysis": "🎯 Analyze Bias", 
                "Full Report": "📊 Generate Full Report"
            }
            
            if st.button(analysis_label[analysis_mode], type="primary", use_container_width=True):
                if validate_inputs(text_content, settings):
                    with st.spinner(f"Performing {analysis_mode.lower()}..."):
                        try:
                            # Create configuration and analysis engine
                            config = create_temp_config(settings)
                            if not config:
                                return
                            
                            engine = AnalysisEngine(
                                model_type=settings['model'], 
                                config=config, 
                                verbose=settings['verbose_mode']
                            )
                            
                            # Perform analysis based on mode
                            if analysis_mode == "Single Summary":
                                result = engine.analyze_single_article(text_content, mode='summary')
                            elif analysis_mode == "Bias Analysis":
                                result = engine.analyze_single_article(text_content, mode='bias')
                            elif analysis_mode == "Full Report":
                                result = engine.analyze_single_article(text_content, mode='full')
                            
                            # Store results
                            st.session_state.last_results = {
                                'type': analysis_mode,
                                'data': result
                            }
                            
                            # Save to file if requested
                            if settings['save_output']:
                                filepath = save_results_to_file(result, settings)
                                if filepath:
                                    st.success(f"Results saved to: {filepath}")
                            
                            st.success(f"{analysis_mode} completed successfully!")
                            
                        except Exception as e:
                            st.error(f"Error during analysis: {str(e)}")
                            if settings['verbose_mode']:
                                st.code(traceback.format_exc())
        
        with tab2:
            # Display results
            if st.session_state.last_results:
                result_type = st.session_state.last_results['type']
                result_data = st.session_state.last_results['data']
                
                if result_type == "Single Summary":
                    format_summary_display(result_data)
                elif result_type == "Bias Analysis":
                    display_bias_analysis(result_data)
                elif result_type == "Full Report":
                    if result_data.get('summary'):
                        format_summary_display(result_data['summary'])
                    if result_data.get('bias_analysis'):
                        display_bias_analysis(result_data['bias_analysis'])
                
                # Export options
                st.markdown("---")
                st.markdown("## 📥 Export")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    download_content = create_download_content(result_data)
                    st.download_button(
                        label="📄 Download as Text",
                        data=download_content,
                        file_name=f"{result_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                
                with col2:
                    if isinstance(result_data, dict):
                        json_content = json.dumps(result_data, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="📋 Download as JSON",
                            data=json_content,
                            file_name=f"{result_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                
                with col3:
                    if st.button("🗑️ Clear Results"):
                        st.session_state.last_results = None
                        st.rerun()
            else:
                st.info("No analysis results yet. Use the 'Single Article Analysis' tab to get started.")
    
    else:  # Multi-article modes
        tab1, tab2 = st.tabs(["📚 Multi-Article Input", "📊 Analysis Results"])
        
        with tab1:
            has_articles = manage_articles()
            
            if has_articles and len(st.session_state.articles) >= 2:
                # Multi-article analysis button
                analysis_label = {
                    "Multi-Article Comparison": "🔄 Compare Articles",
                    "Neutral Synthesis": "🔗 Generate Synthesis"
                }
                
                if st.button(analysis_label[analysis_mode], type="primary", use_container_width=True):
                    with st.spinner(f"Performing {analysis_mode.lower()}..."):
                        try:
                            # Create configuration and analysis engine
                            config = create_temp_config(settings)
                            if not config:
                                return
                            
                            engine = AnalysisEngine(
                                model_type=settings['model'], 
                                config=config, 
                                verbose=settings['verbose_mode']
                            )
                            
                            # Perform multi-article analysis
                            if analysis_mode == "Multi-Article Comparison":
                                result = engine.analyze_multiple_articles(st.session_state.articles, mode='compare')
                            elif analysis_mode == "Neutral Synthesis":
                                result = engine.analyze_multiple_articles(st.session_state.articles, mode='synthesis')
                            
                            # Store results
                            st.session_state.last_results = {
                                'type': analysis_mode,
                                'data': result
                            }
                            
                            st.success(f"{analysis_mode} completed successfully!")
                            
                        except Exception as e:
                            st.error(f"Error during analysis: {str(e)}")
                            if settings['verbose_mode']:
                                st.code(traceback.format_exc())
            
            elif has_articles:
                st.warning(f"You have {len(st.session_state.articles)} article(s). Need at least 2 articles for comparison/synthesis.")
            else:
                st.info("Add at least 2 articles to perform multi-article analysis.")
        
        with tab2:
            # Display multi-article results
            if st.session_state.last_results:
                result_type = st.session_state.last_results['type']
                result_data = st.session_state.last_results['data']
                
                if result_type == "Multi-Article Comparison":
                    display_comparison_results(result_data)
                elif result_type == "Neutral Synthesis":
                    display_synthesis_results(result_data)
                
                # Export options
                st.markdown("---")
                st.markdown("## 📥 Export")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    download_content = create_download_content(result_data)
                    st.download_button(
                        label="📄 Download as Text",
                        data=download_content,
                        file_name=f"{result_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                        mime="text/plain"
                    )
                
                with col2:
                    if isinstance(result_data, dict):
                        json_content = json.dumps(result_data, indent=2, ensure_ascii=False)
                        st.download_button(
                            label="📋 Download as JSON",
                            data=json_content,
                            file_name=f"{result_type.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                
                with col3:
                    if st.button("🗑️ Clear Results"):
                        st.session_state.last_results = None
                        st.rerun()
            else:
                st.info("No analysis results yet. Use the 'Multi-Article Input' tab to get started.")
    
    # Sidebar help
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🆘 Help")
        
        mode_help = {
            "Single Summary": "Generate concise summaries with key points and action items.",
            "Bias Analysis": "Detect political/ideological bias and emotional language.",
            "Multi-Article Comparison": "Compare articles side-by-side to find similarities and differences.",
            "Neutral Synthesis": "Create balanced synthesis from multiple sources.",
            "Full Report": "Complete analysis combining summary and bias detection."
        }
        
        st.info(mode_help.get(analysis_mode, "Select an analysis mode to see help."))
        
        if settings['model'] == 'local':
            st.warning("🏠 Local mode provides basic analysis. Use AI models (OpenAI/Anthropic) for advanced features.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666666; padding: 1rem;'>
            Built with ❤️ using Streamlit | Article Analysis System v2.0
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()