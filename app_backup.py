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


def extract_topics_from_article(content, title, settings):
    """
    Enhanced topic extraction using AI summarization.
    Analyzes the full article content to extract key themes and search terms.
    """
    try:
        # Create a temporary config and analysis engine
        config = create_temp_config(settings)
        engine = AnalysisEngine(
            model_type=settings['model'], 
            config=config, 
            verbose=False  # Keep it quiet for topic extraction
        )
        
        # Step 1: Generate a focused summary to identify main themes
        summary_prompt = f"""
        Analyze this article and provide:
        1. A concise 2-3 sentence summary of the main topic
        2. 3-5 key themes/concepts that best represent what this article is about
        3. Optimal search terms that would find related articles on the same topic
        
        Article Title: {title}
        
        Article Content: {content[:2000]}...  # Use first 2000 chars
        
        Format your response as:
        SUMMARY: [your summary]
        THEMES: [theme1, theme2, theme3, ...]  
        SEARCH_TERMS: [optimized search phrase]
        """
        
        # Get AI analysis
        result = engine.generate_response(summary_prompt, content[:2000])
        
        if result and result.get('success', False):
            response_text = result['response']
            
            # Parse the structured response
            summary = ""
            themes = []
            search_terms = title  # Fallback to title
            
            lines = response_text.split('\n')
            for line in lines:
                line = line.strip()
                if line.startswith('SUMMARY:'):
                    summary = line.replace('SUMMARY:', '').strip()
                elif line.startswith('THEMES:'):
                    themes_text = line.replace('THEMES:', '').strip()
                    themes = [theme.strip() for theme in themes_text.split(',')]
                elif line.startswith('SEARCH_TERMS:'):
                    search_terms = line.replace('SEARCH_TERMS:', '').strip()
            
            # Clean up search terms
            search_terms = search_terms.replace('"', '').replace("'", "")
            
            return {
                'success': True,
                'summary': summary or "AI analysis completed",
                'themes': themes or ["topic extracted"],
                'search_terms': search_terms
            }
        else:
            # Fallback: use title-based extraction
            return {
                'success': False,
                'error': 'AI analysis failed',
                'summary': title,
                'themes': [title],
                'search_terms': title
            }
            
    except Exception as e:
        # Fallback: use title-based extraction  
        return {
            'success': False,
            'error': f'Topic extraction error: {str(e)}',
            'summary': title,
            'themes': [title], 
            'search_terms': title
        }


def search_related_articles(topic, num_articles=6):
    """
    Search for related articles on a topic from diverse sources.
    Returns list of article URLs and basic metadata.
    """
    try:
        # Use multiple search strategies
        articles = []
        
        # Strategy 1: Use Bing News Search (no API key required)
        bing_results = search_bing_news(topic, num_articles//2)
        articles.extend(bing_results)
        
        # Strategy 2: Use RSS feeds from major news sources
        rss_results = search_rss_feeds(topic, num_articles//2)
        articles.extend(rss_results)
        
        # Remove duplicates based on URL domain and sort by relevance
        unique_articles = []
        seen_domains = set()
        
        # Sort all articles by relevance score if available
        all_articles = sorted(articles, key=lambda x: x.get('relevance_score', 0), reverse=True)
        
        for article in all_articles[:num_articles*2]:  # Check more articles for better selection
            domain = urlparse(article['url']).netloc.lower()
            # Remove www. for comparison
            domain = domain.replace('www.', '')
            
            if domain not in seen_domains:
                seen_domains.add(domain)
                unique_articles.append(article)
                
                if len(unique_articles) >= num_articles:
                    break
        
        return unique_articles[:num_articles]
        
    except Exception as e:
        st.warning(f"Search error: {str(e)}")
        return []


def search_bing_news(topic, num_results=3):
    """Search Bing News without requiring API key (using web scraping)."""
    try:
        # Construct Bing News search URL
        query = topic.replace(' ', '+')
        url = f"https://www.bing.com/news/search?q={query}&form=HDRSC1"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # Find news articles in Bing results
        news_cards = soup.find_all('div', class_='news-card') or soup.find_all('article')
        
        for card in news_cards[:num_results]:
            try:
                # Try to extract article URL and title
                link_elem = card.find('a', href=True)
                if link_elem and link_elem.get('href'):
                    article_url = link_elem.get('href')
                    
                    # Skip Bing redirect URLs, try to get direct URLs
                    if 'bing.com' in article_url:
                        continue
                        
                    title_elem = link_elem.find(text=True) or card.find('h2') or card.find('h3')
                    title = title_elem.get_text().strip() if title_elem else "Unknown Article"
                    
                    # Try to identify source
                    source_elem = card.find('span', class_='source') or card.find('cite')
                    source = source_elem.get_text().strip() if source_elem else urlparse(article_url).netloc
                    
                    articles.append({
                        'url': article_url,
                        'title': title,
                        'source': source,
                        'search_method': 'bing_news'
                    })
            except Exception:
                continue
                
        return articles
        
    except Exception:
        return []


def search_rss_feeds(topic, num_results=3):
    """Search RSS feeds from major news sources."""
    try:
        # Major news RSS feeds - expanded for better diversity
        rss_feeds = [
            'https://feeds.bbci.co.uk/news/rss.xml',  # BBC News
            'https://rss.cnn.com/rss/edition.rss',    # CNN  
            'https://www.npr.org/rss/rss.php?id=1001', # NPR
            'https://feeds.reuters.com/reuters/topNews', # Reuters
            'https://feeds.a.dj.com/rss/RSSWorldNews.xml', # Wall Street Journal
            'https://feeds.washingtonpost.com/rss/world', # Washington Post
            'https://www.politico.com/rss/politics08.xml', # Politico
            'https://rss.foxnews.com/foxnews/politics',  # Fox News
            'https://feeds.feedburner.com/time/topstories', # Time
            'https://feeds.nbcnews.com/nbcnews/public/news', # NBC News
        ]
        
        articles = []
        search_terms = topic.lower().split()
        
        for feed_url in rss_feeds:
            try:
                response = requests.get(feed_url, timeout=5)
                soup = BeautifulSoup(response.content, 'xml')
                
                items = soup.find_all('item')[:10]  # Check recent items
                
                for item in items:
                    title_elem = item.find('title')
                    link_elem = item.find('link')
                    
                    if title_elem and link_elem:
                        title = title_elem.get_text().strip()
                        article_url = link_elem.get_text().strip()
                        
                        # Check if article is relevant to topic (improved matching)
                        title_lower = title.lower()
                        
                        # Require multiple terms for better relevance
                        matched_terms = sum(1 for term in search_terms if term in title_lower)
                        relevance_threshold = max(1, len(search_terms) // 2)  # At least half the terms
                        
                        if matched_terms >= relevance_threshold:
                            source = urlparse(feed_url).netloc.replace('www.', '').replace('feeds.', '')
                            
                            articles.append({
                                'url': article_url,
                                'title': title,
                                'source': source,
                                'search_method': 'rss_feed',
                                'relevance_score': matched_terms / len(search_terms)
                            })
                            
                            if len(articles) >= num_results:
                                break
                
                if len(articles) >= num_results:
                    break
                    
            except Exception:
                continue
                
        return articles[:num_results]
        
    except Exception:
        return []


def analyze_source_diversity(articles):
    """
    Analyze the political/ideological diversity of sources.
    Returns diversity score and source classification.
    """
    try:
        # Simple source bias classification (can be enhanced with external APIs)
        source_bias_map = {
            # Left-leaning
            'cnn.com': {'bias': -2, 'credibility': 7},
            'msnbc.com': {'bias': -3, 'credibility': 6}, 
            'huffpost.com': {'bias': -3, 'credibility': 5},
            'nytimes.com': {'bias': -1, 'credibility': 8},
            'washingtonpost.com': {'bias': -1, 'credibility': 8},
            'theguardian.com': {'bias': -2, 'credibility': 7},
            
            # Center/Neutral
            'bbc.co.uk': {'bias': 0, 'credibility': 9},
            'reuters.com': {'bias': 0, 'credibility': 9},
            'apnews.com': {'bias': 0, 'credibility': 9},
            'npr.org': {'bias': 0, 'credibility': 8},
            'pbs.org': {'bias': 0, 'credibility': 8},
            'csmonitor.com': {'bias': 0, 'credibility': 8},
            
            # Right-leaning  
            'foxnews.com': {'bias': 3, 'credibility': 6},
            'nypost.com': {'bias': 2, 'credibility': 6},
            'wsj.com': {'bias': 1, 'credibility': 8},
            'breitbart.com': {'bias': 4, 'credibility': 4},
            'dailywire.com': {'bias': 3, 'credibility': 5},
        }
        
        source_analysis = []
        total_bias = 0
        total_credibility = 0
        
        for article in articles:
            domain = urlparse(article['url']).netloc.lower().replace('www.', '')
            
            # Get bias and credibility ratings
            ratings = source_bias_map.get(domain, {'bias': 0, 'credibility': 5})  # Default: neutral, medium credibility
            
            source_analysis.append({
                'source': article['source'],
                'domain': domain,
                'bias_score': ratings['bias'],  # -5 to +5 scale
                'credibility': ratings['credibility'],  # 1-10 scale
                'title': article['title']
            })
            
            total_bias += abs(ratings['bias'])
            total_credibility += ratings['credibility']
        
        # Calculate diversity metrics
        num_sources = len(articles)
        if num_sources == 0:
            return [], 0, 0
            
        avg_credibility = total_credibility / num_sources
        
        # Diversity score: higher when we have sources across the political spectrum
        bias_scores = [s['bias_score'] for s in source_analysis]
        bias_range = max(bias_scores) - min(bias_scores) if bias_scores else 0
        diversity_score = min(bias_range * 2, 10)  # 0-10 scale
        
        return source_analysis, diversity_score, avg_credibility
        
    except Exception as e:
        return [], 0, 0


def find_convergence_points(article_summaries):
    """
    Find convergence points across multiple article analyses.
    This is a simplified version - could be enhanced with NLP.
    """
    try:
        if not article_summaries or len(article_summaries) < 2:
            return {"convergence_points": [], "disputed_claims": [], "consensus_level": 0}
        
        # Extract key points from each summary
        all_points = []
        for summary in article_summaries:
            if isinstance(summary, dict):
                # Extract from structured summary
                points = summary.get('key_points', []) + summary.get('main_claims', [])
            else:
                # Extract from text summary (basic approach)
                points = [line.strip() for line in str(summary).split('\n') if line.strip() and not line.startswith('#')]
            
            all_points.append(points)
        
        # Find similar points across sources (simplified approach)
        convergence_points = []
        disputed_claims = []
        
        # This is a basic implementation - could be enhanced with semantic similarity
        common_keywords = {}
        
        for article_points in all_points:
            for point in article_points:
                words = set(point.lower().split())
                for word in words:
                    if len(word) > 4:  # Only consider meaningful words
                        common_keywords[word] = common_keywords.get(word, 0) + 1
        
        # Find words mentioned by multiple sources
        total_sources = len(all_points)
        consensus_threshold = max(2, total_sources // 2)  # At least half of sources
        
        consensus_words = {word: count for word, count in common_keywords.items() 
                          if count >= consensus_threshold}
        
        # Generate convergence analysis
        if consensus_words:
            convergence_points = [f"Multiple sources discuss: {', '.join(list(consensus_words.keys())[:5])}"]
            consensus_level = len(consensus_words) / max(len(common_keywords), 1) * 100
        else:
            disputed_claims = ["Sources show significant disagreement on key facts"]
            consensus_level = 0
        
        return {
            "convergence_points": convergence_points,
            "disputed_claims": disputed_claims, 
            "consensus_level": min(consensus_level, 100),
            "total_sources": total_sources
        }
        
    except Exception as e:
        return {"convergence_points": [], "disputed_claims": [f"Analysis error: {str(e)}"], "consensus_level": 0}


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
            "Cross-Source BABE Comparison",
            "Multi-Article Comparison", 
            "Neutral Synthesis",
            "Source Convergence Analysis",
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
    """Display BABE-enhanced bias analysis results with comprehensive visualizations."""
    if not result or result.get('error'):
        st.error(f"Bias analysis failed: {result.get('error', 'Unknown error')}")
        if result.get('fallback'):
            st.warning("Showing fallback analysis:")
            result = result['fallback']
        else:
            return
    
    # BABE methodology explanation header
    st.markdown('<div class="section-header">🎯 BABE-Enhanced Bias Analysis</div>', unsafe_allow_html=True)
    
    # Add BABE methodology explanation
    with st.expander("📚 About BABE (Bias Annotations By Experts) Framework", expanded=False):
        st.markdown("""
        **BABE Framework** uses expert-annotated evaluation methodology for research-grade bias detection:
        
        **🔬 BABE Categories (Expert-Validated):**
        - **Lexical Bias (25%)**: Emotional language, value-laden adjectives, loaded terminology
        - **Informational Bias (30%)**: Omitted perspectives, cherry-picked data, missing context
        - **Demographic Bias (20%)**: Group stereotyping, unfair representation patterns
        - **Epistemological Bias (25%)**: Opinion as fact, false certainty, poor attribution
        
        **📊 Multi-Analyst Calibration:**
        - Cross-validated with **AllSides** and **Ad Fontes Media** ratings
        - Precision/Recall/F1 scoring for each bias category
        - Confidence intervals and evidence transparency
        
        **🎯 Scoring & Metrics:**
        - **-10 to -3**: Strong left-leaning bias | **-2 to +2**: Neutral | **+3 to +10**: Strong right-leaning bias
        - **Precision**: How many detected biases are actually biased (accuracy)
        - **Recall**: How many actual biases were detected (completeness)
        - **F1-Score**: Balanced measure of precision and recall
        
        **✅ Transparency Standards:**
        - Every bias score includes specific evidence and examples
        - Alternative neutral framings provided for biased elements
        - Cross-source comparison recommendations
        """)
    
    # Check if this is BABE-enhanced result
    babe_result = result.get('babe_evaluation')
    if babe_result:
        display_babe_analysis(babe_result, result)
    else:
        # Fallback to legacy display
        display_legacy_bias_analysis(result)

def display_babe_analysis(babe_result, full_result):
    """Display BABE-specific evaluation results"""
    
    # Extract BABE metrics
    overall_score_data = babe_result.get('overall_bias_score', {})
    overall_score = overall_score_data.get('score', 0)
    confidence_interval = overall_score_data.get('confidence_interval', [0, 0])
    evidence_strength = overall_score_data.get('evidence_strength', 'weak')
    
    # === BABE OVERVIEW SECTION ===
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if overall_score > 2:
            st.error(f"**BABE Bias Score**\n{overall_score}/10\n(Right-leaning)")
        elif overall_score < -2:
            st.error(f"**BABE Bias Score**\n{overall_score}/10\n(Left-leaning)")
        else:
            st.success(f"**BABE Bias Score**\n{overall_score}/10\n(Neutral)")
        
        # Show confidence interval
        st.caption(f"95% CI: [{confidence_interval[0]}, {confidence_interval[1]}]")
    
    with col2:
        evidence_emoji = {"strong": "🟢", "medium": "🟡", "weak": "🔴"}
        st.metric("Evidence Strength", evidence_strength.title(), 
                 help="Evidence strength indicates how much concrete evidence supports the bias assessment")
        st.markdown(evidence_emoji.get(evidence_strength, "🔴"))

    with col3:
        cross_validation = babe_result.get('cross_validation', {})
        allsides_agreement = cross_validation.get('allsides_agreement', 'no_data')
        expert_consensus = cross_validation.get('expert_consensus', 0)
        
        st.metric("Expert Consensus", f"{int(expert_consensus * 100)}%",
                 help="Agreement level with external expert rating systems")
        st.caption(f"AllSides: {allsides_agreement}")
    
    with col4:
        # Calculate average F1 score across categories
        category_scores = babe_result.get('category_scores', {})
        f1_scores = [cat.get('f1_score', 0) for cat in category_scores.values()]
        avg_f1 = sum(f1_scores) / len(f1_scores) if f1_scores else 0
        
        st.metric("Analysis Quality (F1)", f"{avg_f1:.2f}",
                 help="F1 score measures balance of precision and recall across bias categories")
        quality_color = "🟢" if avg_f1 > 0.75 else "🟡" if avg_f1 > 0.60 else "🔴"
        st.markdown(quality_color)
    
    # === BABE CATEGORY BREAKDOWN ===
    st.markdown("### 📊 BABE Category Analysis")
    
    # Create interactive category display
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Lexical Bias", "📰 Informational Bias", "👥 Demographic Bias", "🧠 Epistemological Bias"])
    
    categories = ['lexical_bias', 'informational_bias', 'demographic_bias', 'epistemological_bias']
    tab_mapping = [tab1, tab2, tab3, tab4]
    
    for i, (category, tab) in enumerate(zip(categories, tab_mapping)):
        with tab:
            cat_data = category_scores.get(category, {})
            
            col1, col2, col3 = st.columns(3)
            with col1:
                score = cat_data.get('score', 0)
                if abs(score) > 2:
                    st.error(f"**Score: {score}**")
                elif abs(score) > 1:
                    st.warning(f"**Score: {score}**")
                else:
                    st.success(f"**Score: {score}**")
            
            with col2:
                precision = cat_data.get('precision', 0)
                recall = cat_data.get('recall', 0)
                st.metric("Precision", f"{precision:.2f}")
                st.metric("Recall", f"{recall:.2f}")
            
            with col3:
                f1_score = cat_data.get('f1_score', 0)
                st.metric("F1-Score", f"{f1_score:.2f}")
                
            # Evidence for this category
            evidence = cat_data.get('evidence', [])
            if evidence:
                st.markdown("**📋 Evidence:**")
                for item in evidence[:5]:  # Limit to 5 items
                    st.markdown(f"• {item}")
            else:
                st.success("✅ No significant bias detected in this category")
    
    # === HIGHLIGHTED BIAS EVIDENCE ===
    highlighted_evidence = full_result.get('highlighted_bias_evidence', [])
    if highlighted_evidence:
        st.markdown("### 🔍 Specific Bias Evidence")
        
        for evidence in highlighted_evidence[:8]:  # Limit display
            with st.expander(f"📍 {evidence.get('bias_type', 'unknown').replace('_', ' ').title()}: \"{evidence.get('text', '')[:50]}...\""):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown(f"**🎯 Biased Text:** \"{evidence.get('text', '')}\"")
                    st.markdown(f"**📍 Location:** {evidence.get('line_position', 'Unknown')}")
                    st.markdown(f"**💭 Why Biased:** {evidence.get('explanation', 'No explanation')}")
                
                with col2:
                    st.markdown(f"**🔄 Neutral Alternative:**")
                    st.info(evidence.get('alternative_framing', 'Use more balanced language'))
                    st.metric("Confidence", f"{evidence.get('confidence', 0):.0%}")
    
    # === MISSING PERSPECTIVES ===
    missing_perspectives = full_result.get('missing_perspectives', [])
    if missing_perspectives:
        st.markdown("### ❓ Missing Perspectives Identified")
        
        for perspective in missing_perspectives:
            with st.expander(f"🔍 {perspective.get('perspective', 'Unknown perspective')}"):
                st.markdown(f"**📊 Impact:** {perspective.get('impact', 'Unknown impact')}")
                st.markdown(f"**📰 Suggested Sources:**")
                for source in perspective.get('suggested_sources', []):
                    st.markdown(f"• {source}")
                st.metric("Confidence", f"{perspective.get('confidence', 0):.0%}")
    
    # === COMPARATIVE ANALYSIS ===
    comparative = full_result.get('comparative_analysis', {})
    if comparative:
        st.markdown("### ⚖️ Cross-Source Framing Comparison")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🔵 Likely Left Framing:**")
            st.info(comparative.get('likely_left_framing', 'Not available'))
        
        with col2:
            st.markdown("**🟢 Neutral Baseline:**")
            st.success(comparative.get('neutral_baseline', 'Not available'))
        
        with col3:
            st.markdown("**🔴 Likely Right Framing:**")
            st.error(comparative.get('likely_right_framing', 'Not available'))
        
        current_proximity = comparative.get('current_proximity', 'unknown')
        st.markdown(f"**📊 This Article Closest To:** {current_proximity}")
    
    # === ACTIONABLE FEEDBACK ===
    feedback = full_result.get('actionable_feedback', {})
    if feedback:
        st.markdown("### 💡 Actionable Recommendations")
        
        tab1, tab2, tab3 = st.tabs(["👥 For Readers", "✏️ For Authors", "📝 For Editors"])
        
        with tab1:
            for item in feedback.get('for_readers', []):
                st.markdown(f"• {item}")
        
        with tab2:
            for item in feedback.get('for_authors', []):
                st.markdown(f"• {item}")
        
        with tab3:
            for item in feedback.get('for_editors', []):
                st.markdown(f"• {item}")

def display_legacy_bias_analysis(result):
    """Display legacy bias analysis for backward compatibility"""
    
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
        st.metric("Confidence", f"{confidence}%")
        st.markdown(f"{confidence_color}")

    with col3:
        objectivity = result.get('objectivity_score', 100 - abs(overall_score * 10))
        st.metric("Objectivity", f"{objectivity}%")
    
    with col4:
        if result.get('source_context'):
            st.info(f"📰 {result['source_context']}")
        else:
            st.info("📰 Unknown source")
    
    # Show basic component breakdown if available
    if result.get('component_scores'):
        st.markdown("### 📊 Component Breakdown")
        
        components = result['component_scores']
        for component, score in components.items():
            label = component.replace('_', ' ').title()
            if abs(score) > 2:
                st.error(f"**{label}:** {score}")
            elif abs(score) > 1:
                st.warning(f"**{label}:** {score}")
            else:
                st.success(f"**{label}:** {score}")

def add_cross_source_comparison_interface():
    """Add interface for cross-source comparison using BABE methodology"""
    
    st.markdown("---")
    st.markdown('<div class="section-header">⚖️ Cross-Source Comparison (BABE)</div>', unsafe_allow_html=True)
    
    with st.expander("📚 About Cross-Source Comparison", expanded=False):
        st.markdown("""
        **Cross-Source Comparison** analyzes 2-3 articles on the same story to identify:
        - **Framing Differences**: How each source presents the same facts
        - **Bias Divergences**: Relative positioning on political spectrum  
        - **Missing Perspectives**: What each source omits or emphasizes
        - **Consensus Points**: Facts all sources agree on
        - **Major Disagreements**: Where sources fundamentally differ
        
        This helps readers understand how bias shapes news presentation and find balanced perspectives.
        """)
    
    # Article input for comparison
    st.markdown("### 📰 Add Articles for Comparison")
    
    # Initialize session state for comparison articles
    if 'comparison_articles' not in st.session_state:
        st.session_state.comparison_articles = []
    
    # Add new article
    with st.form("add_comparison_article"):
        col1, col2 = st.columns([3, 1])
        
        with col1:
            article_url = st.text_input("Article URL", placeholder="https://example.com/article")
            article_title = st.text_input("Article Title (Optional)", placeholder="Will be auto-detected if left blank")
        
        with col2:
            st.markdown("<br>", unsafe_allow_html=True)  # Spacing
            add_article = st.form_submit_button("➕ Add Article", use_container_width=True)
    
    # Handle article addition
    if add_article and article_url:
        with st.spinner("Fetching article content..."):
            try:
                article_text = fetch_article_from_url(article_url)
                
                # Auto-extract title if not provided
                if not article_title.strip():
                    article_title = extract_title_from_url(article_url)
                
                article_data = {
                    'url': article_url,
                    'title': article_title or f"Article {len(st.session_state.comparison_articles) + 1}",
                    'text': article_text
                }
                
                st.session_state.comparison_articles.append(article_data)
                st.success(f"Added: {article_data['title']}")
                
            except Exception as e:
                st.error(f"Failed to fetch article: {str(e)}")
    
    # Display current articles
    if st.session_state.comparison_articles:
        st.markdown("### 📋 Articles for Comparison")
        
        for i, article in enumerate(st.session_state.comparison_articles):
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.markdown(f"**{i+1}.** [{article['title']}]({article['url']})")
                st.caption(f"Length: {len(article['text'].split())} words")
            
            with col2:
                if st.button(f"👁️ Preview", key=f"preview_{i}"):
                    with st.expander(f"Preview: {article['title']}", expanded=True):
                        st.text(article['text'][:500] + "..." if len(article['text']) > 500 else article['text'])
            
            with col3:
                if st.button(f"🗑️ Remove", key=f"remove_{i}"):
                    st.session_state.comparison_articles.pop(i)
                    st.rerun()
        
        # Comparison analysis button
        if len(st.session_state.comparison_articles) >= 2:
            if st.button("🔍 **Run Cross-Source Analysis**", use_container_width=True, type="primary"):
                with st.spinner("Running BABE cross-source analysis..."):
                    try:
                        # Initialize BiasAnalyzer
                        from summarizer import BiasAnalyzer, TextSummarizer
                        summarizer = TextSummarizer()
                        bias_analyzer = BiasAnalyzer(summarizer)
                        
                        # Run cross-source comparison
                        comparison_result = bias_analyzer.cross_source_comparison(st.session_state.comparison_articles)
                        
                        # Display results
                        display_cross_source_results(comparison_result)
                        
                    except Exception as e:
                        st.error(f"Cross-source analysis failed: {str(e)}")
        else:
            st.info("Add at least 2 articles to run comparison analysis")
        
        # Clear all articles button
        if st.button("🔄 Clear All Articles"):
            st.session_state.comparison_articles = []
            st.rerun()

def display_cross_source_results(result):
    """Display cross-source comparison results"""
    
    if result.get('error'):
        st.error(result['error'])
        return
    
    st.markdown("### 📊 Cross-Source Analysis Results")
    
    # Overview metrics
    articles = result.get('articles', [])
    divergence = result.get('divergence_analysis', {})
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        bias_range = divergence.get('bias_score_range', 0)
        st.metric("Bias Range", f"{bias_range:.1f}", 
                 help="Difference between most biased sources")
    
    with col2:
        polarization = divergence.get('polarization_level', 'unknown')
        color_map = {"low": "🟢", "medium": "🟡", "high": "🔴"}
        st.metric("Polarization", polarization.title())
        st.markdown(color_map.get(polarization, "⚪"))
    
    with col3:
        consensus_count = len(result.get('consensus_points', []))
        st.metric("Consensus Points", consensus_count)
    
    # Individual article analysis
    st.markdown("### 📰 Individual Article Analysis")
    
    for i, article in enumerate(articles):
        with st.expander(f"📄 {article.get('title', f'Article {i+1}')}"):
            col1, col2 = st.columns(2)
            
            with col1:
                bias_score = article.get('bias_score', 0)
                if abs(bias_score) > 2:
                    st.error(f"**Bias Score:** {bias_score}")
                elif abs(bias_score) > 1:
                    st.warning(f"**Bias Score:** {bias_score}")
                else:
                    st.success(f"**Bias Score:** {bias_score}")
                
                st.markdown(f"**Source:** {article.get('source', 'Unknown')}")
            
            with col2:
                st.markdown("**Key Framings:**")
                for framing in article.get('key_framings', [])[:3]:
                    st.markdown(f"• {framing}")
                
                st.markdown("**Emotional Language:**")
                for emotion in article.get('emotional_language', [])[:3]:
                    st.markdown(f"• {emotion}")
    
    # Consensus and disagreements
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ✅ Consensus Points")
        consensus_points = result.get('consensus_points', [])
        if consensus_points:
            for point in consensus_points:
                st.success(f"• {point}")
        else:
            st.info("No clear consensus points identified")
    
    with col2:
        st.markdown("### ⚠️ Major Disagreements")
        disagreements = result.get('major_disagreements', [])
        if disagreements:
            for disagreement in disagreements:
                st.error(f"• {disagreement}")
        else:
            st.success("No major disagreements detected")
    
    # Recommendations
    st.markdown("### 💡 Reader Recommendations")
    
    most_biased = divergence.get('most_biased', {})
    most_neutral = divergence.get('most_neutral', {})
    
    if most_neutral:
        st.success(f"**Most Balanced Source:** {most_neutral.get('title', 'Unknown')} (Score: {most_neutral.get('bias_score', 0)})")
    
    if most_biased:
        st.warning(f"**Most Biased Source:** {most_biased.get('title', 'Unknown')} (Score: {most_biased.get('bias_score', 0)})")
    
    st.info("""
    **💡 For Balanced Understanding:**
    - Read the most neutral source first for baseline facts
    - Compare how different sources frame the same events
    - Look for information only present in one source
    - Consider why sources emphasize different aspects
    """)

# Helper functions for cross-source comparison
def extract_title_from_url(url):
    """Extract title from article URL (simplified)"""
    try:
        import requests
        from bs4 import BeautifulSoup
        
        response = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
        soup = BeautifulSoup(response.content, 'html.parser')
        
        title = soup.find('title')
        return title.get_text().strip() if title else "Untitled Article"
        
    except Exception:
        return "Untitled Article"
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
                    if st.button("🗑️ Clear Results", key="clear_results_1"):
                        st.session_state.last_results = None
                        st.rerun()
            else:
                st.info("No analysis results yet. Use the 'Single Article Analysis' tab to get started.")
    
    else:  # Multi-article modes including Source Convergence Analysis and Cross-Source BABE Comparison
        if analysis_mode == "Cross-Source BABE Comparison":
            # Dedicated interface for BABE cross-source comparison
            add_cross_source_comparison_interface()
            
        elif analysis_mode == "Source Convergence Analysis":
            tab1, tab2 = st.tabs(["🔍 Topic Search", "📊 Convergence Results"])
            
            with tab1:
                st.markdown("## 🔍 Multi-Source Topic Analysis")
                
                # Add methodology explanation
                with st.expander("📚 What is Source Convergence Analysis?", expanded=False):
                    st.markdown("""
                    **Source Convergence Analysis** finds the truth by comparing how different news sources report the same topic:
                    
                    **🎯 How It Works:**
                    1. **Smart Topic Extraction**: When you provide an article URL, AI summarizes the content to extract key themes (not just title keywords!)
                    2. **Diverse Source Search**: Finds related articles from across the political spectrum using refined search terms
                    3. **Individual Analysis**: Analyzes each article for bias and key claims
                    4. **Convergence Detection**: Identifies what facts most sources agree on
                    5. **Truth Synthesis**: Highlights consensus points vs disputed claims
                    
                    **🏆 Why This Works:**
                    - **AI-Enhanced Search**: Smart topic extraction captures actual themes, not just surface keywords
                    - **Consensus = Higher Truth Probability**: Facts agreed upon by opposing sources are likely accurate
                    - **Bias Cancellation**: Left and right-leaning sources balance each other out
                    - **Credibility Weighting**: More credible sources carry more weight in analysis
                    - **Disputed Claims**: Clearly shows what remains controversial or uncertain
                    """)                
                
                # Topic input methods
                search_method = st.radio(
                    "How do you want to find related articles?",
                    ["Search by Topic", "Start with Article URL"],
                    horizontal=True
                )
                
                topic_query = ""
                
                if search_method == "Search by Topic":
                    topic_query = st.text_input(
                        "Enter a topic or news subject:",
                        placeholder="e.g., climate change policy, AI regulation, economic inflation",
                        help="Be specific for better results. Examples: 'Tesla stock performance', 'Ukraine aid package', 'COVID vaccine effectiveness'"
                    )
                else:
                    initial_url = st.text_input(
                        "Enter article URL to find related coverage:",
                        placeholder="https://example.com/news/article",
                        help="We'll extract the topic from this article and find related coverage"
                    )
                    
                    if initial_url and st.button("🔍 Extract Topic from Article"):
                        with st.spinner("Analyzing article to extract key topics..."):
                            # Fetch and analyze the initial article to extract main topic
                            result = fetch_article_from_url(initial_url)
                            if result['success']:
                                # Enhanced topic extraction using summarization
                                extracted_topics = extract_topics_from_article(
                                    result['content'], 
                                    result['title'],
                                    settings
                                )
                                if extracted_topics['success']:
                                    topic_query = extracted_topics['search_terms']
                                    st.success(f"✨ **Smart Topic Extraction Successful!**")
                                    st.info(f"**Original Title:** {result['title']}")
                                    st.info(f"**Key Topics Found:** {topic_query}")
                                    
                                    # Show the summary that was used for extraction - auto-expanded for transparency
                                    with st.expander("📄 Article Summary Used for Topic Extraction", expanded=True):
                                        st.markdown(f"**Summary:** {extracted_topics['summary']}")
                                        st.markdown(f"**Key Themes:** {', '.join(extracted_topics['themes'])}")
                                        st.markdown("---")
                                        st.markdown("🎯 **This information will be used to find related articles across diverse news sources.**")
                                    
                                    # Store all extracted information for seamless workflow
                                    st.session_state['extracted_topic'] = topic_query
                                    st.session_state['extraction_method'] = 'smart_summary'
                                    st.session_state['original_url'] = initial_url
                                    st.session_state['original_title'] = result['title']
                                    st.session_state['article_content'] = result['content']
                                    st.session_state['extraction_data'] = extracted_topics
                                else:
                                    # Fallback to title-based extraction
                                    topic_query = result['title']
                                    st.warning("⚠️ Smart extraction failed, using title as fallback")
                                    st.session_state['extracted_topic'] = topic_query
                                    st.session_state['extraction_method'] = 'title_fallback'
                                    st.session_state['original_url'] = initial_url
                                    st.session_state['original_title'] = result['title']
                                    st.session_state['article_content'] = result['content']
                            else:
                                st.error(f"Could not fetch article: {result['error']}")
                    
                    # Use extracted topic if available - Enhanced Display
                    if 'extracted_topic' in st.session_state:
                        topic_query = st.session_state['extracted_topic']
                        
                        # Enhanced article metadata display  
                        st.success("✅ **Article Analysis Ready!**")
                        
                        with st.container():
                            st.markdown("### 📄 Article Metadata")
                            col1, col2 = st.columns([3, 1])
                            
                            with col1:
                                st.markdown(f"**🔗 Original URL:** {st.session_state.get('original_url', 'N/A')}")
                                st.markdown(f"**📰 Article Title:** {st.session_state.get('original_title', 'N/A')}")
                                st.markdown(f"**🎯 Search Topic:** {topic_query}")
                                
                                # Show extraction method badge
                                extraction_method = st.session_state.get('extraction_method', 'unknown')
                                if extraction_method == 'smart_summary':
                                    st.markdown("🧠 **Method:** AI-Enhanced Topic Extraction")
                                else:
                                    st.markdown("📝 **Method:** Title-Based Extraction")
                            
                            with col2:
                                # Show article details if available
                                if 'extraction_data' in st.session_state and st.session_state['extraction_data'].get('themes'):
                                    st.markdown("**🏷️ Key Themes:**")
                                    for theme in st.session_state['extraction_data']['themes'][:3]:  # Show top 3
                                        st.markdown(f"• {theme}")
                        
                        # Add a clear separator
                        st.markdown("---")
                        st.markdown("### 🔍 **Ready for Multi-Source Analysis**")
                        st.info("✨ All information extracted! Configure analysis settings below and click 'Find & Analyze Sources'.")
                
                # Source diversity settings
                col1, col2 = st.columns(2)
                
                with col1:
                    num_sources = st.slider(
                        "Number of sources to analyze:",
                        min_value=3, max_value=8, value=5,
                        help="More sources = better convergence detection, but slower analysis"
                    )
                
                with col2:
                    require_diversity = st.checkbox(
                        "Require political diversity",
                        value=True,
                        help="Ensures sources span different political perspectives"
                    )
                
                # Enhanced Search and analyze button
                button_text = "🔍 Find & Analyze Sources"
                button_help = "Find related articles and analyze convergence points"
                
                # Make the button more prominent if topic was extracted from URL
                if 'extracted_topic' in st.session_state and st.session_state.get('original_url'):
                    st.markdown("### 🚀 **Start Analysis**")
                    button_text = f"🚀 Analyze '{st.session_state['extracted_topic'][:50]}...'" if len(st.session_state['extracted_topic']) > 50 else f"🚀 Analyze '{st.session_state['extracted_topic']}'"
                    button_help = f"Find articles related to: {st.session_state['extracted_topic']}"
                    
                    # Add a prominent call-to-action
                    st.info("🎯 **Ready to find convergence points!** Click below to search for related articles across diverse sources.")
                
                if topic_query and st.button(button_text, type="primary", width="stretch", help=button_help):
                    if not validate_inputs("dummy text", settings):  # Check API keys
                        st.stop()
                        
                    # Show search methodology info
                    with st.expander("🔍 Search Details", expanded=False):
                        search_terms = topic_query.lower().split()
                        
                        # Show different info based on how topic was extracted
                        extraction_method = st.session_state.get('extraction_method', 'manual')
                        
                        if extraction_method == 'smart_summary':
                            st.markdown("### 🧠 **Smart Topic Extraction Used**")
                            st.markdown("✅ **Enhanced Method**: Article was summarized by AI to extract core themes")
                            st.markdown("✅ **Better Accuracy**: Search terms based on content analysis, not just title keywords")
                            st.markdown("✅ **Context-Aware**: Captures main arguments and topics discussed in the article")
                        elif extraction_method == 'title_fallback':
                            st.markdown("### ⚠️ **Fallback Topic Extraction**")
                            st.markdown("⚠️ AI extraction failed, using article title as search terms")
                        else:
                            st.markdown("### 📝 **Manual Topic Entry**")
                            st.markdown("ℹ️ Using your manually entered topic for search")
                        
                        st.markdown(f"**Search Terms Used:** {', '.join(search_terms)}")
                        st.markdown(f"**Sources Searched:** BBC, CNN, NPR, Reuters, WSJ, Washington Post, Politico, Fox News, Time, NBC")
                        st.markdown(f"**Matching Strategy:** Articles must contain at least {max(1, len(search_terms)//2)} search terms in title")
                        st.markdown(f"**Relevance Scoring:** Articles ranked by percentage of search terms matched")
                    
                    with st.spinner(f"Searching for {num_sources} diverse sources on '{topic_query}'..."):
                        try:
                            # Step 1: Search for related articles
                            st.info("🔍 Searching for related articles...")
                            articles = search_related_articles(topic_query, num_sources)
                            
                            if not articles:
                                st.error("Could not find related articles. Try a different topic or search terms.")
                                st.stop()
                            
                            st.success(f"Found {len(articles)} articles from diverse sources")
                            
                            # Show search results details
                            if articles:
                                with st.expander("📄 Articles Found", expanded=False):
                                    for i, article in enumerate(articles, 1):
                                        relevance = article.get('relevance_score', 0)
                                        relevance_pct = int(relevance * 100) if relevance > 0 else "N/A"
                                        st.markdown(f"**{i}. {article['source']}** - {relevance_pct}% relevance")
                                        st.markdown(f"   *{article['title'][:100]}...*")
                                        st.markdown(f"   `{article['url'][:60]}...`")
                                        st.markdown("")
                            
                            # Step 2: Analyze source diversity
                            source_analysis, diversity_score, avg_credibility = analyze_source_diversity(articles)
                            
                            if require_diversity and diversity_score < 3:
                                st.warning("Low source diversity detected. Results may be biased toward one perspective.")
                            
                            # Step 3: Fetch and analyze each article
                            st.info("📄 Analyzing each article...")
                            article_analyses = []
                            
                            config = create_temp_config(settings)
                            engine = AnalysisEngine(
                                model_type=settings['model'], 
                                config=config, 
                                verbose=settings['verbose_mode']
                            )
                            
                            progress_bar = st.progress(0)
                            
                            for i, article in enumerate(articles):
                                try:
                                    # Fetch article content
                                    fetch_result = fetch_article_from_url(article['url'])
                                    
                                    if fetch_result['success']:
                                        # Analyze the article
                                        analysis_result = engine.analyze_single_article(
                                            fetch_result['content'],
                                            mode='full',
                                            source_url=article['url'],
                                            article_title=article['title']
                                        )
                                        
                                        article_analyses.append({
                                            'source': article['source'],
                                            'title': article['title'],
                                            'url': article['url'],
                                            'content': fetch_result['content'][:1000],  # Store excerpt
                                            'analysis': analysis_result,
                                            'source_info': next((s for s in source_analysis if s['source'] == article['source']), {})
                                        })
                                    else:
                                        st.warning(f"Could not analyze {article['source']}: {fetch_result['error']}")
                                    
                                    progress_bar.progress((i + 1) / len(articles))
                                    
                                except Exception as e:
                                    st.warning(f"Error analyzing {article['source']}: {str(e)}")
                                    continue
                            
                            # Step 4: Find convergence points
                            st.info("🎯 Identifying convergence points...")
                            
                            summaries = [a['analysis'] for a in article_analyses if a.get('analysis')]
                            convergence_analysis = find_convergence_points(summaries)
                            
                            # Store comprehensive results
                            st.session_state.last_results = {
                                'type': 'Source Convergence Analysis',
                                'data': {
                                    'topic': topic_query,
                                    'articles': article_analyses,
                                    'source_analysis': source_analysis,
                                    'diversity_score': diversity_score,
                                    'avg_credibility': avg_credibility,
                                    'convergence': convergence_analysis,
                                    'num_sources_analyzed': len(article_analyses)
                                }
                            }
                            
                            st.success(f"✅ Analysis complete! Found convergence across {len(article_analyses)} sources.")
                            
                        except Exception as e:
                            st.error(f"Analysis failed: {str(e)}")
                            if settings['verbose_mode']:
                                st.exception(e)
            
            with tab2:
                # Display Source Convergence Analysis results
                if st.session_state.last_results and st.session_state.last_results['type'] == 'Source Convergence Analysis':
                    data = st.session_state.last_results['data']
                    
                    st.markdown(f"# 🎯 Convergence Analysis: {data['topic']}")
                    
                    # Overview metrics
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Sources Analyzed", data['num_sources_analyzed'])
                    
                    with col2:
                        diversity_color = "🟢" if data['diversity_score'] > 6 else "🟡" if data['diversity_score'] > 3 else "🔴"
                        st.metric("Diversity Score", f"{data['diversity_score']:.1f}/10")
                        st.markdown(f"{diversity_color}")
                    
                    with col3:
                        credibility_color = "🟢" if data['avg_credibility'] > 7 else "🟡" if data['avg_credibility'] > 5 else "🔴"
                        st.metric("Avg Credibility", f"{data['avg_credibility']:.1f}/10")
                        st.markdown(f"{credibility_color}")
                    
                    with col4:
                        consensus = data['convergence']['consensus_level']
                        consensus_color = "🟢" if consensus > 70 else "🟡" if consensus > 40 else "🔴"
                        st.metric("Consensus Level", f"{consensus:.0f}%")
                        st.markdown(f"{consensus_color}")
                    
                    # Source diversity visualization
                    st.markdown("## 📊 Source Analysis")
                    
                    if data['source_analysis']:
                        import pandas as pd
                        
                        # Create source analysis table
                        source_df = pd.DataFrame([
                            {
                                'Source': s['source'],
                                'Political Bias': f"{s['bias_score']:+d}" if s['bias_score'] != 0 else "Neutral",
                                'Credibility': f"{s['credibility']}/10",
                                'Bias Direction': "Left" if s['bias_score'] < 0 else "Right" if s['bias_score'] > 0 else "Center"
                            }
                            for s in data['source_analysis']
                        ])
                        
                        st.dataframe(source_df, use_container_width=True, hide_index=True)
                        
                        # Bias distribution chart
                        bias_scores = [s['bias_score'] for s in data['source_analysis']]
                        if bias_scores:
                            st.markdown("### 📈 Political Bias Distribution")
                            
                            left_count = sum(1 for b in bias_scores if b < -1)
                            center_count = sum(1 for b in bias_scores if -1 <= b <= 1) 
                            right_count = sum(1 for b in bias_scores if b > 1)
                            
                            col1, col2, col3 = st.columns(3)
                            with col1:
                                st.metric("Left-Leaning", left_count, help="Sources with bias score < -1")
                            with col2:
                                st.metric("Center/Neutral", center_count, help="Sources with bias score between -1 and +1") 
                            with col3:
                                st.metric("Right-Leaning", right_count, help="Sources with bias score > +1")
                    
                    # Convergence points and disputed claims
                    st.markdown("## 🎯 Truth Analysis")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown('<div class="success-box"><h4>✅ Convergence Points</h4>', unsafe_allow_html=True)
                        st.markdown("*Facts that multiple sources agree on (likely true):*")
                        
                        if data['convergence']['convergence_points']:
                            for point in data['convergence']['convergence_points']:
                                st.markdown(f"• {point}")
                        else:
                            st.markdown("• No strong convergence points detected")
                            st.markdown("• Sources show significant disagreement on key facts")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    with col2:
                        st.markdown('<div class="error-box"><h4>⚠️ Disputed Claims</h4>', unsafe_allow_html=True)
                        st.markdown("*Facts where sources disagree (uncertain/controversial):*")
                        
                        if data['convergence']['disputed_claims']:
                            for claim in data['convergence']['disputed_claims']:
                                st.markdown(f"• {claim}")
                        else:
                            st.markdown("• High consensus across sources")
                            st.markdown("• Few disputed facts detected")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Individual article summaries
                    st.markdown("## 📄 Individual Source Analysis")
                    
                    for i, article in enumerate(data['articles']):
                        with st.expander(f"📰 {article['source']}: {article['title'][:100]}..."):
                            
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.markdown(f"**URL:** {article['url']}")
                                st.markdown(f"**Content Preview:**")
                                st.text(article['content'][:300] + "...")
                            
                            with col2:
                                source_info = article.get('source_info', {})
                                
                                bias_score = source_info.get('bias_score', 0)
                                bias_text = f"{bias_score:+d}" if bias_score != 0 else "Neutral"
                                bias_color = "🔴" if abs(bias_score) > 2 else "🟡" if abs(bias_score) > 0 else "🟢"
                                
                                st.markdown(f"**Political Bias:** {bias_color} {bias_text}")
                                st.markdown(f"**Credibility:** {source_info.get('credibility', 5)}/10")
                            
                            # Show analysis results if available
                            if article.get('analysis'):
                                st.markdown("**Key Points:**")
                                analysis = article['analysis']
                                
                                if isinstance(analysis, dict):
                                    if analysis.get('key_points'):
                                        key_points = analysis['key_points']
                                        if isinstance(key_points, list) and len(key_points) > 0:
                                            for point in key_points[:3]:
                                                if isinstance(point, str):
                                                    st.markdown(f"• {point}")
                                    elif analysis.get('summary'):
                                        summary = analysis['summary']
                                        if isinstance(summary, str) and len(summary) > 0:
                                            st.markdown(f"• {summary[:200]}...")
                                        else:
                                            st.markdown(f"• {str(summary)[:200]}...")
                                else:
                                    st.markdown(f"• {str(analysis)[:200]}...")
                    
                    # Methodology notes
                    st.markdown("---")
                    with st.expander("🔬 Methodology & Limitations"):
                        st.markdown("""
                        **How This Analysis Works:**
                        - Searches for articles using news APIs and RSS feeds
                        - Analyzes source credibility based on established media bias databases
                        - Uses AI to extract key claims and identify consensus vs disputed points
                        - Weights results based on source credibility and political diversity
                        
                        **Limitations:**
                        - Search results may not capture all relevant coverage
                        - Source bias ratings are based on general assessments, not article-specific
                        - Convergence detection uses simplified text analysis (could be enhanced with NLP)
                        - Some high-quality sources may be missed due to paywall restrictions
                        - Recent breaking news may have limited diverse coverage available
                        
                        **Best Practices:**
                        - Higher source diversity = more reliable convergence analysis
                        - Consider credibility scores when weighing consensus points
                        - Look for both what sources agree AND disagree on
                        - Supplement with additional research on disputed claims
                        """)
                    
                    # Export options for convergence analysis
                    st.markdown("---")
                    st.markdown("## 📥 Export Results")
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        # Create summary report
                        report_content = f"""SOURCE CONVERGENCE ANALYSIS: {data['topic']}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}

ANALYSIS OVERVIEW:
- Sources Analyzed: {data['num_sources_analyzed']}
- Diversity Score: {data['diversity_score']:.1f}/10
- Average Credibility: {data['avg_credibility']:.1f}/10
- Consensus Level: {data['convergence']['consensus_level']:.0f}%

CONVERGENCE POINTS (Likely True):
"""
                        for point in data['convergence']['convergence_points']:
                            report_content += f"• {point}\n"
                        
                        report_content += "\nDISPUTED CLAIMS (Uncertain):\n"
                        for claim in data['convergence']['disputed_claims']:
                            report_content += f"• {claim}\n"
                        
                        report_content += "\nSOURCE BREAKDOWN:\n"
                        for article in data['articles']:
                            source_info = article.get('source_info', {})
                            bias_score = source_info.get('bias_score', 0)
                            report_content += f"- {article['source']}: Bias {bias_score:+d}, Credibility {source_info.get('credibility', 5)}/10\n"
                        
                        st.download_button(
                            label="📄 Download Report",
                            data=report_content,
                            file_name=f"convergence_analysis_{data['topic'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                    
                    with col2:
                        # JSON export
                        json_content = json.dumps(data, indent=2, ensure_ascii=False, default=str)
                        st.download_button(
                            label="📋 Download JSON",
                            data=json_content,
                            file_name=f"convergence_data_{data['topic'].replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                    
                    with col3:
                        if st.button("🗑️ Clear Results", key="clear_results_2"):
                            st.session_state.last_results = None
                            st.rerun()
                else:
                    st.info("No convergence analysis results yet. Use the 'Topic Search' tab to analyze multiple sources on a topic.")
        
        else:  # Original multi-article modes
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
                        if st.button("🗑️ Clear Results", key="clear_results_3"):
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
            "Source Convergence Analysis": "Find related articles from diverse sources and identify consensus points vs disputed claims.",
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