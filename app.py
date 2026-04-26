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
import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse, urljoin

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

# Custom CSS for better styling with dark mode compatibility
st.markdown("""
<style>
    /* Dark mode detection and variables */
    :root {
        --success-bg: #d4edda;
        --success-border: #c3e6cb;
        --success-text: #155724;
        --error-bg: #f8d7da;
        --error-border: #f5c6cb;
        --error-text: #721c24;
        --info-bg: #e2f3ff;
        --info-border: #b8daff;
        --info-text: #004085;
        --bias-bg: #fff3cd;
        --bias-border: #ffeaa7;
        --bias-text: #856404;
        --comparison-bg: rgba(248, 249, 250, 0.8);
        --comparison-border: #dee2e6;
        --comparison-text: #495057;
        --synthesis-bg: #e7f3ff;
        --synthesis-border: #b8daff;
        --synthesis-text: #0c5460;
    }
    
    /* Dark theme overrides */
    @media (prefers-color-scheme: dark) {
        :root {
            --success-bg: rgba(40, 167, 69, 0.2);
            --success-border: rgba(40, 167, 69, 0.4);
            --success-text: #a3cfbb;
            --error-bg: rgba(220, 53, 69, 0.2);
            --error-border: rgba(220, 53, 69, 0.4);
            --error-text: #f5c2c7;
            --info-bg: rgba(13, 110, 253, 0.2);
            --info-border: rgba(13, 110, 253, 0.4);
            --info-text: #9ec5fe;
            --bias-bg: rgba(255, 193, 7, 0.2);
            --bias-border: rgba(255, 193, 7, 0.4);
            --bias-text: #fff3cd;
            --comparison-bg: rgba(108, 117, 125, 0.2);
            --comparison-border: rgba(108, 117, 125, 0.4);
            --comparison-text: #e9ecef;
            --synthesis-bg: rgba(13, 202, 240, 0.2);
            --synthesis-border: rgba(13, 202, 240, 0.4);
            --synthesis-text: #9eeaf9;
        }
    }
    
    /* Streamlit dark mode detection */
    [data-theme="dark"] {
        --success-bg: rgba(40, 167, 69, 0.2);
        --success-border: rgba(40, 167, 69, 0.4);
        --success-text: #a3cfbb;
        --error-bg: rgba(220, 53, 69, 0.2);
        --error-border: rgba(220, 53, 69, 0.4);
        --error-text: #f5c2c7;
        --info-bg: rgba(13, 110, 253, 0.2);
        --info-border: rgba(13, 110, 253, 0.4);
        --info-text: #9ec5fe;
        --bias-bg: rgba(255, 193, 7, 0.2);
        --bias-border: rgba(255, 193, 7, 0.4);
        --bias-text: #fff3cd;
        --comparison-bg: rgba(108, 117, 125, 0.2);
        --comparison-border: rgba(108, 117, 125, 0.4);
        --comparison-text: #e9ecef;
        --synthesis-bg: rgba(13, 202, 240, 0.2);
        --synthesis-border: rgba(13, 202, 240, 0.4);
        --synthesis-text: #9eeaf9;
    }

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
        background-color: var(--success-bg);
        border: 1px solid var(--success-border);
        color: var(--success-text);
        backdrop-filter: blur(10px);
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: var(--error-bg);
        border: 1px solid var(--error-border);
        color: var(--error-text);
        backdrop-filter: blur(10px);
    }
    .info-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: var(--info-bg);
        border: 1px solid var(--info-border);
        color: var(--info-text);
        backdrop-filter: blur(10px);
    }
    .bias-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: var(--bias-bg);
        border: 1px solid var(--bias-border);
        color: var(--bias-text);
        backdrop-filter: blur(10px);
    }
    .comparison-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: var(--comparison-bg);
        border: 1px solid var(--comparison-border);
        color: var(--comparison-text);
        backdrop-filter: blur(10px);
    }
    .synthesis-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: var(--synthesis-bg);
        border: 1px solid var(--synthesis-border);
        color: var(--synthesis-text);
        backdrop-filter: blur(10px);
    }
    
    /* Additional dark mode compatibility */
    .stAlert > div {
        background-color: transparent !important;
    }
    
    /* Ensure text visibility in all themes */
    .comparison-box *, .synthesis-box * {
        color: inherit !important;
    }
</style>""", unsafe_allow_html=True)


def fetch_article_from_url(url):
    """
    Fetch and extract article content from a URL using multiple methods.
    Returns dict with 'success', 'content', 'title', 'error' keys.
    """
    try:
        # Validate URL
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            return {
                'success': False,
                'error': 'Invalid URL. Please include http:// or https://',
                'content': '',
                'title': ''
            }
        
        # Add protocol if missing
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        
        # Set up headers to mimic a real browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
        
        # Fetch the webpage
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Try newspaper3k first (best for articles)
        try:
            from newspaper import Article
            article = Article(url)
            article.set_html(response.content)
            article.parse()
            
            if article.text and len(article.text.strip()) > 100:
                return {
                    'success': True,
                    'content': article.text.strip(),
                    'title': article.title or 'Extracted Article',
                    'error': ''
                }
        except ImportError:
            pass  # newspaper3k not available, fallback to BeautifulSoup
        except Exception:
            pass  # newspaper3k failed, fallback to BeautifulSoup
        
        # Fallback to BeautifulSoup extraction
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'header', 'footer', 'aside', 'advertisement']):
            element.decompose()
        
        # Try to find article content using common selectors
        content_selectors = [
            'article', '[role="main"]', '.article-body', '.entry-content', 
            '.post-content', '.content', '.main-content', '.article-content',
            '.story-body', '.article-text', '.post-body'
        ]
        
        article_content = ""
        title = ""
        
        # Extract title
        title_tag = soup.find('title')
        if title_tag:
            title = title_tag.get_text().strip()
        
        # Try to find article content
        for selector in content_selectors:
            elements = soup.select(selector)
            if elements:
                for element in elements:
                    text = element.get_text(separator=' ', strip=True)
                    if len(text) > len(article_content):
                        article_content = text
        
        # If no specific selectors work, try to extract paragraphs
        if not article_content or len(article_content) < 200:
            paragraphs = soup.find_all('p')
            article_content = ' '.join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 20])
        
        # Clean up the text
        article_content = re.sub(r'\s+', ' ', article_content).strip()
        
        if len(article_content) < 100:
            return {
                'success': False,
                'error': 'Could not extract meaningful content from this URL. The page might be behind a paywall, require JavaScript, or not contain article text.',
                'content': article_content,
                'title': title
            }
        
        return {
            'success': True,
            'content': article_content,
            'title': title or 'Extracted Article',
            'error': ''
        }
        
    except requests.exceptions.RequestException as e:
        return {
            'success': False,
            'error': f'Network error: {str(e)}',
            'content': '',
            'title': ''
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Error extracting content: {str(e)}',
            'content': '',
            'title': ''
        }


def validate_and_clean_url(url):
    """Clean and validate URL input from user."""
    if not url:
        return None, "Please enter a URL"
    
    url = url.strip()
    
    # Remove common prefixes that users might accidentally include
    prefixes_to_remove = ['www.', 'http://www.', 'https://www.']
    for prefix in prefixes_to_remove:
        if url.startswith(prefix) and not url.startswith('http'):
            url = url[len(prefix):]
    
    # Add https if no protocol
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    # Basic URL validation
    try:
        parsed = urlparse(url)
        if not all([parsed.scheme, parsed.netloc]):
            return None, "Invalid URL format"
        return url, None
    except Exception:
        return None, "Invalid URL format"


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
    """Display enhanced bias analysis results with comprehensive visualizations."""
    if not result or result.get('error'):
        st.error(f"Bias analysis failed: {result.get('error', 'Unknown error')}")
        return
    
    # Methodology explanation header
    st.markdown('<div class="section-header">🎯 Enhanced Bias Analysis</div>', unsafe_allow_html=True)
    
    # Add methodology explanation
    with st.expander("📚 What is Bias Analysis?", expanded=False):
        st.markdown("""
        **Bias Analysis** examines text for systematic prejudices, unfair representations, or one-sided perspectives using multiple detection methods:
        
        **🔍 What We Analyze:**
        - **Language Bias**: Loaded words, emotional manipulation, selective terminology
        - **Framing Bias**: How topics are presented, what's emphasized vs. minimized
        - **Omission Bias**: Missing context, incomplete information, ignored perspectives
        - **Source Bias**: Publisher reputation, author credibility, institutional leanings
        
        **📊 Scoring System:**
        - **-10 to -3**: Strong left-leaning bias
        - **-2 to +2**: Relatively neutral/balanced
        - **+3 to +10**: Strong right-leaning bias
        - **Confidence**: How certain the analysis is (60%+ is reliable)
        
        **🎯 Methodology:**
        1. **Lexical Analysis**: Scans for biased terminology and emotional language
        2. **Contextual Evaluation**: Examines framing, missing information, and perspective balance
        3. **Source Assessment**: Considers publisher reputation and credibility indicators
        4. **Pattern Recognition**: Identifies systematic trends in language and presentation
        """)
    
    # Handle both old and new format
    overall_score = result.get('overall_bias_score', result.get('bias_score', 0))
    confidence = result.get('confidence_level', result.get('confidence', 0))
    direction = result.get('bias_direction', 'neutral')
    
    # === OVERVIEW SECTION ===
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if overall_score > 2:
            st.error(f"**Overall Bias**\n{overall_score}/10\n(Right-leaning)")
        elif overall_score < -2:
            st.error(f"**Overall Bias**\n{overall_score}/10\n(Left-leaning)")
        else:
            st.success(f"**Overall Bias**\n{overall_score}/10\n(Neutral)")
    
    with col2:
        confidence_color = "🟢" if confidence > 80 else "🟡" if confidence > 60 else "🔴"
        st.metric("Confidence", f"{confidence}%", delta=None, 
                 help="Confidence reflects how certain the analysis is based on available data. Higher scores indicate more reliable patterns detected. Calculated from source reliability, text length, and pattern clarity.")
        st.markdown(f"{confidence_color}")

    with col3:
        objectivity = result.get('objectivity_score', 100 - abs(overall_score * 10))
        st.metric("Objectivity", f"{objectivity}%",
                 help="Objectivity measures neutral language use and balanced perspective. Higher scores indicate less biased language. Calculated as inverse of bias intensity (100% - |bias_score| * 10).")
        # Source context if available
        if result.get('source_context'):
            st.info(f"📰 {result['source_context']}")
        else:
            st.info("📰 Unknown source")
    
    # === COMPONENT BREAKDOWN ===
    if result.get('component_scores'):
        st.markdown("### 📊 Bias Component Breakdown")
        
        components = result['component_scores']
        
        # Create visual component chart
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Component scores table
            import pandas as pd
            
            component_data = {
                'Component': ['Language Bias', 'Framing Bias', 'Omission Bias', 'Source Bias', 'Emotional Manipulation'],
                'Score': [
                    components.get('language_bias', 0),
                    components.get('framing_bias', 0), 
                    components.get('omission_bias', 0),
                    components.get('source_bias', 0),
                    components.get('emotional_manipulation', 0)
                ],
                'Impact': [
                    '🔴' if abs(components.get('language_bias', 0)) > 2 else '🟡' if abs(components.get('language_bias', 0)) > 1 else '🟢',
                    '🔴' if abs(components.get('framing_bias', 0)) > 2 else '🟡' if abs(components.get('framing_bias', 0)) > 1 else '🟢',
                    '🔴' if abs(components.get('omission_bias', 0)) > 2 else '🟡' if abs(components.get('omission_bias', 0)) > 1 else '🟢',
                    '🔴' if abs(components.get('source_bias', 0)) > 2 else '🟡' if abs(components.get('source_bias', 0)) > 1 else '🟢',
                    '🔴' if abs(components.get('emotional_manipulation', 0)) > 2 else '🟡' if abs(components.get('emotional_manipulation', 0)) > 1 else '🟢'
                ]
            }
            
            df = pd.DataFrame(component_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        
        with col2:
            # Score justification
            if result.get('explainability', {}).get('score_justification'):
                st.markdown("**📝 Score Explanation:**")
                st.info(result['explainability']['score_justification'])
    
    # === DETAILED ANALYSIS ===
    if result.get('detailed_analysis'):
        st.markdown("### 🔍 Detailed Analysis")
        
        detailed = result['detailed_analysis']
        
        # Create tabs for different analysis aspects
        tab1, tab2, tab3, tab4 = st.tabs(["🗣️ Language & Emotion", "🎭 Framing Issues", "❓ Missing Context", "📊 Technical Analysis"])
        
        with tab1:
            st.info("**📝 Focus**: This tab analyzes word choice, emotional tone, and persuasive language techniques.")
            
            # Biased phrases and emotional analysis
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="bias-box"><h4>🚨 Biased Phrases Detected</h4>', unsafe_allow_html=True)
                if detailed.get('biased_phrases'):
                    for phrase in detailed['biased_phrases'][:8]:  # Limit display
                        if isinstance(phrase, dict):
                            intensity_color = "🔴" if phrase.get('intensity', 0) > 7 else "🟡" if phrase.get('intensity', 0) > 4 else "🟢"
                            st.markdown(f"{intensity_color} **\"{phrase.get('text', '')}\"**<br>↳ {phrase.get('bias_type', 'unknown')} (intensity: {phrase.get('intensity', 0)}/10)", unsafe_allow_html=True)
                        else:
                            st.markdown(f"• {phrase}")
                else:
                    st.success("✅ No significantly biased phrases detected")
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="info-box"><h4>😤 Emotional Analysis</h4>', unsafe_allow_html=True)
                emotion_analysis = detailed.get('emotion_analysis', {})
                
                dominant_tone = emotion_analysis.get('dominant_tone', 'neutral')
                tone_emoji = {"anger": "😠", "fear": "😰", "moral_outrage": "😤", "contempt": "🙄", "neutral": "😐"}.get(dominant_tone, "😐")
                
                st.markdown(f"**Dominant Tone:** {tone_emoji} {dominant_tone.replace('_', ' ').title()}")
                
                if emotion_analysis.get('emotional_targets'):
                    st.markdown("**Emotional targets:**")
                    for target in emotion_analysis['emotional_targets'][:4]:
                        st.markdown(f"• {target}")
                
                author_vs_quoted = emotion_analysis.get('author_vs_quoted', 'unknown')
                if author_vs_quoted != 'unknown':
                    st.markdown(f"**Source of emotion:** {author_vs_quoted}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Language-specific tips
            st.markdown("**💡 What This Means:**")
            st.markdown("""
            - **High-intensity phrases** suggest strong bias or emotional manipulation
            - **Emotional targets** show who/what the article seeks to make you feel about
            - **Neutral tone** with varied perspectives suggests balanced reporting
            """)
        
        with tab2:
            st.info("**📝 Focus**: This tab examines how topics are presented, what's emphasized vs. minimized, and perspective balance.")
            
            # Framing issues
            st.markdown('<div class="comparison-box"><h4>🎭 Framing Analysis</h4>', unsafe_allow_html=True)
            
            if detailed.get('framing_issues'):
                for issue in detailed['framing_issues']:
                    if isinstance(issue, dict):
                        st.warning(f"**{issue.get('type', 'Unknown').replace('_', ' ').title()}**: {issue.get('description', 'No description')}")
                    else:
                        st.warning(f"• {issue}")
            else:
                st.success("✅ No significant framing issues detected")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Alternative perspectives section - unique to this tab
            if result.get('reader_guidance', {}).get('alternative_framings'):
                st.markdown('<div class="success-box"><h4>🔄 Alternative Perspectives to Consider</h4>', unsafe_allow_html=True)
                for framing in result['reader_guidance']['alternative_framings'][:4]:
                    st.markdown(f"• {framing}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Framing-specific tips
            st.markdown("**💡 What This Means:**")
            st.markdown("""
            - **Framing** shapes how you interpret events before you even form an opinion
            - **Multiple perspectives** on the same facts can be equally valid
            - **Balanced articles** acknowledge complexity and competing viewpoints
            """)
        
        with tab3:
            st.info("**📝 Focus**: This tab identifies missing background information, omitted facts, and incomplete narratives.")
            
            # Missing context
            st.markdown('<div class="error-box"><h4>❓ Missing Context Detection</h4>', unsafe_allow_html=True)
            
            if detailed.get('missing_context'):
                for context in detailed['missing_context']:
                    st.markdown(f"⚠️ {context}")
            else:
                st.success("✅ No obvious missing context detected")
            
            st.markdown('</div>', unsafe_allow_html=True)
            
            # Critical questions section - unique to this tab
            if result.get('reader_guidance', {}).get('critical_questions'):
                st.markdown('<div class="info-box"><h4>❓ Important Questions to Ask</h4>', unsafe_allow_html=True)
                # Filter for context-related questions
                all_questions = result['reader_guidance']['critical_questions']
                context_questions = [q for q in all_questions if any(word in q.lower() for word in ['context', 'background', 'history', 'why', 'what', 'when', 'where'])]
                
                for question in (context_questions or all_questions)[:5]:
                    st.markdown(f"• {question}")
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Context-specific tips
            st.markdown("**💡 What This Means:**")
            st.markdown("""
            - **Missing context** can make stories misleading even if facts are accurate
            - **Background information** helps you understand why events matter
            - **Complete stories** include historical context, multiple stakeholders, and consequences
            """)
        
        with tab4:
            st.info("**📝 Focus**: This tab analyzes factual certainty, evidence strength, and claims vs. speculation.")
            
            # Technical analysis
            modality = detailed.get('modality_analysis', {})
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown('<div class="synthesis-box"><h4>📊 Certainty Analysis</h4>', unsafe_allow_html=True)
                
                certainty_level = modality.get('certainty_level', 'unknown')
                certainty_color = {"high": "🔴", "medium": "🟡", "low": "🟢", "unknown": "⚪"}.get(certainty_level, "⚪")
                
                st.markdown(f"**Certainty Level:** {certainty_color} {certainty_level.title()}")
                st.markdown(f"**Assertion Strength:** {modality.get('assertion_strength', 'unknown').title()}")
                
                if modality.get('speculation_markers'):
                    st.markdown("**Speculation markers found:**")
                    markers_text = ", ".join(modality['speculation_markers'][:8])
                    st.code(markers_text, language=None)
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            with col2:
                st.markdown('<div class="comparison-box"><h4>🔍 Evidence Assessment</h4>', unsafe_allow_html=True)
                
                # Show source reliability if available
                source_context = result.get('source_context', 'Unknown source')
                st.markdown(f"**Source:** {source_context}")
                
                # Show confidence level
                confidence = result.get('confidence_level', result.get('confidence', 0))
                confidence_color = "🟢" if confidence > 80 else "🟡" if confidence > 60 else "🔴"
                st.markdown(f"**Analysis Confidence:** {confidence_color} {confidence}%")
                
                # Show evidence quality indicators
                if result.get('explainability', {}).get('bias_evidence'):
                    evidence_count = len(result['explainability']['bias_evidence'])
                    st.markdown(f"**Evidence Points Found:** {evidence_count}")
                
                st.markdown('</div>', unsafe_allow_html=True)
            
            # Technical-specific tips
            st.markdown("**💡 What This Means:**")
            st.markdown("""
            - **High certainty** with weak evidence suggests overconfidence or bias
            - **Speculation markers** ("might", "could", "possibly") indicate uncertainty
            - **Strong evidence** includes data, expert sources, and verifiable facts
            """)
    
    # === ACTIONABLE RECOMMENDATIONS ===
    if result.get('reader_guidance') or result.get('explainability'):
        st.markdown("### 🎯 Key Takeaways & Next Steps")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown('<div class="success-box"><h4>✅ What to Do</h4>', unsafe_allow_html=True)
            
            # Show neutrality suggestions if available
            if result.get('explainability', {}).get('neutrality_suggestions'):
                st.markdown("**To get more balanced information:**")
                for suggestion in result['explainability']['neutrality_suggestions'][:3]:
                    st.markdown(f"• {suggestion}")
            else:
                st.markdown("""
                • Seek additional sources with different perspectives
                • Look for primary sources and original documents  
                • Check if competing viewpoints are fairly represented
                """)
            
            st.markdown('</div>', unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="info-box"><h4>📚 Recommended Sources</h4>', unsafe_allow_html=True)
            
            if result.get('reader_guidance', {}).get('suggested_sources'):
                for source in result['reader_guidance']['suggested_sources'][:4]:
                    st.markdown(f"• {source}")
            else:
                st.markdown("""
                • Fact-checking sites (Snopes, FactCheck.org, PolitiFact)
                • Primary sources (government data, research papers)
                • News aggregators showing multiple perspectives
                • Subject matter experts on social media/blogs
                """)
            
            st.markdown('</div>', unsafe_allow_html=True)
    
    # === EXPLAINABILITY & NEUTRALITY ===
    if result.get('explainability'):
        st.markdown("### 🛠️ Transparency & Improvement Suggestions")
        
        explainability = result['explainability']
        
        # Bias evidence
        if explainability.get('bias_evidence'):
            with st.expander("📋 Specific Evidence of Bias"):
                for evidence in explainability['bias_evidence']:
                    if isinstance(evidence, str):
                        st.markdown(f"• {evidence}")
                    else:
                        st.markdown(f"• {evidence.get('text', 'Unknown evidence')}")
        
        # Neutrality suggestions
        if explainability.get('neutrality_suggestions'):
            with st.expander("✏️ How to Make This More Neutral"):
                for suggestion in explainability['neutrality_suggestions']:
                    st.info(f"💡 {suggestion}")
    
    # === LEGACY SUPPORT ===
    # Handle old format results for backward compatibility
    if not result.get('detailed_analysis') and result.get('bias_indicators'):
        st.markdown("### 🔍 Basic Bias Indicators")
        for indicator in result['bias_indicators']:
            st.markdown(f"• {indicator}")
    
    if not result.get('reader_guidance') and result.get('recommendations'):
        st.markdown("### 💡 Interpretation Guide")
        st.info(result['recommendations'])


def highlight_biased_text(original_text: str, biased_phrases: list, max_length: int = 2000) -> str:
    """Create HTML highlighted version of text showing biased phrases"""
    
    # Limit text length for display
    display_text = original_text[:max_length]
    if len(original_text) > max_length:
        display_text += "..."
    
    highlighted_text = display_text
    
    # Color mapping for different bias types
    color_map = {
        'emotional': '#ffcccc',      # Light red
        'negative_political': '#ffdddd',
        'positive_political': '#ddffdd',
        'negative_moral': '#ffe6e6',
        'positive_moral': '#e6ffe6',
        'anger': '#ff9999',
        'fear': '#ffcc99',
        'moral_outrage': '#ff6666',
        'contempt': '#cc99ff'
    }
    
    # Sort phrases by length (longest first) to avoid nested highlighting issues
    sorted_phrases = sorted(biased_phrases, key=lambda x: len(x.get('text', '') if isinstance(x, dict) else str(x)), reverse=True)
    
    for phrase_info in sorted_phrases[:20]:  # Limit to prevent performance issues
        if isinstance(phrase_info, dict):
            phrase = phrase_info.get('text', '')
            bias_type = phrase_info.get('bias_type', 'emotional')
            intensity = phrase_info.get('intensity', 5)
        else:
            phrase = str(phrase_info)
            bias_type = 'emotional'
            intensity = 5
        
        if phrase and phrase in highlighted_text:
            # Use color based on bias type, intensity affects opacity
            color = color_map.get(bias_type, '#ffcccc')
            opacity = min(0.9, 0.3 + (intensity * 0.1))  # Range 0.3 to 0.9
            
            # Create highlighted version
            highlighted_phrase = f'<mark style="background-color: {color}; opacity: {opacity}; padding: 2px 4px; border-radius: 3px;" title="{bias_type} (intensity: {intensity})">{phrase}</mark>'
            highlighted_text = highlighted_text.replace(phrase, highlighted_phrase, 1)  # Replace only first occurrence
    
    return highlighted_text


def display_highlighted_text(original_text: str, result: dict):
    """Display original text with bias highlighting"""
    
    if not result.get('detailed_analysis', {}).get('biased_phrases'):
        return
    
    st.markdown("### 🎨 Text Visualization")
    st.markdown("*Biased phrases are highlighted. Hover over highlights to see bias type and intensity.*")
    
    biased_phrases = result['detailed_analysis']['biased_phrases']
    highlighted_html = highlight_biased_text(original_text, biased_phrases)
    
    # Display in a styled container
    st.markdown(
        f"""
        <div style="
            border: 1px solid #ddd; 
            border-radius: 8px; 
            padding: 15px; 
            background-color: #fafafa; 
            max-height: 400px; 
            overflow-y: auto;
            line-height: 1.6;
            font-family: 'Arial', sans-serif;
        ">
            {highlighted_html}
        </div>
        """, 
        unsafe_allow_html=True
    )
    
    # Add legend
    st.markdown("**Legend:**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<span style="background-color: #ffcccc; padding: 2px 8px; border-radius: 3px;">Emotional Language</span>', unsafe_allow_html=True)
        st.markdown('<span style="background-color: #ff9999; padding: 2px 8px; border-radius: 3px;">High Intensity</span>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<span style="background-color: #ffdddd; padding: 2px 8px; border-radius: 3px;">Political Language</span>', unsafe_allow_html=True)
        st.markdown('<span style="background-color: #ffe6e6; padding: 2px 8px; border-radius: 3px;">Moral Language</span>', unsafe_allow_html=True)
    
    with col3:
        st.markdown("💡 *Darker colors = Higher intensity*")
        st.markdown("🎯 *Hover over highlights for details*")


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
                ["Direct Text Input", "File Upload", "URL Input"],
                horizontal=True
            )
            
            text_content = ""
            
            if input_method == "Direct Text Input":
                text_content = st.text_area(
                    "Enter or paste your article here:",
                    height=300,
                    placeholder="Paste your article text here for analysis..."
                )
            elif input_method == "File Upload":
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
            else:  # URL Input
                url_input = st.text_input(
                    "Enter article URL:",
                    placeholder="https://example.com/article or example.com/article",
                    help="Enter the URL of the article you want to analyze"
                )
                
                if url_input:
                    # Clean and validate URL
                    clean_url, error = validate_and_clean_url(url_input)
                    
                    if error:
                        st.error(error)
                        text_content = ""
                    else:
                        # Add a button to fetch the article
                        if st.button("🔗 Fetch Article", type="secondary", use_container_width=True):
                            with st.spinner("Fetching article content..."):
                                result = fetch_article_from_url(clean_url)
                                
                                if result['success']:
                                    text_content = result['content']
                                    st.success(f"✅ Article fetched successfully!")
                                    st.info(f"**Title:** {result['title']}")
                                    
                                    # Show preview
                                    with st.expander("📋 Article Preview"):
                                        st.text(text_content[:1000] + "..." if len(text_content) > 1000 else text_content)
                                    
                                    # Store in session state so it persists
                                    st.session_state['fetched_content'] = text_content
                                    st.session_state['fetched_title'] = result['title']
                                    st.session_state['fetched_url'] = clean_url
                                else:
                                    st.error(f"❌ Failed to fetch article: {result['error']}")
                                    if result['content']:
                                        st.warning("Partial content was extracted:")
                                        st.text(result['content'][:500] + "...")
                                    text_content = ""
                        else:
                            # Check if we have previously fetched content
                            if 'fetched_content' in st.session_state:
                                text_content = st.session_state['fetched_content']
                                st.info(f"Using previously fetched article: **{st.session_state.get('fetched_title', 'Unknown')}**")
                            else:
                                text_content = ""
                else:
                    text_content = ""
            
            # Additional metadata for enhanced bias analysis
            if analysis_mode in ["Bias Analysis", "Full Report"]:
                st.markdown("### 📋 Article Metadata (Optional - Enhances Bias Analysis)")
                col1, col2 = st.columns(2)
                
                with col1:
                    article_title = st.text_input(
                        "Article Title",
                        placeholder="Enter the article headline/title",
                        help="Helps with contextual analysis"
                    )
                
                with col2:
                    source_url = st.text_input(
                        "Source URL or Domain",
                        placeholder="e.g., cnn.com, foxnews.com, reuters.com",
                        help="Enables source bias profiling and publisher context"
                    )
            else:
                article_title = None
                source_url = None
            
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
                                result = engine.analyze_single_article(text_content, mode='summary', source_url=source_url, article_title=article_title)
                            elif analysis_mode == "Bias Analysis":
                                result = engine.analyze_single_article(text_content, mode='bias', source_url=source_url, article_title=article_title)
                            elif analysis_mode == "Full Report":
                                result = engine.analyze_single_article(text_content, mode='full', source_url=source_url, article_title=article_title)
                            
                            # Store results
                            st.session_state.last_results = {
                                'type': analysis_mode,
                                'data': result,
                                'original_text': text_content  # Store original text for highlighting
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
                    # Add highlighted text visualization for bias analysis
                    if st.session_state.last_results.get('original_text'):
                        display_highlighted_text(st.session_state.last_results['original_text'], result_data)
                elif result_type == "Full Report":
                    if result_data.get('summary'):
                        format_summary_display(result_data['summary'])
                    if result_data.get('bias_analysis'):
                        display_bias_analysis(result_data['bias_analysis'])
                        # Add highlighted text visualization for full report bias analysis
                        if st.session_state.last_results.get('original_text'):
                            display_highlighted_text(st.session_state.last_results['original_text'], result_data['bias_analysis'])
                
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