#!/usr/bin/env python3
"""
Streamlit Web UI for TextSummarizer
A modern web interface for the TextSummarizer CLI tool.
"""

import streamlit as st
import tempfile
import os
from datetime import datetime
from pathlib import Path
import json
import traceback

# Import existing summarizer components
from summarizer import TextSummarizer
from config import Config

# Page configuration
st.set_page_config(
    page_title="Text Summarizer",
    page_icon="📝",
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
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables."""
    if 'config' not in st.session_state:
        st.session_state.config = None
    if 'summarizer' not in st.session_state:
        st.session_state.summarizer = None
    if 'last_summary' not in st.session_state:
        st.session_state.last_summary = None


def setup_sidebar():
    """Setup sidebar with configuration options."""
    st.sidebar.markdown("## ⚙️ Configuration")
    
    # Model selection
    model_options = ["openai", "anthropic", "local"]
    selected_model = st.sidebar.selectbox(
        "Select AI Model",
        options=model_options,
        index=0,
        help="Choose the AI model for summarization"
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


def validate_inputs(text_content, selected_model, settings):
    """Validate user inputs before processing."""
    if not text_content.strip():
        st.error("Please provide some text to summarize.")
        return False
    
    if len(text_content.strip()) < 50:
        st.warning("Text seems quite short. You might get better results with longer text.")
    
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
    """Main Streamlit application."""
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">📝 Text Summarizer</h1>', unsafe_allow_html=True)
    st.markdown("Transform long texts into concise summaries with AI-powered analysis")
    
    # Setup sidebar
    settings = setup_sidebar()
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("## 📄 Input Text")
        
        # Input method selection
        input_method = st.radio(
            "Choose input method:",
            ["Direct Text Input", "File Upload"],
            horizontal=True
        )
        
        text_content = ""
        
        if input_method == "Direct Text Input":
            text_content = st.text_area(
                "Enter or paste your text here:",
                height=300,
                placeholder="Paste your text here for summarization..."
            )
        else:
            uploaded_file = st.file_uploader(
                "Choose a text file",
                type=['txt', 'md', 'py', 'js', 'html', 'css', 'json'],
                help="Upload a text file to summarize"
            )
            
            if uploaded_file is not None:
                try:
                    # Read file content
                    text_content = str(uploaded_file.read(), "utf-8")
                    st.success(f"File '{uploaded_file.name}' loaded successfully!")
                    
                    # Show preview
                    with st.expander("📋 File Preview"):
                        st.text(text_content[:1000] + "..." if len(text_content) > 1000 else text_content)
                        
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
        
        # Process button
        if st.button("🚀 Generate Summary", type="primary", use_container_width=True):
            if validate_inputs(text_content, settings['model'], settings):
                with st.spinner("Generating summary..."):
                    try:
                        # Create configuration
                        config = create_temp_config(settings)
                        if not config:
                            return
                        
                        # Initialize summarizer
                        summarizer = TextSummarizer(
                            model_type=settings['model'], 
                            config=config, 
                            verbose=settings['verbose_mode']
                        )
                        
                        # Generate summary
                        result = summarizer.summarize(text_content)
                        
                        # Store in session state
                        st.session_state.last_summary = result
                        
                        # Save to file if requested
                        if settings['save_output']:
                            filepath = save_results_to_file(result, settings)
                            if filepath:
                                st.success(f"Results saved to: {filepath}")
                        
                        st.success("Summary generated successfully!")
                        
                    except Exception as e:
                        st.error(f"Error generating summary: {str(e)}")
                        if settings['verbose_mode']:
                            st.code(traceback.format_exc())
    
    with col2:
        st.markdown("## ℹ️ Information")
        
        st.markdown("""
        ### How to use:
        1. **Choose input method**: Direct text or file upload
        2. **Select AI model** in the sidebar
        3. **Configure API keys** (if needed)
        4. **Click Generate Summary**
        
        ### Supported models:
        - **OpenAI**: GPT-3.5-turbo (requires API key)
        - **Anthropic**: Claude-3-haiku (requires API key)
        - **Local**: No API key needed (basic extraction)
        
        ### Features:
        - 📝 Concise summaries
        - 🔑 Key points extraction
        - ✅ Action items identification
        - 💾 Auto-save results
        - 📥 Download functionality
        """)
    
    # Results section
    if st.session_state.last_summary:
        st.markdown("---")
        st.markdown("## 📊 Results")
        
        # Display formatted results
        format_summary_display(st.session_state.last_summary)
        
        # Download section
        st.markdown("---")
        st.markdown("## 📥 Export")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            # Download as text
            download_content = create_download_content(st.session_state.last_summary)
            st.download_button(
                label="📄 Download as Text",
                data=download_content,
                file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                mime="text/plain"
            )
        
        with col2:
            # Download as JSON (if result is structured)
            if isinstance(st.session_state.last_summary, dict):
                json_content = json.dumps(st.session_state.last_summary, indent=2, ensure_ascii=False)
                st.download_button(
                    label="📋 Download as JSON",
                    data=json_content,
                    file_name=f"summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
        
        with col3:
            # Clear results
            if st.button("🗑️ Clear Results"):
                st.session_state.last_summary = None
                st.rerun()
    
    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #666666; padding: 1rem;'>
            Built with ❤️ using Streamlit | TextSummarizer v1.0
        </div>
        """,
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()