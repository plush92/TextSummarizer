"""
Text Summarizer Module

Handles AI model integration for text summarization.
Supports multiple providers: OpenAI, Anthropic, and local models.
"""

import json
import re
from abc import ABC, abstractmethod
from typing import Dict, List, Any


class BaseSummarizer(ABC):
    """Abstract base class for summarizers"""
    
    @abstractmethod
    def summarize(self, text: str, max_length: int = 150) -> Dict[str, Any]:
        """Generate structured summary of the text"""
        pass


class OpenAISummarizer(BaseSummarizer):
    """OpenAI GPT-based summarizer"""
    
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        try:
            import openai
            self.client = openai.OpenAI(api_key=api_key)
            self.model = model
        except ImportError:
            raise ImportError("OpenAI library not installed. Run: pip install openai")
        except Exception as e:
            raise Exception(f"Failed to initialize OpenAI client: {e}")
    
    def summarize(self, text: str, max_length: int = 150) -> Dict[str, Any]:
        """Generate summary using OpenAI API"""
        prompt = f"""
Please analyze the following text and provide a structured summary with these components:

1. A concise summary (max {max_length} words)
2. 3-5 key bullet points
3. 2-4 actionable items (if any)

Format your response as JSON with the following structure:
{{
    "summary": "Brief summary here...",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "action_items": ["Action 1", "Action 2"]
}}

Text to analyze:
{text}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful text summarization assistant. Always respond with valid JSON in the requested format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extract JSON from response (in case there's extra text)
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                json_str = content
            
            result = json.loads(json_str)
            
            # Validate required fields
            required_fields = ['summary', 'key_points', 'action_items']
            for field in required_fields:
                if field not in result:
                    result[field] = []
            
            return result
            
        except json.JSONDecodeError:
            # Fallback: parse response manually
            return self._manual_parse(content)
        except Exception as e:
            raise Exception(f"OpenAI API error: {e}")
    
    def _manual_parse(self, content: str) -> Dict[str, Any]:
        """Manually parse response if JSON parsing fails"""
        lines = content.split('\n')
        result = {
            'summary': '',
            'key_points': [],
            'action_items': []
        }
        
        current_section = None
        for line in lines:
            line = line.strip()
            if 'summary' in line.lower() and ':' in line:
                result['summary'] = line.split(':', 1)[1].strip()
            elif 'key' in line.lower() and 'point' in line.lower():
                current_section = 'key_points'
            elif 'action' in line.lower():
                current_section = 'action_items'
            elif line.startswith(('-', '•', '*')) or line[0:2].isdigit():
                cleaned_line = re.sub(r'^[-•*\d\.\s]+', '', line)
                if current_section and cleaned_line:
                    result[current_section].append(cleaned_line)
        
        return result


class AnthropicSummarizer(BaseSummarizer):
    """Anthropic Claude-based summarizer"""
    
    def __init__(self, api_key: str, model: str = "claude-3-haiku-20240307"):
        try:
            import anthropic
            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = model
        except ImportError:
            raise ImportError("Anthropic library not installed. Run: pip install anthropic")
        except Exception as e:
            raise Exception(f"Failed to initialize Anthropic client: {e}")
    
    def summarize(self, text: str, max_length: int = 150) -> Dict[str, Any]:
        """Generate summary using Anthropic API"""
        prompt = f"""Please analyze the following text and provide a structured summary:

1. Write a concise summary (max {max_length} words)
2. List 3-5 key bullet points
3. Identify 2-4 actionable items (if any exist in the content)

Text: {text}

Please format your response as JSON:
{{
    "summary": "Brief summary here...",
    "key_points": ["Point 1", "Point 2", "Point 3"],
    "action_items": ["Action 1", "Action 2"]
}}"""
        
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )
            
            content = response.content[0].text.strip()
            
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                result = json.loads(json_str)
            else:
                # Fallback parsing
                result = self._manual_parse(content)
            
            # Validate required fields
            required_fields = ['summary', 'key_points', 'action_items']
            for field in required_fields:
                if field not in result:
                    result[field] = []
            
            return result
            
        except Exception as e:
            raise Exception(f"Anthropic API error: {e}")
    
    def _manual_parse(self, content: str) -> Dict[str, Any]:
        """Manually parse response if JSON parsing fails"""
        # Similar manual parsing logic as OpenAI
        lines = content.split('\n')
        result = {
            'summary': '',
            'key_points': [],
            'action_items': []
        }
        
        current_section = None
        for line in lines:
            line = line.strip()
            if 'summary' in line.lower() and ':' in line:
                result['summary'] = line.split(':', 1)[1].strip()
            elif 'key' in line.lower() and 'point' in line.lower():
                current_section = 'key_points'
            elif 'action' in line.lower():
                current_section = 'action_items'
            elif line.startswith(('-', '•', '*')) or line[0:2].isdigit():
                cleaned_line = re.sub(r'^[-•*\d\.\s]+', '', line)
                if current_section and cleaned_line:
                    result[current_section].append(cleaned_line)
        
        return result


class LocalSummarizer(BaseSummarizer):
    """Local/offline summarizer using simple extraction techniques"""
    
    def __init__(self):
        print("Using local summarizer (basic extraction)")
        print("Note: For better results, use OpenAI or Anthropic models")
    
    def summarize(self, text: str, max_length: int = 150) -> Dict[str, Any]:
        """Generate basic summary using local text processing"""
        
        # Split into sentences
        sentences = self._split_sentences(text)
        
        # Extract key sentences (simple approach)
        key_sentences = self._extract_key_sentences(sentences, max_length // 20)
        
        # Generate summary
        summary = ' '.join(key_sentences[:3])
        
        # Extract potential key points (sentences with keywords)
        key_points = self._extract_key_points(sentences)
        
        # Extract action items (sentences with action words)
        action_items = self._extract_action_items(sentences)
        
        return {
            'summary': summary,
            'key_points': key_points[:5],
            'action_items': action_items[:4]
        }
    
    def _split_sentences(self, text: str) -> List[str]:
        """Split text into sentences"""
        # Simple sentence splitting
        sentences = re.split(r'[.!?]+', text)
        return [s.strip() for s in sentences if s.strip()]
    
    def _extract_key_sentences(self, sentences: List[str], num_sentences: int) -> List[str]:
        """Extract key sentences based on length, position, and keywords"""
        scored_sentences = []
        
        for i, sentence in enumerate(sentences):
            score = 0
            
            # Position scoring (beginning and end are important)
            if i < len(sentences) * 0.2:  # First 20%
                score += 2
            if i > len(sentences) * 0.8:  # Last 20%
                score += 1
            
            # Length scoring (not too short, not too long)
            word_count = len(sentence.split())
            if 10 <= word_count <= 30:
                score += 2
            elif 5 <= word_count <= 10:
                score += 1
            
            # Keyword scoring
            important_words = [
                'important', 'significant', 'key', 'main', 'primary', 
                'essential', 'critical', 'major', 'conclude', 'result',
                'therefore', 'however', 'furthermore', 'moreover'
            ]
            
            for word in important_words:
                if word in sentence.lower():
                    score += 1
            
            scored_sentences.append((sentence, score))
        
        # Sort by score and return top sentences
        scored_sentences.sort(key=lambda x: x[1], reverse=True)
        return [sent for sent, score in scored_sentences[:num_sentences]]
    
    def _extract_key_points(self, sentences: List[str]) -> List[str]:
        """Extract sentences that might be key points"""
        key_points = []
        keywords = [
            'benefit', 'advantage', 'feature', 'include', 'consist',
            'contain', 'provide', 'offer', 'enable', 'allow'
        ]
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(keyword in sentence_lower for keyword in keywords):
                if len(sentence.split()) >= 5:  # Not too short
                    key_points.append(sentence.strip())
        
        return key_points
    
    def _extract_action_items(self, sentences: List[str]) -> List[str]:
        """Extract sentences that might be action items"""
        action_items = []
        action_words = [
            'should', 'must', 'need', 'require', 'recommend', 'suggest',
            'plan', 'schedule', 'implement', 'create', 'develop', 'build',
            'contact', 'call', 'email', 'send', 'follow up', 'review'
        ]
        
        for sentence in sentences:
            sentence_lower = sentence.lower()
            if any(word in sentence_lower for word in action_words):
                if len(sentence.split()) >= 4:  # Not too short
                    action_items.append(sentence.strip())
        
        return action_items


class TextSummarizer:
    """Main text summarizer class that manages different AI providers"""
    
    def __init__(self, model_type: str = 'openai', config=None, verbose: bool = False):
        self.model_type = model_type
        self.config = config
        self.verbose = verbose
        self.summarizer = self._initialize_summarizer()
    
    def _initialize_summarizer(self) -> BaseSummarizer:
        """Initialize the appropriate summarizer based on model type"""
        
        if self.model_type == 'openai':
            api_key = self.config.get_openai_api_key() if self.config else None
            if not api_key:
                raise Exception("OpenAI API key not configured. Set OPENAI_API_KEY environment variable.")
            return OpenAISummarizer(api_key)
        
        elif self.model_type == 'anthropic':
            api_key = self.config.get_anthropic_api_key() if self.config else None
            if not api_key:
                raise Exception("Anthropic API key not configured. Set ANTHROPIC_API_KEY environment variable.")
            return AnthropicSummarizer(api_key)
        
        elif self.model_type == 'local':
            return LocalSummarizer()
        
        else:
            raise ValueError(f"Unsupported model type: {self.model_type}")
    
    def summarize(self, text: str, max_length: int = 150) -> Dict[str, Any]:
        """Generate summary using the configured model"""
        
        if self.verbose:
            print(f"Using {self.model_type} model for summarization...")
            print(f"Input text length: {len(text)} characters")
        
        # Pre-process text
        text = text.strip()
        if len(text) < 50:
            raise ValueError("Text is too short to summarize (minimum 50 characters)")
        
        # Generate summary
        result = self.summarizer.summarize(text, max_length)
        
        if self.verbose:
            print("Summary generated successfully")
        
        return result


# =============================================================================
# EXTENDED ANALYSIS CAPABILITIES
# =============================================================================

class BaseAnalyzer(ABC):
    """Abstract base class for text analysis beyond summarization"""
    
    @abstractmethod
    def analyze(self, text: str) -> Dict[str, Any]:
        """Perform analysis on the text"""
        pass


class BiasAnalyzer:
    """Analyzes political and ideological bias in text"""
    
    def __init__(self, summarizer_instance: BaseSummarizer):
        self.summarizer = summarizer_instance
    
    def analyze_bias(self, text: str) -> Dict[str, Any]:
        """Analyze bias using the configured AI model"""
        
        bias_prompt = f"""
Analyze the following article for political and ideological bias. Provide:

1. Overall bias score (-10 to +10, where -10 is extremely left-leaning, 0 is neutral, +10 is extremely right-leaning)
2. Confidence level (0-100%)
3. Specific indicators of bias found
4. Emotional language detection
5. Source credibility assessment

Format as JSON:
{{
    "bias_score": 0,
    "confidence": 85,
    "bias_direction": "neutral|left-leaning|right-leaning",
    "bias_indicators": ["indicator1", "indicator2"],
    "emotional_language": ["examples of emotional language"],
    "objectivity_score": 75,
    "recommendations": "How to interpret this article"
}}

Article text:
{text[:3000]}"""  # Limit text to avoid token limits
        
        if hasattr(self.summarizer, 'client'):  # OpenAI or Anthropic
            try:
                if hasattr(self.summarizer, 'model'):  # OpenAI
                    response = self.summarizer.client.chat.completions.create(
                        model=self.summarizer.model,
                        messages=[{"role": "user", "content": bias_prompt}],
                        temperature=0.3
                    )
                    return self._parse_bias_response(response.choices[0].message.content)
                else:  # Anthropic
                    response = self.summarizer.client.messages.create(
                        model=self.summarizer.model,
                        messages=[{"role": "user", "content": bias_prompt}],
                        max_tokens=1000,
                        temperature=0.3
                    )
                    return self._parse_bias_response(response.content[0].text)
            except Exception as e:
                return {"error": f"AI analysis failed: {str(e)}"}
        else:  # Local analyzer
            return self._local_bias_analysis(text)
    
    def _parse_bias_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for bias analysis"""
        try:
            # Try JSON parsing first
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except:
            pass
        
        # Fallback: manual parsing
        return {
            "bias_score": 0,
            "confidence": 50,
            "bias_direction": "neutral",
            "bias_indicators": ["Analysis format error"],
            "emotional_language": [],
            "objectivity_score": 50,
            "recommendations": "Could not analyze - please try again"
        }
    
    def _local_bias_analysis(self, text: str) -> Dict[str, Any]:
        """Simple local bias analysis using keyword detection"""
        
        left_indicators = ['progressive', 'social justice', 'inequality', 'climate change', 
                          'universal healthcare', 'wealth redistribution']
        right_indicators = ['conservative', 'traditional values', 'free market', 'fiscal responsibility',
                           'strong defense', 'law and order']
        emotional_words = ['outrageous', 'shocking', 'devastating', 'brilliant', 'terrible', 'amazing']
        
        text_lower = text.lower()
        
        left_count = sum(1 for word in left_indicators if word in text_lower)
        right_count = sum(1 for word in right_indicators if word in text_lower)
        emotional_count = sum(1 for word in emotional_words if word in text_lower)
        
        # Simple scoring
        bias_score = right_count - left_count
        bias_direction = "neutral"
        if bias_score > 2:
            bias_direction = "right-leaning"
        elif bias_score < -2:
            bias_direction = "left-leaning"
        
        return {
            "bias_score": max(-10, min(10, bias_score)),
            "confidence": 60,
            "bias_direction": bias_direction,
            "bias_indicators": [f"Left indicators: {left_count}, Right indicators: {right_count}"],
            "emotional_language": [f"Emotional words found: {emotional_count}"],
            "objectivity_score": max(0, 100 - emotional_count * 10),
            "recommendations": "Local analysis - limited accuracy. Use AI models for better results."
        }


class ArticleComparator:
    """Compares multiple articles on the same topic"""
    
    def __init__(self, summarizer_instance: BaseSummarizer):
        self.summarizer = summarizer_instance
    
    def compare_articles(self, articles: List[Dict[str, str]]) -> Dict[str, Any]:
        """Compare multiple articles and find similarities/differences"""
        
        if len(articles) < 2:
            return {"error": "Need at least 2 articles for comparison"}
        
        # Prepare comparison prompt
        articles_text = ""
        for i, article in enumerate(articles, 1):
            title = article.get('title', f'Article {i}')
            content = article.get('content', '')[:1500]  # Limit length
            articles_text += f"\n\n=== ARTICLE {i}: {title} ===\n{content}"
        
        comparison_prompt = f"""
Compare these {len(articles)} articles and analyze:

1. Main topic/theme consensus
2. Key similarities across articles  
3. Major differences in perspective
4. Factual agreements and disagreements
5. Overall credibility comparison
6. Bias differences between sources

Format as JSON:
{{
    "main_topic": "Common theme",
    "similarities": ["similarity1", "similarity2"],
    "differences": ["difference1", "difference2"], 
    "factual_agreements": ["fact1", "fact2"],
    "factual_disagreements": ["disagreement1", "disagreement2"],
    "credibility_ranking": [1, 2, 3],
    "bias_comparison": "Comparative bias analysis",
    "recommendation": "How to interpret these sources together"
}}

Articles to compare:{articles_text}"""
        
        if hasattr(self.summarizer, 'client'):  # AI-powered comparison
            try:
                if hasattr(self.summarizer, 'model'):  # OpenAI
                    response = self.summarizer.client.chat.completions.create(
                        model=self.summarizer.model,
                        messages=[{"role": "user", "content": comparison_prompt}],
                        temperature=0.3
                    )
                    return self._parse_comparison_response(response.choices[0].message.content)
                else:  # Anthropic
                    response = self.summarizer.client.messages.create(
                        model=self.summarizer.model,
                        messages=[{"role": "user", "content": comparison_prompt}],
                        max_tokens=1500,
                        temperature=0.3
                    )
                    return self._parse_comparison_response(response.content[0].text)
            except Exception as e:
                return {"error": f"AI comparison failed: {str(e)}"}
        else:  # Local comparison
            return self._local_comparison(articles)
    
    def _parse_comparison_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for article comparison"""
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except:
            pass
        
        return {
            "main_topic": "Analysis error",
            "similarities": ["Could not analyze"],
            "differences": ["Format error"],
            "factual_agreements": [],
            "factual_disagreements": [],
            "credibility_ranking": list(range(1, len(response) + 1)),
            "bias_comparison": "Analysis failed",
            "recommendation": "Please try again"
        }
    
    def _local_comparison(self, articles: List[Dict[str, str]]) -> Dict[str, Any]:
        """Simple local comparison using keyword overlap"""
        
        # Basic keyword extraction for comparison
        all_words = []
        for article in articles:
            content = article.get('content', '').lower()
            words = re.findall(r'\b\w+\b', content)
            all_words.extend(words)
        
        # Find common words (crude similarity measure)
        word_freq = {}
        for word in all_words:
            if len(word) > 4:  # Filter short words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        common_topics = [word for word, count in word_freq.items() if count >= len(articles)]
        
        return {
            "main_topic": f"Articles about: {', '.join(common_topics[:3])}",
            "similarities": [f"Common keywords: {len(common_topics)}"],
            "differences": ["Local analysis cannot detect nuanced differences"],
            "factual_agreements": ["Cannot determine without AI analysis"],
            "factual_disagreements": ["Cannot determine without AI analysis"],
            "credibility_ranking": list(range(1, len(articles) + 1)),
            "bias_comparison": "Use AI models for bias comparison",
            "recommendation": "Local comparison is limited. Use AI models for detailed analysis."
        }


class SynthesisGenerator:
    """Generates neutral synthesis from multiple sources"""
    
    def __init__(self, summarizer_instance: BaseSummarizer):
        self.summarizer = summarizer_instance
    
    def generate_synthesis(self, articles: List[Dict[str, str]]) -> Dict[str, Any]:
        """Create a neutral synthesis from multiple articles"""
        
        if len(articles) < 2:
            return {"error": "Need at least 2 articles for synthesis"}
        
        # Prepare synthesis prompt
        articles_text = ""
        for i, article in enumerate(articles, 1):
            title = article.get('title', f'Article {i}')
            content = article.get('content', '')[:1200]  # Limit length
            articles_text += f"\n\n=== SOURCE {i}: {title} ===\n{content}"
        
        synthesis_prompt = f"""
Create a neutral, balanced synthesis from these {len(articles)} sources. Your goal is to:

1. Present the most factual information from all sources
2. Acknowledge different perspectives fairly
3. Identify areas of consensus vs disagreement
4. Maintain journalistic neutrality
5. Cite which sources support each point

Format as JSON:
{{
    "title": "Synthesis title",
    "neutral_summary": "Balanced overview incorporating all sources",
    "key_facts": ["Fact 1 (Sources: 1,2)", "Fact 2 (Sources: 2,3)"],
    "different_perspectives": ["Perspective A (Source 1)", "Perspective B (Source 2)"],
    "areas_of_consensus": ["Agreement 1", "Agreement 2"],
    "areas_of_disagreement": ["Disagreement 1", "Disagreement 2"],
    "confidence_assessment": "How reliable is this synthesis",
    "limitations": "What gaps remain"
}}

Sources to synthesize:{articles_text}"""
        
        if hasattr(self.summarizer, 'client'):  # AI-powered synthesis
            try:
                if hasattr(self.summarizer, 'model'):  # OpenAI
                    response = self.summarizer.client.chat.completions.create(
                        model=self.summarizer.model,
                        messages=[{"role": "user", "content": synthesis_prompt}],
                        temperature=0.2  # Lower temperature for more factual output
                    )
                    return self._parse_synthesis_response(response.choices[0].message.content)
                else:  # Anthropic
                    response = self.summarizer.client.messages.create(
                        model=self.summarizer.model,
                        messages=[{"role": "user", "content": synthesis_prompt}],
                        max_tokens=2000,
                        temperature=0.2
                    )
                    return self._parse_synthesis_response(response.content[0].text)
            except Exception as e:
                return {"error": f"AI synthesis failed: {str(e)}"}
        else:  # Local synthesis
            return self._local_synthesis(articles)
    
    def _parse_synthesis_response(self, response: str) -> Dict[str, Any]:
        """Parse AI response for synthesis"""
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = response[json_start:json_end]
                return json.loads(json_str)
        except:
            pass
        
        return {
            "title": "Synthesis Error",
            "neutral_summary": "Could not generate synthesis - please try again",
            "key_facts": ["Analysis failed"],
            "different_perspectives": [],
            "areas_of_consensus": [],
            "areas_of_disagreement": [],
            "confidence_assessment": "Low - technical error",
            "limitations": "Could not complete analysis"
        }
    
    def _local_synthesis(self, articles: List[Dict[str, str]]) -> Dict[str, Any]:
        """Simple local synthesis using text combination"""
        
        combined_content = ""
        titles = []
        
        for i, article in enumerate(articles, 1):
            title = article.get('title', f'Source {i}')
            titles.append(title)
            content = article.get('content', '')[:300]
            combined_content += f" {content}"
        
        # Very basic synthesis
        return {
            "title": f"Combined Report from {len(articles)} sources",
            "neutral_summary": f"This is a combination of {len(articles)} articles: {', '.join(titles)}. " + 
                             combined_content[:500] + "...",
            "key_facts": [f"Information compiled from {len(articles)} sources"],
            "different_perspectives": [f"See original sources: {', '.join(titles)}"],
            "areas_of_consensus": ["Cannot determine without AI analysis"],
            "areas_of_disagreement": ["Cannot determine without AI analysis"],
            "confidence_assessment": "Low - basic text combination only",
            "limitations": "Local synthesis is very limited. Use AI models for quality synthesis."
        }


class AnalysisEngine:
    """Main engine coordinating different analysis modes"""
    
    def __init__(self, model_type: str = 'openai', config=None, verbose: bool = False):
        # Initialize base summarizer
        self.text_summarizer = TextSummarizer(model_type, config, verbose)
        self.base_summarizer = self.text_summarizer.summarizer
        
        # Initialize analysis components
        self.bias_analyzer = BiasAnalyzer(self.base_summarizer)
        self.comparator = ArticleComparator(self.base_summarizer)
        self.synthesizer = SynthesisGenerator(self.base_summarizer)
        
        self.verbose = verbose
    
    def analyze_single_article(self, text: str, mode: str = 'summary') -> Dict[str, Any]:
        """Analyze a single article in various modes"""
        
        if mode == 'summary':
            return self.text_summarizer.summarize(text)
        elif mode == 'bias':
            return self.bias_analyzer.analyze_bias(text)
        elif mode == 'full':
            summary = self.text_summarizer.summarize(text)
            bias = self.bias_analyzer.analyze_bias(text)
            return {
                'summary': summary,
                'bias_analysis': bias,
                'analysis_type': 'comprehensive'
            }
        else:
            raise ValueError(f"Unknown analysis mode: {mode}")
    
    def analyze_multiple_articles(self, articles: List[Dict[str, str]], mode: str = 'compare') -> Dict[str, Any]:
        """Analyze multiple articles"""
        
        if mode == 'compare':
            return self.comparator.compare_articles(articles)
        elif mode == 'synthesis':
            return self.synthesizer.generate_synthesis(articles)
        elif mode == 'full':
            comparison = self.comparator.compare_articles(articles)
            synthesis = self.synthesizer.generate_synthesis(articles)
            return {
                'comparison': comparison,
                'synthesis': synthesis,
                'analysis_type': 'comprehensive_multi'
            }
        else:
            raise ValueError(f"Unknown multi-article mode: {mode}")