# Text Summarizer

A powerful tool for summarizing text using AI models, available as both a **web interface** and **command-line tool**. Supports multiple AI providers (OpenAI, Anthropic) and local processing for privacy-conscious users.

## Features

- 📝 **Multiple input methods**: File, direct text, or stdin
- 🤖 **Multiple AI providers**: OpenAI GPT, Anthropic Claude, or local processing
- 📊 **Structured output**: Short summary, key bullet points, and action items
- 💾 **Save results**: Automatic file saving with timestamps
- ⚙️ **Configurable**: Environment variables or config file setup
- 🔒 **Privacy options**: Local processing mode requires no API keys

## Installation

1. **Clone or download the files**:
   ```bash
   cd TextSummarizer
   ```

2. **Install dependencies** (choose based on your preferred AI provider):
   ```bash
   # Install all dependencies (includes web UI)
   pip install -r requirements.txt
   
   # OR install selectively:
   
   # For web interface
   pip install streamlit
   
   # For OpenAI support
   pip install openai
   
   # For Anthropic support  
   pip install anthropic
   
   # For local mode only (no additional dependencies needed)
   # The tool works with Python standard library
   ```

3. **Set up API keys** (optional, not needed for local mode):
   ```bash
   # Option 1: Environment variables (recommended)
   export OPENAI_API_KEY="your_openai_api_key"
   export ANTHROPIC_API_KEY="your_anthropic_api_key"
   
   # Option 2: Interactive setup
   python main.py --setup
   ```

## Quick Start

### 🌐 Web Interface (Recommended for Beginners)

```bash
# Install dependencies
pip install streamlit

# Launch the web interface
streamlit run app.py
```

Then open your browser to the URL shown (typically `http://localhost:8501`) and enjoy the intuitive web interface!

### 💻 Command Line Interface

```bash
# Summarize a file
python main.py --file document.txt

# Summarize direct text
python main.py --text "Your long text here..."

# Summarize from stdin
echo "Text content" | python main.py
cat document.txt | python main.py

# Use local processing (no API key needed)
python main.py --file document.txt --model local
```

## Usage Examples

### Basic Usage

```bash
# Summarize a document and save to file
python main.py --file research_paper.txt --output summary.txt

# Quick text summary without saving
python main.py --text "Long text..." --no-save

# Verbose output to see what's happening
python main.py --file document.txt --verbose
```

### Advanced Options

```bash
# Use different AI models
python main.py --file document.txt --model openai      # Default
python main.py --file document.txt --model anthropic   # Anthropic Claude
python main.py --file document.txt --model local       # Local processing

# Control summary length
python main.py --file document.txt --max-length 200

# Combine options
python main.py --file input.txt --model anthropic --max-length 100 --output result.txt --verbose
```

### Pipe Usage

```bash
# From curl
curl -s https://example.com/article | python main.py

# From other commands
cat *.txt | python main.py --output combined_summary.txt

# Process multiple files
for file in *.txt; do
    python main.py --file "$file" --output "summary_$(basename "$file")"
done
```

## Configuration

### Method 1: Environment Variables (Recommended)

```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
export OPENAI_API_KEY="sk-your-key-here"
export ANTHROPIC_API_KEY="your-anthropic-key"
export SUMMARIZER_DEFAULT_MODEL="openai"
export SUMMARIZER_MAX_LENGTH="150"
```

### Method 2: Configuration File

```bash
# Run interactive setup
python main.py --setup

# Or manually create ~/.text_summarizer_config:
openai_api_key=sk-your-key-here
anthropic_api_key=your-anthropic-key
default_model=openai
default_max_length=150
```

## API Keys Setup

### OpenAI API Key
1. Visit https://platform.openai.com/api-keys
2. Create an account and generate an API key
3. Set the `OPENAI_API_KEY` environment variable

### Anthropic API Key
1. Visit https://console.anthropic.com/
2. Create an account and generate an API key  
3. Set the `ANTHROPIC_API_KEY` environment variable

### Local Mode (No API Key)
Use `--model local` for basic text processing without external APIs. Results are simpler but require no setup.

## Output Format

The tool generates structured summaries with three sections:

```
📝 SHORT SUMMARY
Brief overview of the text content...

🔑 KEY POINTS  
1. First important point
2. Second key insight
3. Third significant detail

✅ ACTION ITEMS
1. Task or action mentioned in text
2. Follow-up item to consider
```

## Command Line Options

```
positional arguments:
  None

options:
  -h, --help            show this help message and exit

Input options:
  --file FILE, -f FILE  Input text file to summarize
  --text TEXT, -t TEXT  Direct text input to summarize

Output options:
  --output OUTPUT, -o OUTPUT
                        Output file path (default: auto-generated filename)
  --no-save            Display results only, do not save to file

Model options:
  --model {openai,anthropic,local}
                        AI model to use (default: openai)
  --max-length MAX_LENGTH
                        Maximum length for summary (default: 150 words)

Other options:
  --verbose, -v         Verbose output
  --setup              Run configuration setup
```

## Examples by Use Case

### Research Papers
```bash
python main.py --file research_paper.pdf.txt --model openai --max-length 200 --output research_summary.txt
```

### Meeting Notes
```bash
python main.py --file meeting_transcript.txt --model anthropic --output meeting_actions.txt
```

### Articles/Blog Posts
```bash
curl -s https://example.com/article.html | html2text | python main.py --no-save
```

### Email Threads
```bash
python main.py --text "Long email thread..." --max-length 100 --output email_summary.txt
```

## Troubleshooting

### API Key Issues
```bash
# Check if API key is set
echo $OPENAI_API_KEY

# Test with local mode
python main.py --model local --text "Test text"

# Run setup
python main.py --setup
```

### Import Errors
```bash
# Install missing dependencies
pip install openai anthropic

# Check Python version (3.7+ required)
python --version
```

### File Issues
```bash
# Check file exists and is readable
ls -la your_file.txt
cat your_file.txt | head

# Try with verbose mode
python main.py --file your_file.txt --verbose
```

## Privacy & Security

- **Local Mode**: Use `--model local` for completely offline processing
- **API Keys**: Store securely, never commit to version control
- **Data**: Text is sent to AI providers only when using their APIs
- **Logs**: No sensitive data is logged by the tool

## Contributing

Feel free to enhance this tool! Areas for improvement:

- Additional AI providers
- Better local processing algorithms
- Output format options (JSON, XML, etc.)
- Batch processing features
- Web interface

## License

This tool is provided as-is for educational and personal use. Please comply with the terms of service of any AI providers you use.

## Support

For issues or questions:

1. Check this README for common solutions
2. Try `--verbose` mode for detailed output
3. Test with `--model local` to isolate API issues
4. Verify API keys and network connectivity