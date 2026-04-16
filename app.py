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
    """Display enhanced bias analysis results with comprehensive visualizations."""
    if not result or result.get('error'):
        st.error(f"Bias analysis failed: {result.get('error', 'Unknown error')}")
        return
    
    st.markdown('<div class="section-header">🎯 Enhanced Bias Analysis</div>', unsafe_allow_html=True)
    
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
            # Biased phrases and emotional analysis
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown("**🚨 Biased Phrases Detected:**")
                if detailed.get('biased_phrases'):
                    for phrase in detailed['biased_phrases'][:10]:  # Limit display
                        if isinstance(phrase, dict):
                            intensity_color = "🔴" if phrase.get('intensity', 0) > 7 else "🟡" if phrase.get('intensity', 0) > 4 else "🟢"
                            st.markdown(f"{intensity_color} **\"{phrase.get('text', '')}\"** - {phrase.get('bias_type', 'unknown')} (intensity: {phrase.get('intensity', 0)}/10)")
                        else:
                            st.markdown(f"• {phrase}")
                else:
                    st.success("No significantly biased phrases detected")
            
            with col2:
                st.markdown("**😤 Emotional Analysis:**")
                emotion_analysis = detailed.get('emotion_analysis', {})
                
                dominant_tone = emotion_analysis.get('dominant_tone', 'neutral')
                tone_emoji = {"anger": "😠", "fear": "😰", "moral_outrage": "😤", "contempt": "🙄", "neutral": "😐"}.get(dominant_tone, "😐")
                
                st.markdown(f"**Dominant Tone:** {tone_emoji} {dominant_tone.replace('_', ' ').title()}")
                
                if emotion_analysis.get('emotional_targets'):
                    st.markdown("**Emotional targets:**")
                    for target in emotion_analysis['emotional_targets'][:5]:
                        st.markdown(f"• {target}")
                
                author_vs_quoted = emotion_analysis.get('author_vs_quoted', 'unknown')
                if author_vs_quoted != 'unknown':
                    st.markdown(f"**Source of emotion:** {author_vs_quoted}")
            
            # Tab-specific Reader Guidance for Language & Emotion
            if result.get('reader_guidance'):
                st.markdown("---")
                st.markdown("### 🧭 Language Analysis Guidance")
                guidance = result['reader_guidance']
                
                if guidance.get('key_concerns'):
                    st.markdown("**⚠️ Key Language Concerns:**")
                    language_concerns = [c for c in guidance['key_concerns'] if any(word in c.lower() for word in ['language', 'emotion', 'tone', 'phrase', 'word'])]
                    for concern in language_concerns[:3]:
                        st.warning(f"• {concern}")
                
                if guidance.get('critical_questions'):
                    st.markdown("**❓ Questions About Language Use:**")
                    language_questions = [q for q in guidance['critical_questions'] if any(word in q.lower() for word in ['language', 'emotion', 'tone', 'phrase', 'word'])]
                    for question in language_questions[:3]:
                        st.info(f"• {question}")
        
        with tab2:
            # Framing issues
            st.markdown("**🎭 Framing Analysis:**")
            
            if detailed.get('framing_issues'):
                for issue in detailed['framing_issues']:
                    if isinstance(issue, dict):
                        st.warning(f"**{issue.get('type', 'Unknown').replace('_', ' ').title()}**: {issue.get('description', 'No description')}")
                    else:
                        st.warning(f"• {issue}")
            else:
                st.success("No significant framing issues detected")
            
            # Tab-specific Reader Guidance for Framing
            if result.get('reader_guidance'):
                st.markdown("---")
                st.markdown("### 🧭 Framing Analysis Guidance")
                guidance = result['reader_guidance']
                
                if guidance.get('alternative_framings'):
                    st.markdown("**🔄 Alternative Perspectives to Consider:**")
                    for framing in guidance['alternative_framings'][:4]:
                        st.success(f"• {framing}")
                
                if guidance.get('suggested_sources'):
                    st.markdown("**🔍 Sources for Different Framings:**")
                    framing_sources = [s for s in guidance['suggested_sources'] if any(word in s.lower() for word in ['perspective', 'view', 'angle', 'frame'])]
                    for source in (framing_sources or guidance['suggested_sources'])[:3]:
                        st.markdown(f"• {source}")
        
        with tab3:
            # Missing context
            st.markdown("**❓ Missing Context Detection:**")
            
            if detailed.get('missing_context'):
                for context in detailed['missing_context']:
                    st.warning(f"⚠️ {context}")
            else:
                st.success("No obvious missing context detected")
            
            # Tab-specific Reader Guidance for Missing Context
            if result.get('reader_guidance'):
                st.markdown("---")
                st.markdown("### 🧭 Context Analysis Guidance")
                guidance = result['reader_guidance']
                
                if guidance.get('critical_questions'):
                    st.markdown("**❓ Important Context Questions:**")
                    context_questions = [q for q in guidance['critical_questions'] if any(word in q.lower() for word in ['context', 'background', 'history', 'why', 'what'])]
                    for question in (context_questions or guidance['critical_questions'])[:4]:
                        st.info(f"• {question}")
                
                if guidance.get('suggested_sources'):
                    st.markdown("**📚 Sources for Additional Context:**")
                    context_sources = [s for s in guidance['suggested_sources'] if any(word in s.lower() for word in ['context', 'background', 'history'])]
                    for source in (context_sources or guidance['suggested_sources'])[:3]:
                        st.markdown(f"• {source}")
        
        with tab4:
            # Technical analysis
            modality = detailed.get('modality_analysis', {})
            
            st.markdown("**📊 Certainty vs Speculation Analysis:**")
            
            certainty_level = modality.get('certainty_level', 'unknown')
            certainty_color = {"high": "🔴", "medium": "🟡", "low": "🟢", "unknown": "⚪"}.get(certainty_level, "⚪")
            
            st.markdown(f"**Certainty Level:** {certainty_color} {certainty_level.title()}")
            st.markdown(f"**Assertion Strength:** {modality.get('assertion_strength', 'unknown').title()}")
            
            if modality.get('speculation_markers'):
                st.markdown("**Speculation markers found:**")
                st.code(", ".join(modality['speculation_markers'][:10]))
            
            # Tab-specific Reader Guidance for Technical Analysis
            if result.get('reader_guidance'):
                st.markdown("---")
                st.markdown("### 🧭 Technical Analysis Guidance")
                guidance = result['reader_guidance']
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if guidance.get('key_concerns'):
                        st.markdown("**⚠️ Technical Concerns:**")
                        tech_concerns = [c for c in guidance['key_concerns'] if any(word in c.lower() for word in ['certainty', 'speculation', 'evidence', 'fact', 'claim'])]
                        for concern in (tech_concerns or guidance['key_concerns'])[:3]:
                            st.warning(f"• {concern}")
                
                with col2:
                    if guidance.get('critical_questions'):
                        st.markdown("**❓ Evidence Questions:**")
                        evidence_questions = [q for q in guidance['critical_questions'] if any(word in q.lower() for word in ['evidence', 'prove', 'fact', 'claim', 'certain'])]
                        for question in (evidence_questions or guidance['critical_questions'])[:3]:
                            st.info(f"• {question}")
    
    # === OVERALL READER GUIDANCE ===
    # Note: Tab-specific guidance is now shown within each tab
    # This section shows overall guidance that applies to all aspects
    if result.get('reader_guidance'):
        st.markdown("### 🧭 Overall Analysis Summary")
        
        guidance = result['reader_guidance']
        
        # Show only the most general, overarching guidance here
        if guidance.get('key_concerns'):
            general_concerns = [c for c in guidance['key_concerns'] if not any(word in c.lower() for word in ['language', 'emotion', 'framing', 'context', 'certainty'])]
            if general_concerns:
                st.markdown("**⚠️ Overall Key Concerns:**")
                for concern in general_concerns[:2]:
                    st.warning(f"• {concern}")
        
        # Show publication context and overall source reliability
        if guidance.get('suggested_sources'):
            general_sources = [s for s in guidance['suggested_sources'] if not any(word in s.lower() for word in ['perspective', 'framing', 'context', 'background'])]
            if general_sources:
                st.markdown("**🔍 Additional Sources for Verification:**")
                for source in general_sources[:2]:
                    st.markdown(f"• {source}")
    
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