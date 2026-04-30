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


def extract_topics_local_mode(content, title):
    """
    Local topic extraction without AI - uses text analysis and keyword extraction.
    Provides better results than just using the title.
    """
    import re
    from collections import Counter
    
    try:
        # Combine title and content for analysis
        full_text = f"{title} {content[:1500]}"  # Use first 1500 chars
        
        # Basic text processing
        # Remove URLs, emails, and special characters
        clean_text = re.sub(r'http[s]?://\S+', '', full_text)
        clean_text = re.sub(r'\S+@\S+', '', clean_text)
        clean_text = re.sub(r'[^\w\s]', ' ', clean_text)
        
        # Extract potential keywords (2-3 word phrases and important single words)
        words = clean_text.lower().split()
        
        # Common stop words to filter out
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their', 'said', 'says', 'also', 'than', 'more', 'very', 'so', 'just', 'now', 'then', 'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'many', 'most', 'other', 'some', 'such', 'only', 'own', 'same', 'so', 'than', 'too', 'very'}
        
        # Filter meaningful words (length > 2, not stop words)
        meaningful_words = [w for w in words if len(w) > 2 and w not in stop_words]
        
        # Count word frequency
        word_counts = Counter(meaningful_words)
        top_words = [word for word, count in word_counts.most_common(10)]
        
        # Extract 2-word phrases
        phrases = []
        for i in range(len(meaningful_words) - 1):
            phrase = f"{meaningful_words[i]} {meaningful_words[i+1]}"
            if len(phrase) > 6:  # Skip very short phrases
                phrases.append(phrase)
        
        phrase_counts = Counter(phrases)
        top_phrases = [phrase for phrase, count in phrase_counts.most_common(5)]
        
        # Create enhanced search terms by combining title keywords with content keywords
        title_words = [w for w in title.lower().split() if len(w) > 2 and w not in stop_words]
        
        # Prioritize title words + top content words + top phrases
        search_components = []
        if title_words:
            search_components.extend(title_words[:3])  # Top 3 title words
        if top_words:
            search_components.extend([w for w in top_words[:3] if w not in search_components])
        
        # Create search term
        if search_components:
            search_terms = ' '.join(search_components[:4])  # Max 4 components
        else:
            search_terms = title
            
        # Create themes from top phrases and words
        themes = []
        if top_phrases:
            themes.extend(top_phrases[:2])
        themes.extend([w.capitalize() for w in top_words[:3] if w not in ' '.join(themes).lower()])
        
        if not themes:
            themes = [title]
        
        return {
            'success': True,
            'summary': f"Local analysis of article: {title[:100]}{'...' if len(title) > 100 else ''}",
            'themes': themes[:5],  # Limit to 5 themes
            'search_terms': search_terms,
            'extraction_method': 'local'
        }
        
    except Exception as e:
        # Final fallback
        return {
            'success': False,
            'error': f'Local extraction error: {str(e)}',
            'fallback_reason': 'local_error',
            'summary': f"Title-based extraction: {title}",
            'themes': [title],
            'search_terms': title
        }


def extract_topics_from_article(content, title, settings):
    """
    Enhanced topic extraction using AI summarization.
    Analyzes the full article content to extract key themes and search terms.
    """
    try:
        # Check if we're using local model - provide basic but improved topic extraction
        if settings['model'] == 'local':
            return extract_topics_local_mode(content, title)
        
        # Check if we have the necessary API keys for AI models
        missing_keys = []
        if settings['model'] == 'openai' and not settings.get('openai_key'):
            missing_keys.append('OpenAI API Key')
        elif settings['model'] == 'anthropic' and not settings.get('anthropic_key'):
            missing_keys.append('Anthropic API Key')
        
        if missing_keys:
            return {
                'success': False,
                'error': f'Missing required API key: {missing_keys[0]}',
                'fallback_reason': 'no_api_key',
                'summary': f"Extracted from title: {title}",
                'themes': [title],
                'search_terms': title
            }
        
        # Create a temporary config and analysis engine
        config = create_temp_config(settings)
        if not config:
            return {
                'success': False,
                'error': 'Configuration setup failed',
                'fallback_reason': 'config_error',
                'summary': f"Extracted from title: {title}",
                'themes': [title],
                'search_terms': title
            }
            
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


def extract_atomic_claims(text, source_info):
    """
    Layer 1: Extract atomic claims from article text.
    Returns factual statements that can be verified/compared.
    """
    import re
    from datetime import datetime
    
    claims = []
    sentences = re.split(r'[.!?]+', text)
    
    # Patterns for different types of claims
    patterns = {
        'event': r'(.*?)\s+(happened|occurred|took place|began|started|ended)\s+(.*)',
        'causation': r'(.*?)\s+(caused|led to|resulted in|triggered)\s+(.*)',
        'attribution': r'(.*?)\s+(said|stated|claimed|announced|reported)\s+(.*)',
        'quantity': r'(.*?)\s+(\d+(?:,\d+)*(?:\.\d+)?)\s+(.*)',
        'temporal': r'(.*?)\s+(yesterday|today|Monday|Tuesday|January|February|on \w+|in \d+)\s+(.*)',
        'location': r'(.*?)\s+(in|at|near|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(.*)'
    }
    
    for i, sentence in enumerate(sentences[:20]):  # Limit for performance
        sentence = sentence.strip()
        if len(sentence) < 20:  # Skip very short sentences
            continue
            
        # Extract different types of claims
        for claim_type, pattern in patterns.items():
            matches = re.finditer(pattern, sentence, re.IGNORECASE)
            for match in matches:
                claim = {
                    'id': f"{source_info['source']}_{i}_{claim_type}",
                    'text': sentence,
                    'type': claim_type,
                    'source': source_info['source'],
                    'source_url': source_info['url'],
                    'source_title': source_info['title'],
                    'confidence': 0.7,  # Base confidence
                    'extracted_components': match.groups() if match.groups() else []
                }
                claims.append(claim)
    
    return claims

def cluster_similar_claims(all_claims):
    """
    Layer 2: Group semantically similar claims across articles.
    Uses text similarity to identify the same claim expressed differently.
    """
    import difflib
    from collections import defaultdict
    
    clusters = []
    used_claim_ids = set()
    
    for i, claim in enumerate(all_claims):
        if claim['id'] in used_claim_ids:
            continue
            
        # Start new cluster
        cluster = {
            'cluster_id': f"cluster_{len(clusters)}",
            'representative_claim': claim['text'],
            'claims': [claim],
            'sources': {claim['source']},
            'types': {claim['type']},
            'similarity_threshold': 0.6
        }
        
        used_claim_ids.add(claim['id'])
        
        # Find similar claims
        for j, other_claim in enumerate(all_claims[i+1:], i+1):
            if other_claim['id'] in used_claim_ids:
                continue
                
            # Calculate similarity
            similarity = difflib.SequenceMatcher(
                None, 
                claim['text'].lower(), 
                other_claim['text'].lower()
            ).ratio()
            
            # Also check if they're the same type and have overlapping components
            type_match = claim['type'] == other_claim['type']
            component_overlap = False
            
            if claim.get('extracted_components') and other_claim.get('extracted_components'):
                comp1 = set(' '.join(claim['extracted_components']).lower().split())
                comp2 = set(' '.join(other_claim['extracted_components']).lower().split())
                component_overlap = len(comp1.intersection(comp2)) > 0
            
            # Cluster if similar enough
            if similarity > cluster['similarity_threshold'] or (type_match and component_overlap and similarity > 0.4):
                cluster['claims'].append(other_claim)
                cluster['sources'].add(other_claim['source'])
                cluster['types'].add(other_claim['type'])
                used_claim_ids.add(other_claim['id'])
        
        clusters.append(cluster)
    
    return clusters

def score_cluster_agreement(cluster, total_sources):
    """
    Layer 3: Calculate agreement scoring for each claim cluster.
    """
    num_sources_reporting = len(cluster['sources'])
    source_coverage = num_sources_reporting / total_sources
    
    # Source diversity bonus (reporting from different perspectives is valuable)
    source_list = list(cluster['sources'])
    diversity_bonus = min(len(set(source_list)), 3) / 3  # Cap at 3 different sources
    
    # Confidence based on consistency of reporting
    claim_texts = [claim['text'] for claim in cluster['claims']]
    avg_similarity = 0
    if len(claim_texts) > 1:
        similarities = []
        for i in range(len(claim_texts)):
            for j in range(i+1, len(claim_texts)):
                sim = difflib.SequenceMatcher(None, claim_texts[i].lower(), claim_texts[j].lower()).ratio()
                similarities.append(sim)
        avg_similarity = sum(similarities) / len(similarities) if similarities else 0
    
    agreement_score = {
        'source_coverage': source_coverage,
        'sources_reporting': num_sources_reporting,
        'total_sources': total_sources,
        'diversity_score': diversity_bonus,
        'consistency_score': avg_similarity,
        'overall_confidence': (source_coverage * 0.4 + diversity_bonus * 0.3 + avg_similarity * 0.3),
        'agreement_level': 'high' if source_coverage > 0.7 else 'medium' if source_coverage > 0.4 else 'low'
    }
    
    return agreement_score

def analyze_claim_framing(cluster):
    """
    Layer 4: Analyze how the same claim is framed differently across sources.
    """
    framing_analysis = {
        'sentiment_variations': [],
        'emphasis_differences': [],
        'loaded_language': [],
        'perspective_differences': []
    }
    
    # Simple sentiment analysis (could be enhanced with ML models)
    positive_words = {'success', 'achievement', 'victory', 'progress', 'improvement', 'breakthrough', 'positive'}
    negative_words = {'failure', 'defeat', 'setback', 'decline', 'crisis', 'disaster', 'negative', 'concerning'}
    
    for claim in cluster['claims']:
        text_lower = claim['text'].lower()
        
        # Sentiment analysis
        pos_count = sum(1 for word in positive_words if word in text_lower)
        neg_count = sum(1 for word in negative_words if word in text_lower)
        
        sentiment = 'positive' if pos_count > neg_count else 'negative' if neg_count > pos_count else 'neutral'
        
        # Check for loaded language patterns
        loaded_phrases = []
        if any(word in text_lower for word in ['alleged', 'claimed', 'supposedly', 'reportedly']):
            loaded_phrases.append('uncertainty_markers')
        if any(word in text_lower for word in ['crisis', 'disaster', 'catastrophe', 'emergency']):
            loaded_phrases.append('crisis_language')
        if any(word in text_lower for word in ['expert', 'official', 'authority', 'confirmed']):
            loaded_phrases.append('authority_appeals')
        
        framing_analysis['sentiment_variations'].append({
            'source': claim['source'],
            'sentiment': sentiment,
            'pos_indicators': pos_count,
            'neg_indicators': neg_count
        })
        
        if loaded_phrases:
            framing_analysis['loaded_language'].append({
                'source': claim['source'],
                'techniques': loaded_phrases
            })
    
    # Identify emphasis differences
    claim_lengths = [len(claim['text']) for claim in cluster['claims']]
    if claim_lengths:
        avg_length = sum(claim_lengths) / len(claim_lengths)
        for claim in cluster['claims']:
            if len(claim['text']) > avg_length * 1.5:
                framing_analysis['emphasis_differences'].append({
                    'source': claim['source'],
                    'emphasis': 'detailed_coverage',
                    'length_ratio': len(claim['text']) / avg_length
                })
            elif len(claim['text']) < avg_length * 0.5:
                framing_analysis['emphasis_differences'].append({
                    'source': claim['source'],
                    'emphasis': 'brief_mention',
                    'length_ratio': len(claim['text']) / avg_length
                })
    
    return framing_analysis

def detect_omissions(clusters, source_list):
    """
    Layer 5: Detect what claims are present in some sources but missing from others.
    """
    omissions = []
    
    for cluster in clusters:
        missing_sources = set(source_list) - cluster['sources']
        
        if missing_sources:
            # Assess importance of the omitted claim
            importance_score = cluster.get('agreement_score', {}).get('overall_confidence', 0)
            
            # Higher importance if it's a high-agreement claim that some sources omit
            if importance_score > 0.6 and len(missing_sources) > 0:
                omission = {
                    'claim': cluster['representative_claim'],
                    'reporting_sources': list(cluster['sources']),
                    'omitting_sources': list(missing_sources),
                    'importance_score': importance_score,
                    'omission_type': 'significant' if importance_score > 0.8 else 'notable',
                    'potential_reasons': []
                }
                
                # Infer potential reasons for omission
                if cluster.get('framing_analysis', {}).get('loaded_language'):
                    omission['potential_reasons'].append('controversial_framing')
                if any('crisis' in claim['text'].lower() for claim in cluster['claims']):
                    omission['potential_reasons'].append('crisis_narrative')
                if any(word in cluster['representative_claim'].lower() for word in ['government', 'political', 'policy']):
                    omission['potential_reasons'].append('political_sensitivity')
                
                omissions.append(omission)
    
    return omissions

def create_truth_map(clusters, omissions, source_analysis):
    """
    Layer 6: Create the final "Truth Map" output instead of a single summary.
    """
    truth_map = {
        'timestamp': datetime.now().isoformat(),
        'sources_analyzed': len(source_analysis),
        'claims_extracted': sum(len(cluster['claims']) for cluster in clusters),
        'widely_reported': [],
        'disputed_framed_differently': [],
        'missing_from_some_coverage': [],
        'source_perspective_distances': [],
        'methodological_notes': []
    }
    
    # Categorize claims by agreement level
    for cluster in clusters:
        agreement = cluster.get('agreement_score', {})
        framing = cluster.get('framing_analysis', {})
        
        claim_summary = {
            'claim': cluster['representative_claim'],
            'sources_reporting': list(cluster['sources']),
            'confidence': agreement.get('overall_confidence', 0),
            'source_count': len(cluster['sources'])
        }
        
        # Widely reported (high agreement)
        if agreement.get('agreement_level') == 'high':
            truth_map['widely_reported'].append(claim_summary)
        
        # Disputed/Framed Differently (medium agreement or framing differences)
        elif (agreement.get('agreement_level') in ['medium', 'low'] or 
              len(framing.get('sentiment_variations', [])) > 1):
            
            dispute_info = claim_summary.copy()
            dispute_info['framing_differences'] = {
                'sentiment_range': list(set(sv['sentiment'] for sv in framing.get('sentiment_variations', []))),
                'loaded_language_detected': len(framing.get('loaded_language', [])) > 0,
                'emphasis_variations': len(framing.get('emphasis_differences', [])) > 0
            }
            truth_map['disputed_framed_differently'].append(dispute_info)
    
    # Missing from some coverage
    for omission in omissions:
        truth_map['missing_from_some_coverage'].append({
            'claim': omission['claim'],
            'reported_by': omission['reporting_sources'],
            'omitted_by': omission['omitting_sources'],
            'importance': omission['omission_type'],
            'potential_reasons': omission['potential_reasons']
        })
    
    # Calculate perspective distances between sources
    if len(source_analysis) > 1:
        for i in range(len(source_analysis)):
            for j in range(i+1, len(source_analysis)):
                source1, source2 = source_analysis[i], source_analysis[j]
                
                # Calculate difference in claim selection and framing
                s1_claims = set()
                s2_claims = set()
                
                for cluster in clusters:
                    if source1['source'] in cluster['sources']:
                        s1_claims.add(cluster['cluster_id'])
                    if source2['source'] in cluster['sources']:
                        s2_claims.add(cluster['cluster_id'])
                
                overlap = len(s1_claims.intersection(s2_claims))
                total = len(s1_claims.union(s2_claims))
                story_similarity = overlap / total if total > 0 else 0
                
                bias_distance = abs(source1.get('bias_score', 0) - source2.get('bias_score', 0))
                
                perspective_distance = {
                    'source_pair': f"{source1['source']} ↔ {source2['source']}",
                    'story_overlap': story_similarity,
                    'bias_difference': bias_distance,
                    'perspective_distance': 1 - story_similarity + (bias_distance / 10),
                    'interpretation': 'similar_stories' if story_similarity > 0.7 else 
                                   'different_emphasis' if story_similarity > 0.4 else 
                                   'different_stories'
                }
                
                truth_map['source_perspective_distances'].append(perspective_distance)
    
    # Add methodological notes
    truth_map['methodological_notes'] = [
        f"Analysis based on {len(clusters)} claim clusters extracted from {len(source_analysis)} sources",
        "Claims grouped using text similarity and semantic clustering",
        "Agreement scored by source coverage and consistency",
        "Framing analysis includes sentiment and loaded language detection",
        "Omission detection weighted by claim importance and source diversity",
        "This system shows what's agreed on, contested, and missing—not 'the truth'"
    ]
    
    return truth_map

def find_convergence_points(article_summaries, articles_metadata=None):
    """
    Enhanced convergence analysis using layered claim extraction and truth mapping.
    Returns a comprehensive "Truth Map" instead of simple convergence points.
    """
    try:
        if not article_summaries or len(article_summaries) < 2:
            return {
                "convergence_points": [], 
                "disputed_claims": [], 
                "consensus_level": 0,
                "truth_map": None,
                "error": "Insufficient articles for convergence analysis"
            }
        
        # Prepare source information
        sources_info = []
        if articles_metadata:
            sources_info = articles_metadata
        else:
            # Create basic source info if not provided
            for i, summary in enumerate(article_summaries):
                sources_info.append({
                    'source': f'Source_{i+1}',
                    'url': f'unknown_url_{i}',
                    'title': f'Article {i+1}',
                    'bias_score': 0
                })
        
        # Layer 1: Extract atomic claims from each article
        all_claims = []
        for i, summary in enumerate(article_summaries):
            if i < len(sources_info):
                source_info = sources_info[i]
                summary_text = summary if isinstance(summary, str) else str(summary)
                claims = extract_atomic_claims(summary_text, source_info)
                all_claims.extend(claims)
        
        if not all_claims:
            return {
                "convergence_points": [],
                "disputed_claims": [],
                "consensus_level": 0,
                "truth_map": None,
                "error": "No claims could be extracted from articles"
            }
        
        # Layer 2: Cluster similar claims
        clusters = cluster_similar_claims(all_claims)
        
        # Layer 3: Score agreement for each cluster
        total_sources = len(sources_info)
        for cluster in clusters:
            cluster['agreement_score'] = score_cluster_agreement(cluster, total_sources)
        
        # Layer 4: Analyze framing within clusters
        for cluster in clusters:
            cluster['framing_analysis'] = analyze_claim_framing(cluster)
        
        # Layer 5: Detect omissions
        source_names = [source['source'] for source in sources_info]
        omissions = detect_omissions(clusters, source_names)
        
        # Layer 6: Create Truth Map
        truth_map = create_truth_map(clusters, omissions, sources_info)
        
        # Legacy format for backwards compatibility
        convergence_points = [claim['claim'] for claim in truth_map['widely_reported']]
        disputed_claims = [claim['claim'] for claim in truth_map['disputed_framed_differently']]
        consensus_level = len(truth_map['widely_reported']) / len(clusters) if clusters else 0
        
        return {
            "convergence_points": convergence_points,
            "disputed_claims": disputed_claims,
            "consensus_level": consensus_level,
            "truth_map": truth_map,
            "analysis_summary": {
                "total_claims": len(all_claims),
                "claim_clusters": len(clusters),
                "widely_agreed": len(truth_map['widely_reported']),
                "disputed_or_framed": len(truth_map['disputed_framed_differently']),
                "omissions_detected": len(truth_map['missing_from_some_coverage'])
            }
        }
        
    except Exception as e:
        return {
            "convergence_points": [],
            "disputed_claims": [],
            "consensus_level": 0,
            "truth_map": None,
            "error": f"Analysis failed: {str(e)}"
        }
        
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
            "Source Convergence Analysis"
        ],
        help="Select the type of analysis to perform"
    )
    
    # Model selection
    model_options = ["openai", "anthropic", "local"]
    selected_model = st.sidebar.selectbox(
        "Select AI Model",
        options=model_options,
        index=0,
        help="OpenAI/Anthropic: Advanced analysis + smart topic extraction. Local: Basic analysis, title-only topic extraction."
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


# =============================================================================
# ENHANCED BIAS ANALYSIS HELPER FUNCTIONS
# =============================================================================

def get_bias_rule_explanation(text: str, category: str) -> str:
    """Generate explanation for why text is biased based on category"""
    rules = {
        'lexical_bias': [
            ('emotionally charged adjectives', ['devastating', 'shocking', 'outrageous', 'brilliant']),
            ('value-laden language', ['hero', 'villain', 'savior', 'enemy']),
            ('loaded terminology', ['regime', 'thugs', 'freedom fighters']),
            ('inflammatory descriptors', ['slammed', 'destroyed', 'crushed'])
        ],
        'informational_bias': [
            ('selective statistics', ['only positive data', 'cherry-picked numbers']),
            ('omitted context', ['missing background', 'no counterarguments']),
            ('emphasis imbalance', ['disproportionate focus', 'buried key facts'])
        ],
        'demographic_bias': [
            ('group generalizations', ['all', 'every', 'these people']),
            ('stereotyping language', ['typical', 'as expected', 'unsurprisingly']),
            ('tokenism patterns', ['single representative', 'exceptional case'])
        ],
        'epistemological_bias': [
            ('opinion as fact', ['obviously', 'clearly', 'undoubtedly']),
            ('unattributed claims', ['sources say', 'it is believed']),
            ('false certainty', ['will happen', 'proves that', 'shows'])
        ]
    }
    
    text_lower = text.lower()
    for rule_name, indicators in rules.get(category, []):
        for indicator in indicators:
            if isinstance(indicator, str) and indicator in text_lower:
                return rule_name
            elif isinstance(indicator, list):
                for word in indicator:
                    if word in text_lower:
                        return rule_name
    
    return f"Detected {category.replace('_', ' ')} pattern"

def generate_neutral_alternatives(biased_text: str, category: str) -> list:
    """Generate 2-3 neutral alternatives for biased text"""
    alternatives = []
    
    # Simple pattern-based alternatives (in real implementation, this would be AI-generated)
    if 'slammed' in biased_text.lower():
        alternatives = [
            biased_text.replace('slammed', 'criticized'),
            biased_text.replace('slammed', 'responded to'),
            biased_text.replace('slammed', 'disagreed with')
        ]
    elif 'devastating' in biased_text.lower():
        alternatives = [
            biased_text.replace('devastating', 'significant'),
            biased_text.replace('devastating', 'substantial'),
            biased_text.replace('devastating', 'considerable')
        ]
    elif 'hero' in biased_text.lower() or 'villain' in biased_text.lower():
        alternatives = [
            "Use specific role/title instead of value-laden labels",
            "Describe actions without character judgment",
            "Let readers form their own opinions about the person"
        ]
    else:
        # Generic alternatives based on category
        if category == 'lexical_bias':
            alternatives = [
                "Use more neutral, descriptive language",
                "Replace emotional words with factual terms", 
                "Choose terminology that doesn't imply judgment"
            ]
        elif category == 'informational_bias':
            alternatives = [
                "Include perspectives from multiple stakeholders",
                "Provide relevant context and background",
                "Present counterarguments or alternative views"
            ]
        elif category == 'demographic_bias':
            alternatives = [
                "Avoid broad generalizations about groups",
                "Focus on specific individuals or documented cases",
                "Use inclusive language that doesn't stereotype"
            ]
        elif category == 'epistemological_bias':
            alternatives = [
                "Attribute claims to specific sources",
                "Use qualifying language (may, appears, suggests)",
                "Distinguish clearly between facts and opinions"
            ]
    
    return alternatives[:3] if alternatives else ["Use more objective language", "Provide balanced perspective", "Include source attribution"]

def check_context_balance(text: str, full_article: str) -> bool:
    """Check if balancing information is provided elsewhere in article"""
    # Simple check - in real implementation this would be more sophisticated
    balance_indicators = [
        'however', 'but', 'on the other hand', 'critics argue', 'supporters say',
        'alternative view', 'different perspective', 'counterargument', 'in contrast'
    ]
    
    return any(indicator in full_article.lower() for indicator in balance_indicators)

def create_bias_visualization_bar(score: float) -> str:
    """Create HTML for bias visualization bar"""
    # Normalize score to 0-100 for positioning
    position = ((score + 10) / 20) * 100
    position = max(0, min(100, position))
    
    color = "red" if score > 2 else "orange" if score > 0 else "blue" if score < -2 else "orange" if score < 0 else "green"
    
    return f"""
    <div style="width: 100%; height: 20px; background: linear-gradient(to right, #ff4444 0%, #ff8844 25%, #44ff44 45%, #44ff44 55%, #ff8844 75%, #ff4444 100%); border-radius: 10px; position: relative; margin: 5px 0;">
        <div style="position: absolute; top: 0; left: {position}%; width: 4px; height: 100%; background: black; border-radius: 2px;"></div>
        <div style="text-align: center; font-size: 8px; color: white; line-height: 20px;">Left ← → Right</div>
    </div>
    """

def expand_missing_perspectives(original_perspectives: list, article_text: str) -> list:
    """Expand missing perspectives with specific angles and severity"""
    expanded = []
    
    # Always include these standard missing perspectives for political articles
    standard_perspectives = [
        {
            'perspective': 'Military Strategic Analysis',
            'severity': 'Moderate',
            'specific_angles': [
                'Tactical implications of current operations',
                'Strategic objectives and military planning',
                'Resource allocation and logistics considerations',
                'International military cooperation aspects'
            ],
            'suggested_sources': ['Defense News', 'Military Times', 'Jane\'s Defence Weekly', 'Armed Forces experts'],
            'impact': 'Missing military context may lead to incomplete understanding of conflict dynamics',
            'confidence': 0.75
        },
        {
            'perspective': 'International Law Framework',
            'severity': 'Major',
            'specific_angles': [
                'Geneva Convention compliance analysis',
                'International Court of Justice precedents',
                'UN Charter violation assessments', 
                'War crimes investigation procedures'
            ],
            'suggested_sources': ['International Court of Justice', 'UN Human Rights Council', 'Legal scholars', 'Amnesty International'],
            'impact': 'Legal framework absence hinders proper accountability assessment',
            'confidence': 0.85
        },
        {
            'perspective': 'Humanitarian Impact Assessment',
            'severity': 'High',
            'specific_angles': [
                'Civilian casualty verification methods',
                'Refugee and displacement statistics',
                'Medical facility and school damage reports',
                'Long-term psychological trauma studies'
            ],
            'suggested_sources': ['UN OCHA', 'Doctors Without Borders', 'Red Cross/Red Crescent', 'Local humanitarian NGOs'],
            'impact': 'Humanitarian gaps reduce understanding of human cost',
            'confidence': 0.90
        },
        {
            'perspective': 'Economic and Resource Analysis',
            'severity': 'Moderate',
            'specific_angles': [
                'Infrastructure damage economic impact',
                'Regional trade disruption effects',
                'Energy supply chain implications',
                'Reconstruction cost projections'
            ],
            'suggested_sources': ['World Bank', 'Regional economic institutions', 'Trade organizations', 'Economic analysts'],
            'impact': 'Economic context missing affects long-term consequence understanding',
            'confidence': 0.70
        }
    ]
    
    # Add original perspectives if they exist
    for orig in original_perspectives:
        if isinstance(orig, dict):
            expanded.append(orig)
    
    # Add standard perspectives if not already covered
    existing_types = [p.get('perspective', '').lower() for p in expanded]
    
    for std_perspective in standard_perspectives:
        perspective_type = std_perspective['perspective'].lower()
        if not any(existing_type in perspective_type or perspective_type in existing_type for existing_type in existing_types):
            expanded.append(std_perspective)
    
    return expanded[:6]  # Limit to 6 total

def enhance_comparative_analysis(original_comparative: dict, overall_score: float, article_text: str) -> dict:
    """Enhance comparative analysis with concrete examples and distance scores"""
    enhanced = original_comparative.copy() if original_comparative else {}
    
    # Generate framing examples based on bias score
    if overall_score < -2:  # Left-leaning
        enhanced.update({
            'likely_left_framing': enhanced.get('likely_left_framing', 'Emphasize humanitarian concerns and civilian impact'),
            'likely_right_framing': enhanced.get('likely_right_framing', 'Focus on security threats and defensive measures'),
            'neutral_baseline': enhanced.get('neutral_baseline', 'Report verified facts with multiple source attribution'),
            'left_examples': ['Highlight civilian casualties prominently', 'Frame as humanitarian crisis'],
            'right_examples': ['Emphasize security justifications', 'Frame as defensive action'],
            'current_proximity': 'Left-leaning outlets (CNN, MSNBC)',
            'most_similar_outlet': 'CNN or Washington Post'
        })
    elif overall_score > 2:  # Right-leaning
        enhanced.update({
            'likely_left_framing': enhanced.get('likely_left_framing', 'Criticize military action and emphasize casualties'),
            'likely_right_framing': enhanced.get('likely_right_framing', 'Support security measures and national defense'),
            'neutral_baseline': enhanced.get('neutral_baseline', 'Present multiple perspectives with clear attribution'),
            'left_examples': ['Question military necessity', 'Emphasize international condemnation'],
            'right_examples': ['Support defensive measures', 'Highlight security achievements'],
            'current_proximity': 'Right-leaning outlets (Fox News, NY Post)',
            'most_similar_outlet': 'Fox News or Wall Street Journal'
        })
    else:  # Neutral
        enhanced.update({
            'likely_left_framing': enhanced.get('likely_left_framing', 'Focus on humanitarian impact and civilian protection'),
            'likely_right_framing': enhanced.get('likely_right_framing', 'Emphasize security needs and defensive measures'),
            'neutral_baseline': enhanced.get('neutral_baseline', 'Balanced reporting with multiple perspectives'),
            'left_examples': ['Prioritize humanitarian angle', 'Question proportionality'],
            'right_examples': ['Support security rationale', 'Emphasize threat reduction'],
            'current_proximity': 'Center/Neutral outlets',
            'most_similar_outlet': 'Reuters, AP, or NPR'
        })
    
    return enhanced

def analyze_bias_interactions(category_scores: dict, overall_score: float) -> list:
    """Analyze how different bias types reinforce each other"""
    interactions = []
    
    # Check which categories show significant bias
    biased_categories = {cat: data for cat, data in category_scores.items() 
                        if abs(data.get('score', 0)) > 1}
    
    if len(biased_categories) >= 2:
        # Lexical + Informational interaction
        if 'lexical_bias' in biased_categories and 'informational_bias' in biased_categories:
            interactions.append({
                'interaction_type': 'Lexical × Informational Bias Amplification',
                'mechanism': 'Emotionally charged language amplifies the impact of selective information omission',
                'amplification': 'High - emotional framing makes missing context less noticeable',
                'example': 'Using "devastating attacks" while omitting defensive context creates stronger bias impression',
                'impact_level': 'High'
            })
        
        # Demographic + Epistemological interaction
        if 'demographic_bias' in biased_categories and 'epistemological_bias' in biased_categories:
            interactions.append({
                'interaction_type': 'Demographic × Epistemological Bias Reinforcement',
                'mechanism': 'Group stereotypes presented as factual certainty rather than opinion',
                'amplification': 'Medium - false certainty makes stereotypes seem more credible',
                'example': 'Presenting group generalizations without qualification or evidence',
                'impact_level': 'Medium'
            })
        
        # Informational + Epistemological interaction  
        if 'informational_bias' in biased_categories and 'epistemological_bias' in biased_categories:
            interactions.append({
                'interaction_type': 'Informational × Epistemological Bias Synergy',
                'mechanism': 'Information omissions increase impact of presenting opinion as settled fact',
                'amplification': 'High - missing counterarguments make false certainty more convincing',
                'example': 'Stating definitive conclusions while omitting contradictory evidence',
                'impact_level': 'High'
            })
        
        # All categories interaction
        if len(biased_categories) >= 3:
            interactions.append({
                'interaction_type': 'Multi-Category Systemic Bias Pattern',
                'mechanism': 'Multiple bias types create reinforcing echo chamber effect',
                'amplification': 'Very High - creates comprehensive bias framework',
                'example': 'Combining emotional language, selective facts, group stereotypes, and false certainty',
                'impact_level': 'High'
            })
    
    return interactions

def enhance_actionable_feedback(original_feedback: dict, category_scores: dict, overall_score: float, missing_perspectives: list) -> dict:
    """Generate enhanced, specific actionable feedback"""
    enhanced = {}
    
    # Generate reader takeaways based on specific bias patterns
    reader_takeaways = []
    
    if category_scores.get('lexical_bias', {}).get('score', 0) != 0:
        reader_takeaways.append("Be aware of emotionally loaded language that may frame events with inherent bias")
    
    if category_scores.get('informational_bias', {}).get('score', 0) != 0:
        reader_takeaways.append("Seek additional sources to fill information gaps and missing perspectives")
    
    if category_scores.get('demographic_bias', {}).get('score', 0) != 0:
        reader_takeaways.append("Watch for group generalizations and seek individual stories over stereotypes")
    
    if category_scores.get('epistemological_bias', {}).get('score', 0) != 0:
        reader_takeaways.append("Distinguish between factual reporting and opinion presented as certainty")
    
    # Media literacy guidance
    media_literacy = []
    
    if overall_score > 2:
        media_literacy.extend([
            "This article leans right - seek left-leaning and neutral sources for balance",
            "Pay attention to which voices and perspectives are prioritized or omitted",
            "Consider how the framing might differ in outlets with different political orientations"
        ])
    elif overall_score < -2:
        media_literacy.extend([
            "This article leans left - seek right-leaning and neutral sources for balance", 
            "Notice which aspects of the story receive emphasis or minimal coverage",
            "Compare with conservative and centrist outlet coverage of the same events"
        ])
    else:
        media_literacy.extend([
            "While relatively balanced, all sources have some inherent perspective",
            "Cross-reference with multiple sources to build complete understanding",
            "Notice subtle framing choices even in neutral-appearing coverage"
        ])
    
    # Author feedback
    author_feedback = [
        "Use more precise, neutral terminology instead of emotional descriptors",
        "Include perspectives from all major stakeholders in the conflict",
        "Provide clear source attribution for all significant claims",
        "Balance reporting of different viewpoints rather than emphasizing one side"
    ]
    
    # Editor feedback  
    editor_feedback = [
        "Review for subtle bias in headline and subhead phrasing",
        "Ensure quotes represent range of viewpoints proportionally",
        "Check that statistical data includes relevant context and comparison",
        "Verify that opinion elements are clearly labeled and separated from news"
    ]
    
    enhanced.update({
        'reader_takeaways': reader_takeaways,
        'media_literacy': media_literacy,
        'author_feedback': author_feedback,
        'editor_feedback': editor_feedback
    })
    
    return enhanced

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
        # Enhanced BABE Score interpretation
        if overall_score > 2:
            st.error(f"**BABE Bias Score**\n{overall_score}/10\n(Right-leaning)")
            interpretation = "This indicates moderate to strong right-leaning bias across multiple categories."
        elif overall_score < -2:
            st.error(f"**BABE Bias Score**\n{overall_score}/10\n(Left-leaning)")
            interpretation = "This indicates moderate to strong left-leaning bias across multiple categories."
        else:
            st.success(f"**BABE Bias Score**\n{overall_score}/10\n(Neutral)")
            interpretation = "This indicates relatively balanced coverage with minimal detectable bias."
        
        # Show confidence interval with plain language explanation
        st.caption(f"95% CI: [{confidence_interval[0]:.1f}, {confidence_interval[1]:.1f}]")
        st.caption(f"The true bias score is likely between {confidence_interval[0]:.1f} and {confidence_interval[1]:.1f}")
        
        # Visual bias indicator bar
        bias_bar_html = create_bias_visualization_bar(overall_score)
        st.markdown(bias_bar_html, unsafe_allow_html=True)
        
        # Score interpretation
        st.info(f"**Interpretation:** {interpretation}")
    
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
    
    # Create interactive category display with enhanced structure
    tab1, tab2, tab3, tab4 = st.tabs(["📝 Lexical Bias", "📰 Informational Bias", "👥 Demographic Bias", "🧠 Epistemological Bias"])
    
    categories = ['lexical_bias', 'informational_bias', 'demographic_bias', 'epistemological_bias']
    tab_mapping = [tab1, tab2, tab3, tab4]
    
    # Category explanations for better structure
    category_explanations = {
        'lexical_bias': "Measures emotional language, value-laden adjectives, and word choice that frames events with inherent bias.",
        'informational_bias': "Evaluates selective omission, cherry-picked statistics, and missing context that skews understanding.", 
        'demographic_bias': "Identifies unfair representation of groups through stereotyping, tokenism, or systematic exclusion.",
        'epistemological_bias': "Detects opinion presented as fact, false certainty, and poor attribution of claims."
    }
    
    for i, (category, tab) in enumerate(zip(categories, tab_mapping)):
        with tab:
            cat_data = category_scores.get(category, {})
            
            # Add category explanation at the top
            st.markdown(f"**What this measures:** {category_explanations[category]}")
            st.markdown("---")
            
            # Enhanced scoring with severity indicators
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                score = cat_data.get('score', 0)
                severity = "High" if abs(score) > 3 else "Moderate" if abs(score) > 1.5 else "Low"
                severity_color = "🔴" if abs(score) > 3 else "🟡" if abs(score) > 1.5 else "🟢"
                
                if abs(score) > 2:
                    st.error(f"**Score: {score}**")
                elif abs(score) > 1:
                    st.warning(f"**Score: {score}**")
                else:
                    st.success(f"**Score: {score}**")
                st.caption(f"{severity_color} **Severity:** {severity}")
            
            with col2:
                precision = cat_data.get('precision', 0)
                st.metric("Precision", f"{precision:.3f}", help="How many detected biases are actually biased")
            
            with col3:
                recall = cat_data.get('recall', 0)
                st.metric("Recall", f"{recall:.3f}", help="How many actual biases were detected")
            
            with col4:
                f1_score = cat_data.get('f1_score', 0)
                st.metric("F1-Score", f"{f1_score:.3f}", help="Balanced measure of precision and recall")
            
            # Enhanced Evidence Presentation
            evidence = cat_data.get('evidence', [])
            if evidence:
                st.markdown("**📋 Evidence Analysis:**")
                for idx, item in enumerate(evidence[:5]):  # Limit to 5 items
                    with st.expander(f"Evidence {idx+1}: \"{item[:60]}...\""):
                        # Extract or generate bias rule explanation
                        bias_rule = get_bias_rule_explanation(item, category)
                        
                        st.markdown(f"**🎯 Biased Text:** \"{item}\"")
                        st.markdown(f"**📖 Bias Type:** {bias_rule}")
                        
                        # Generate multiple neutral alternatives
                        neutral_alternatives = generate_neutral_alternatives(item, category)
                        st.markdown("**🔄 Neutral Alternatives:**")
                        for alt_idx, alt in enumerate(neutral_alternatives[:3], 1):
                            st.markdown(f"  {alt_idx}. {alt}")
                        
                        # Context check
                        context_available = check_context_balance(item, full_result.get('full_text', ''))
                        context_status = "✅ Yes" if context_available else "❌ No"
                        st.markdown(f"**⚖️ Balancing Information Provided:** {context_status}")
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
    
    # === EXPANDED MISSING PERSPECTIVES ===
    missing_perspectives = full_result.get('missing_perspectives', [])
    if missing_perspectives or overall_score != 0:  # Show even if empty but biased
        st.markdown("### ❓ Missing Perspectives Analysis")
        
        # Expand missing perspectives with specific angles
        expanded_perspectives = expand_missing_perspectives(missing_perspectives, full_result.get('full_text', ''))
        
        for perspective in expanded_perspectives[:6]:  # Show up to 6 perspectives
            severity = perspective.get('severity', 'Moderate')
            severity_emoji = {"Major": "🔴", "Moderate": "🟡", "Minor": "🟢"}.get(severity, "🟡")
            
            with st.expander(f"{severity_emoji} {perspective.get('perspective', 'Unknown perspective')} ({severity} omission)"):
                st.markdown(f"**📊 Impact:** {perspective.get('impact', 'Unknown impact')}")
                st.markdown(f"**🎯 Specific Missing Angles:**")
                
                angles = perspective.get('specific_angles', [])
                for angle in angles[:4]:  # Show up to 4 specific angles
                    st.markdown(f"  • {angle}")
                
                st.markdown(f"**📰 Suggested Sources for Balance:**")
                sources = perspective.get('suggested_sources', [])
                for source in sources[:4]:
                    st.markdown(f"  • {source}")
                    
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Confidence", f"{perspective.get('confidence', 0):.0%}")
                with col2:
                    st.metric("Severity", severity)
    
    # === ENHANCED COMPARATIVE ANALYSIS ===
    comparative = full_result.get('comparative_analysis', {})
    if comparative or overall_score != 0:  # Show even if no data but article is biased
        st.markdown("### ⚖️ Cross-Source Framing Comparison")
        
        # Generate or enhance comparative analysis
        enhanced_comparative = enhance_comparative_analysis(comparative, overall_score, full_result.get('full_text', ''))
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**🔵 Likely Left Framing:**")
            left_framing = enhanced_comparative.get('likely_left_framing', 'Focus on humanitarian impact and civilian casualties.')
            st.info(left_framing)
            
            # Add concrete examples
            left_examples = enhanced_comparative.get('left_examples', [])
            if left_examples:
                st.markdown("**Examples:**")
                for ex in left_examples[:2]:
                    st.caption(f"• {ex}")
        
        with col2:
            st.markdown("**🟢 Neutral Baseline:**")
            neutral_baseline = enhanced_comparative.get('neutral_baseline', 'Report facts with multiple source attribution.')
            st.success(neutral_baseline)
            
            # Distance from neutral with visual indicator
            distance_from_neutral = abs(overall_score) / 10.0
            st.metric("Distance from Neutral", f"{distance_from_neutral:.2f}", 
                     help="0.0 = perfectly neutral, 1.0 = maximum bias")
        
        with col3:
            st.markdown("**🔴 Likely Right Framing:**")
            right_framing = enhanced_comparative.get('likely_right_framing', 'Emphasize security concerns and national interests.')
            st.error(right_framing)
            
            # Add concrete examples
            right_examples = enhanced_comparative.get('right_examples', [])
            if right_examples:
                st.markdown("**Examples:**")
                for ex in right_examples[:2]:
                    st.caption(f"• {ex}")
        
        # Enhanced proximity analysis
        current_proximity = enhanced_comparative.get('current_proximity', 'Neutral baseline')
        similar_outlet = enhanced_comparative.get('most_similar_outlet', 'Reuters/AP')
        
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"**📊 This Article Closest To:** {current_proximity}")
        with col2:
            st.markdown(f"**📰 Most Similar Outlet:** {similar_outlet}")
            st.caption("Based on framing patterns and bias indicators")
    
    # === NEW: BIAS INTERACTION ANALYSIS ===
    if overall_score != 0:  # Only show if bias is detected
        st.markdown("### 🧩 Bias Interaction Analysis")
        
        bias_interactions = analyze_bias_interactions(category_scores, overall_score)
        
        st.markdown("**How Different Bias Types Reinforce Each Other:**")
        for interaction in bias_interactions[:4]:  # Show top 4 interactions
            with st.expander(f"🔗 {interaction.get('interaction_type', 'Unknown Interaction')}"):
                st.markdown(f"**🎯 Mechanism:** {interaction.get('mechanism', 'Not specified')}")
                st.markdown(f"**📈 Amplification Effect:** {interaction.get('amplification', 'Unknown')}")
                st.markdown(f"**🔍 Example:** {interaction.get('example', 'Not provided')}")
                
                impact_level = interaction.get('impact_level', 'Medium')
                impact_color = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(impact_level, "🟡")
                st.markdown(f"**{impact_color} Impact Level:** {impact_level}")
    
    # === ENHANCED ACTIONABLE FEEDBACK ===
    feedback = full_result.get('actionable_feedback', {})
    if feedback or overall_score != 0:  # Generate feedback even if not provided
        st.markdown("### 💡 Enhanced Actionable Recommendations")
        
        enhanced_feedback = enhance_actionable_feedback(feedback, category_scores, overall_score, missing_perspectives)
        
        tab1, tab2, tab3, tab4 = st.tabs(["👥 What This Means for Readers", "✏️ For Authors", "📝 For Editors", "🔍 Model Insights"])
        
        with tab1:
            st.markdown("**🎯 Reader Takeaway (Key Points to Remember):**")
            reader_takeaways = enhanced_feedback.get('reader_takeaways', [])
            for idx, takeaway in enumerate(reader_takeaways[:4], 1):
                st.markdown(f"**{idx}.** {takeaway}")
            
            st.markdown("---")
            st.markdown("**📚 Media Literacy Guidance:**")
            literacy_guidance = enhanced_feedback.get('media_literacy', [])
            for guidance in literacy_guidance[:3]:
                st.info(f"💡 {guidance}")
        
        with tab2:
            author_feedback = enhanced_feedback.get('author_feedback', [])
            for feedback_item in author_feedback:
                st.markdown(f"• {feedback_item}")
        
        with tab3:
            editor_feedback = enhanced_feedback.get('editor_feedback', [])
            for feedback_item in editor_feedback:
                st.markdown(f"• {feedback_item}")
        
        # === NEW: MODEL TRANSPARENCY SECTION ===
        with tab4:
            st.markdown("**🔬 Analysis Methodology Transparency:**")
            
            # Explain metrics in plain language
            st.markdown("**📊 Metric Explanations:**")
            st.markdown("""
            - **Precision**: How accurate our bias detection is (fewer false positives)
            - **Recall**: How complete our bias detection is (fewer missed biases)
            - **F1-Score**: Balanced measure combining precision and recall
            - **Confidence Interval**: Range where the true bias score likely falls
            """)
            
            # Model limitations
            st.markdown("**⚠️ Analysis Limitations:**")
            limitations = [
                "Bias detection is probabilistic and may not capture sarcasm or complex rhetorical framing",
                "Cultural and contextual nuances may be missed in automated analysis", 
                "Short articles provide less context for comprehensive bias assessment",
                "Analysis focuses on observable patterns, not author intent",
                "Cross-cultural bias patterns may vary from training data"
            ]
            
            for limitation in limitations:
                st.warning(f"• {limitation}")
            
            # Analysis confidence and calibration
            st.markdown("**✅ Quality Indicators:**")
            quality_metrics = {
                "Analysis Confidence": f"{evidence_strength.title()} evidence strength",
                "Cross-Validation": f"{int(cross_validation.get('expert_consensus', 0) * 100)}% expert consensus", 
                "Sample Size": f"{len(highlighted_evidence)} bias instances analyzed",
                "Category Coverage": f"{len([c for c in category_scores.values() if c.get('score', 0) != 0])}/4 categories show bias"
            }
            
            for metric, value in quality_metrics.items():
                st.success(f"**{metric}:** {value}")
        
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
    if analysis_mode in ["Single Summary", "Bias Analysis"]:
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
            if analysis_mode in ["Bias Analysis"]:
                st.markdown("### 📋 Article Metadata (Optional - Enhances Bias Analysis)")
                
                # Check if we have auto-detected metadata from URL fetch or file upload
                has_auto_title = 'fetched_title' in st.session_state and st.session_state['fetched_title']
                has_auto_url = 'fetched_url' in st.session_state and st.session_state['fetched_url']
                
                # Checkbox to enable/disable metadata inclusion
                include_metadata = st.checkbox(
                    "🏷️ Include article metadata for enhanced analysis",
                    value=has_auto_title or has_auto_url,
                    help="Including title and source improves bias detection accuracy"
                )
                
                if include_metadata:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        # Auto-populate title if available, otherwise show input
                        if has_auto_title:
                            article_title = st.text_input(
                                "Article Title",
                                value=st.session_state['fetched_title'],
                                help="Auto-detected from article. You can edit if needed."
                            )
                        else:
                            article_title = st.text_input(
                                "Article Title",
                                placeholder="Enter the article headline/title",
                                help="Helps with contextual analysis"
                            )
                    
                    with col2:
                        # Auto-populate URL if available, otherwise show input
                        if has_auto_url:
                            source_url = st.text_input(
                                "Source URL or Domain",
                                value=st.session_state['fetched_url'],
                                help="Auto-detected from URL input. You can edit if needed."
                            )
                        else:
                            source_url = st.text_input(
                                "Source URL or Domain", 
                                placeholder="e.g., cnn.com, foxnews.com, reuters.com",
                                help="Enables source bias profiling and publisher context"
                            )
                    
                    # Show what metadata will be included
                    if article_title or source_url:
                        st.success(f"✅ Metadata included: {f'Title: {article_title[:50]}...' if article_title else ''}{' | ' if article_title and source_url else ''}{f'Source: {source_url}' if source_url else ''}")
                else:
                    article_title = None
                    source_url = None
                    st.info("💡 **Tip:** Including metadata significantly improves bias analysis accuracy by providing context about the source and framing.")
            else:
                article_title = None
                source_url = None
            
            # Analysis button
            analysis_label = {
                "Single Summary": "📝 Generate Summary",
                "Bias Analysis": "🎯 Analyze Bias"
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
    
    else:  # Source Convergence Analysis
        if analysis_mode == "Source Convergence Analysis":
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
                                    extraction_method = extracted_topics.get('extraction_method', 'ai')
                                    
                                    if extraction_method == 'local':
                                        st.success(f"✅ **Local Topic Extraction Completed!**")
                                        st.info(f"**Method:** Text analysis (no API key required)")
                                    else:
                                        st.success(f"✨ **AI Topic Extraction Successful!**")
                                        st.info(f"**Method:** {settings['model'].upper()} AI analysis")
                                    
                                    st.info(f"**Original Title:** {result['title']}")
                                    st.info(f"**Key Topics Found:** {topic_query}")
                                    
                                    # Show the summary that was used for extraction - auto-expanded for transparency
                                    with st.expander("📄 Article Analysis Used for Topic Extraction", expanded=True):
                                        st.markdown(f"**Summary:** {extracted_topics['summary']}")
                                        st.markdown(f"**Key Themes:** {', '.join(extracted_topics['themes'])}")
                                        st.markdown("---")
                                        if extraction_method == 'local':
                                            st.markdown("🔍 **Local Analysis:** Keywords extracted using text analysis patterns.")
                                        else:
                                            st.markdown("🎯 **AI Analysis:** Advanced topic modeling and summarization used.")
                                        st.markdown("**This information will be used to find related articles across diverse news sources.**")
                                    
                                    # Store all extracted information for seamless workflow
                                    st.session_state['extracted_topic'] = topic_query
                                    st.session_state['extraction_method'] = extraction_method
                                    st.session_state['original_url'] = initial_url
                                    st.session_state['original_title'] = result['title']
                                    st.session_state['article_content'] = result['content']
                                    st.session_state['extraction_data'] = extracted_topics
                                else:
                                    # Enhanced fallback handling with specific user guidance
                                    topic_query = result['title']
                                    fallback_reason = extracted_topics.get('fallback_reason', 'unknown')
                                    
                                    if fallback_reason == 'no_api_key':
                                        st.error("🚫 **Smart Topic Extraction Failed: Missing API Key**")
                                        st.markdown("""
                                        **Issue:** AI-powered topic extraction requires an API key for the selected model.
                                        
                                        **Quick Fix Options:**
                                        1. **Add API Key:** Enter your OpenAI API key in the sidebar → 🔑 API Keys
                                        2. **Switch to Local Mode:** Change model to 'local' in the sidebar (basic extraction)
                                        3. **Manual Topic:** Use 'Search by Topic' mode instead and enter your own search terms
                                        
                                        **Current Fallback:** Using article title as search term (less accurate results expected)
                                        """)
                                        st.info(f"**Fallback Search Term:** {topic_query}")
                                    elif fallback_reason == 'config_error':
                                        st.error("⚠️ **Smart Topic Extraction Failed: Configuration Error**")
                                        st.markdown("""
                                        **Issue:** There was a problem setting up the AI analysis engine.
                                        
                                        **Suggested Actions:**
                                        1. Check that your API key is valid
                                        2. Try switching to 'local' model mode
                                        3. Refresh the page and try again
                                        
                                        **Current Fallback:** Using article title as search term
                                        """)
                                    else:
                                        st.warning("⚠️ **Smart Topic Extraction Failed: AI Analysis Error**")
                                        st.info(f"**Fallback:** Using article title as search term: '{topic_query}'")
                                        st.caption("💡 **Tip:** For better results, ensure your API key is valid or try the 'Search by Topic' mode.")
                                    
                                    st.session_state['extracted_topic'] = topic_query
                                    st.session_state['extraction_method'] = 'title_fallback'
                                    st.session_state['extraction_error'] = extracted_topics.get('error', 'Unknown error')
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
                    display_convergence_analysis_results(data, settings)
                else:
                    st.info("No convergence analysis results yet. Use the 'Topic Search' tab to analyze multiple sources.")
                    
                    with st.expander("💡 What is a Truth Map?", expanded=True):
                        st.markdown("""
                        **The Truth Map** is a sophisticated analysis that goes beyond simple fact-checking:
                        
                        **🗺️ What You'll See:**
                        • **Widely Reported**: Claims most sources agree on (high confidence)
                        • **Disputed/Framed Differently**: Same facts, different interpretation
                        • **Missing from Some Coverage**: What some sources report but others omit
                        • **Source Perspective Distances**: How differently sources tell the story
                        
                        **🎯 Why This Matters:**
                        Instead of claiming to find "the truth," this system shows you:
                        - What sources agree/disagree on
                        - How bias and framing affect coverage  
                        - Information gaps you should investigate
                        - The complexity behind seemingly simple stories
                        
                        **🔬 The Method:**
                        1. **Claim Extraction**: Break articles into atomic factual statements
                        2. **Similarity Clustering**: Group the same claims expressed differently  
                        3. **Agreement Scoring**: Weight by source diversity and consistency
                        4. **Framing Analysis**: Detect sentiment and loaded language differences
                        5. **Omission Detection**: Find claims missing from some sources
                        6. **Truth Mapping**: Honest synthesis of what's agreed, contested, and missing
                        """)
            
def display_truth_map(truth_map, topic, source_analysis, num_sources):
    """
    Display the enhanced Truth Map analysis results.
    """
    st.markdown(f"# 🗺️ Truth Map: {topic}")
    st.caption(f"Analysis completed: {truth_map.get('timestamp', 'Unknown time')}")
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Sources Analyzed", num_sources)
    
    with col2:
        st.metric("Claims Extracted", truth_map.get('claims_extracted', 0))
    
    with col3:
        widely_reported = len(truth_map.get('widely_reported', []))
        st.metric("Widely Agreed", widely_reported, 
                 help="Claims reported by most sources with high confidence")
    
    with col4:
        disputed = len(truth_map.get('disputed_framed_differently', []))
        st.metric("Disputed/Framed", disputed,
                 help="Claims with different framing or limited agreement")
    
    # Source Analysis
    st.markdown("## 📊 Source Analysis")
    
    if source_analysis:
        import pandas as pd
        
        # Create source analysis table
        source_df = pd.DataFrame([
            {
                'Source': s['source'],
                'Political Bias': f"{s['bias_score']:+d}" if s['bias_score'] != 0 else "Neutral",
                'Credibility': f"{s['credibility']}/10",
                'Bias Direction': "Left" if s['bias_score'] < 0 else "Right" if s['bias_score'] > 0 else "Center"
            }
            for s in source_analysis
        ])
        
        st.dataframe(source_df, use_container_width=True, hide_index=True)
        
        # Perspective distances
        if truth_map.get('source_perspective_distances'):
            st.markdown("### 🔄 Source Perspective Distances")
            st.caption("How differently sources are telling the story")
            
            for distance in truth_map['source_perspective_distances'][:5]:  # Show top 5
                interpretation = distance['interpretation']
                
                if interpretation == 'similar_stories':
                    icon = "🟢"
                    desc = "Very similar coverage"
                elif interpretation == 'different_emphasis':
                    icon = "🟡"
                    desc = "Same story, different emphasis"
                else:
                    icon = "🔴"
                    desc = "Fundamentally different stories"
                
                st.markdown(f"{icon} **{distance['source_pair']}**: {desc} "
                           f"(Overlap: {distance['story_overlap']:.1%})")
    
    # The Truth Map - Main Results
    st.markdown("## 🗺️ The Truth Map")
    st.markdown("*This system doesn't claim to show 'the truth' — it shows what's agreed on, contested, and missing.*")
    
    # Widely Reported Section
    if truth_map.get('widely_reported'):
        st.markdown("### ✅ Widely Reported")
        st.markdown("*Claims reported by most sources with high confidence*")
        
        for claim_info in truth_map['widely_reported']:
            with st.expander(f"📄 {claim_info['claim'][:100]}...", expanded=False):
                st.markdown(f"**Full Claim:** {claim_info['claim']}")
                st.markdown(f"**Sources Reporting:** {', '.join(claim_info['sources_reporting'])}")
                st.markdown(f"**Confidence Score:** {claim_info['confidence']:.2f}")
                st.markdown(f"**Source Count:** {claim_info['source_count']}/{num_sources} sources")
                
                # Confidence interpretation
                if claim_info['confidence'] > 0.8:
                    st.success("🟢 **High Confidence** - Widely agreed upon across sources")
                elif claim_info['confidence'] > 0.6:
                    st.info("🟡 **Medium Confidence** - Generally agreed upon")
                else:
                    st.warning("🟠 **Lower Confidence** - Some agreement but limited sources")
    else:
        st.markdown("### ✅ Widely Reported")
        st.info("No claims achieved wide agreement across sources")
    
    # Disputed/Framed Differently Section
    if truth_map.get('disputed_framed_differently'):
        st.markdown("### ⚖️ Disputed / Framed Differently")
        st.markdown("*Claims where sources disagree or use different framing*")
        
        for claim_info in truth_map['disputed_framed_differently']:
            framing = claim_info.get('framing_differences', {})
            
            with st.expander(f"⚖️ {claim_info['claim'][:100]}...", expanded=False):
                st.markdown(f"**Full Claim:** {claim_info['claim']}")
                st.markdown(f"**Sources Reporting:** {', '.join(claim_info['sources_reporting'])}")
                st.markdown(f"**Confidence Score:** {claim_info['confidence']:.2f}")
                
                # Framing analysis
                if framing.get('sentiment_range') and len(framing['sentiment_range']) > 1:
                    st.markdown(f"**Sentiment Variation:** {', '.join(framing['sentiment_range'])}")
                
                if framing.get('loaded_language_detected'):
                    st.warning("⚠️ Loaded language detected in some coverage")
                
                if framing.get('emphasis_variations'):
                    st.info("📏 Varying levels of detail/emphasis across sources")
                
                st.markdown("**Why This Matters:** Different framing can significantly influence reader perception of the same facts.")
    else:
        st.markdown("### ⚖️ Disputed / Framed Differently")
        st.success("High consensus - sources show similar framing")
    
    # Missing from Some Coverage Section
    if truth_map.get('missing_from_some_coverage'):
        st.markdown("### ⚠️ Missing from Some Coverage")
        st.markdown("*Claims reported by some sources but omitted by others*")
        
        for omission in truth_map['missing_from_some_coverage']:
            importance = omission['importance']
            icon = "🚨" if importance == 'significant' else "⚠️"
            
            with st.expander(f"{icon} {omission['claim'][:100]}...", expanded=False):
                st.markdown(f"**Full Claim:** {omission['claim']}")
                st.markdown(f"**Reported By:** {', '.join(omission['reported_by'])}")
                st.markdown(f"**Omitted By:** {', '.join(omission['omitted_by'])}")
                st.markdown(f"**Importance Level:** {importance.title()}")
                
                if omission.get('potential_reasons'):
                    st.markdown("**Potential Reasons for Omission:**")
                    reason_map = {
                        'controversial_framing': '🔥 Controversial or sensitive topic',
                        'crisis_narrative': '📰 Crisis/emergency framing differences', 
                        'political_sensitivity': '🏛️ Political implications'
                    }
                    
                    for reason in omission['potential_reasons']:
                        st.markdown(f"• {reason_map.get(reason, reason)}")
                
                if importance == 'significant':
                    st.error("🚨 **Significant Omission** - Important information missing from multiple sources")
                else:
                    st.warning("⚠️ **Notable Omission** - Worth investigating why some sources didn't cover this")
    else:
        st.markdown("### ⚠️ Missing from Some Coverage")
        st.success("Comprehensive coverage - no major omissions detected")
    
    # Methodology and Limitations
    with st.expander("🔬 Methodology & Limitations", expanded=False):
        st.markdown("### How This Analysis Works")
        
        methodology_notes = truth_map.get('methodological_notes', [])
        for note in methodology_notes:
            st.markdown(f"• {note}")
        
        st.markdown("### Important Limitations")
        st.markdown("""
        **What This System Does:**
        - ✅ Shows what sources agree/disagree on
        - ✅ Makes bias and framing visible
        - ✅ Identifies information gaps
        - ✅ Provides transparency about methodology
        
        **What This System Doesn't Do:**
        - ❌ Determine absolute truth
        - ❌ Eliminate all bias
        - ❌ Replace critical thinking
        - ❌ Account for all possible perspectives
        
        **Remember:** Facts and interpretation often intertwine. This tool helps you see how different sources construct their narratives, but ultimately you must triangulate reality using your own judgment.
        """)
    
    # Export options
    st.markdown("---")
    st.markdown("## 📥 Export Truth Map")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Create downloadable summary
        summary_text = f"""TRUTH MAP ANALYSIS: {topic}
Generated: {truth_map.get('timestamp', 'Unknown')}

WIDELY REPORTED CLAIMS ({len(truth_map.get('widely_reported', []))}):
"""
        for claim in truth_map.get('widely_reported', []):
            summary_text += f"\n• {claim['claim']}\n  Sources: {', '.join(claim['sources_reporting'])}\n  Confidence: {claim['confidence']:.2f}\n"
        
        summary_text += f"\nDISPUTED/FRAMED DIFFERENTLY ({len(truth_map.get('disputed_framed_differently', []))}):  \n"
        for claim in truth_map.get('disputed_framed_differently', []):
            summary_text += f"\n• {claim['claim']}\n  Sources: {', '.join(claim['sources_reporting'])}\n"
        
        summary_text += f"\nMISSING FROM SOME COVERAGE ({len(truth_map.get('missing_from_some_coverage', []))}):  \n"
        for omission in truth_map.get('missing_from_some_coverage', []):
            summary_text += f"\n• {omission['claim']}\n  Reported by: {', '.join(omission['reported_by'])}\n  Omitted by: {', '.join(omission['omitted_by'])}\n"
        
        st.download_button(
            label="📄 Download Summary",
            data=summary_text,
            file_name=f"truth_map_{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            mime="text/plain"
        )
    
    with col2:
        # JSON export
        import json
        json_data = json.dumps(truth_map, indent=2, ensure_ascii=False)
        st.download_button(
            label="📋 Download JSON", 
            data=json_data,
            file_name=f"truth_map_{topic.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json"
        )
    
    with col3:
        if st.button("🗑️ Clear Results"):
            st.session_state.last_results = None
            st.rerun()

def display_convergence_analysis_results(data, settings):
    """
    Display Source Convergence Analysis results using the new Truth Map format.
    """
    # Check if we have the new truth_map format
    convergence_data = data.get('convergence', {})
    
    if convergence_data.get('truth_map'):
        # New format - display truth map
        truth_map = convergence_data['truth_map']
        display_truth_map(
            truth_map, 
            data['topic'], 
            data.get('source_analysis', []),
            data.get('num_sources_analyzed', 0)
        )
    else:
        # Legacy format fallback
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
            consensus = convergence_data.get('consensus_level', 0)
            consensus_color = "🟢" if consensus > 70 else "🟡" if consensus > 40 else "🔴"
            st.metric("Consensus Level", f"{consensus:.0f}%")
            st.markdown(f"{consensus_color}")
        
        # Basic convergence points display
        st.markdown("## 🎯 Analysis Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### ✅ Convergence Points")
            convergence_points = convergence_data.get('convergence_points', [])
            if convergence_points:
                for point in convergence_points:
                    st.markdown(f"• {point}")
            else:
                st.info("No strong convergence points detected")
        
        with col2:
            st.markdown("### ⚠️ Disputed Claims")
            disputed_claims = convergence_data.get('disputed_claims', [])
            if disputed_claims:
                for claim in disputed_claims:
                    st.markdown(f"• {claim}")
            else:
                st.success("High consensus across sources")
        
        if convergence_data.get('error'):
            st.error(f"Analysis Error: {convergence_data['error']}")

    # Sidebar help
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🆘 Help")
        
        mode_help = {
            "Single Summary": "Generate concise summaries with key points and action items.",
            "Bias Analysis": "Detect political/ideological bias and emotional language.",
            "Source Convergence Analysis": "Find related articles from diverse sources and identify consensus points vs disputed claims."
        }
        
        # Display help for Source Convergence Analysis since we're in that mode
        st.info(mode_help["Source Convergence Analysis"])
        
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