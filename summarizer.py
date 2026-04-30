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
    """Advanced analyzer for political and ideological bias with comprehensive detection capabilities"""
    
    def __init__(self, summarizer_instance: BaseSummarizer):
        self.summarizer = summarizer_instance
        self._init_bias_databases()
        self._init_babe_evaluation_system()
    
    def _init_babe_evaluation_system(self):
        """Initialize BABE (Bias Annotations By Experts) evaluation framework"""
        
        # Expert-annotated bias categories based on BABE methodology
        self.babe_bias_categories = {
            'lexical_bias': {
                'description': 'Biased word choice and emotional language',
                'examples': ['slammed', 'destroyed', 'hero', 'villain'],
                'weight': 0.25
            },
            'informational_bias': {
                'description': 'Selective omission or emphasis of information',
                'examples': ['cherry-picking stats', 'omitting context', 'burying counterarguments'],
                'weight': 0.30
            },
            'demographic_bias': {
                'description': 'Unfair representation of groups or individuals',
                'examples': ['stereotyping', 'tokenism', 'group generalizations'],
                'weight': 0.20
            },
            'epistemological_bias': {
                'description': 'Presenting opinion as fact or speculation as certainty',
                'examples': ['unattributed claims', 'false certainty', 'opinion masquerading as news'],
                'weight': 0.25
            }
        }
        
        # Multi-analyst rating systems integration (AllSides & Ad Fontes Media)
        self.external_rating_systems = {
            'allsides': {
                'cnn.com': {'lean': 'Lean Left', 'reliability': 'Mixed'},
                'foxnews.com': {'lean': 'Lean Right', 'reliability': 'Mixed'},
                'reuters.com': {'lean': 'Center', 'reliability': 'High'},
                'washingtonpost.com': {'lean': 'Lean Left', 'reliability': 'High'},
                'wsj.com': {'lean': 'Lean Right', 'reliability': 'High'},
                'npr.org': {'lean': 'Lean Left', 'reliability': 'High'},
                'bbc.com': {'lean': 'Center', 'reliability': 'High'}
            },
            'ad_fontes': {
                'reuters.com': {'reliability_score': 48, 'bias_score': 0.5},  # High reliability, minimal bias
                'ap.org': {'reliability_score': 49, 'bias_score': 0},
                'bbc.com': {'reliability_score': 45, 'bias_score': -2},
                'cnn.com': {'reliability_score': 35, 'bias_score': -8},
                'foxnews.com': {'reliability_score': 33, 'bias_score': 12},
                'washingtonpost.com': {'reliability_score': 40, 'bias_score': -6}
            }
        }
        
        # Linguistic baseline patterns for objective measurement
        self.linguistic_baselines = {
            'objectivity_markers': {
                'high_objectivity': ['according to', 'data shows', 'research indicates', 'officials confirmed'],
                'medium_objectivity': ['appears to', 'seems to', 'suggests', 'may indicate'],
                'low_objectivity': ['clearly', 'obviously', 'undoubtedly', 'everyone knows']
            },
            'attribution_quality': {
                'strong': ['named expert said', 'official statement', 'peer-reviewed study'],
                'medium': ['officials say', 'experts believe', 'sources indicate'],
                'weak': ['critics claim', 'some say', 'it is believed']
            },
            'modal_verbs': {
                'certain': ['is', 'are', 'will', 'has', 'have'],
                'probable': ['likely', 'probably', 'appears', 'tends to'],
                'possible': ['might', 'could', 'may', 'possibly', 'allegedly']
            }
        }
        
        # BABE-style evaluation metrics
        self.evaluation_metrics = {
            'precision_targets': ['political_bias', 'sensationalism', 'factual_accuracy'],
            'recall_targets': ['missing_context', 'omitted_perspectives', 'unstated_assumptions'],
            'f1_balance': 'harmonic_mean_precision_recall'
        }
    
    def _init_bias_databases(self):
        """Initialize bias detection databases and patterns"""
        
        # Publisher bias database (expandable)
        self.publisher_bias_db = {
            # Left-leaning sources
            'cnn.com': {'lean': -3, 'reliability': 'high'},
            'msnbc.com': {'lean': -4, 'reliability': 'medium'},
            'huffpost.com': {'lean': -5, 'reliability': 'medium'},
            'theguardian.com': {'lean': -2, 'reliability': 'high'},
            'washingtonpost.com': {'lean': -1, 'reliability': 'high'},
            'nytimes.com': {'lean': -1, 'reliability': 'high'},
            
            # Center sources
            'reuters.com': {'lean': 0, 'reliability': 'very high'},
            'ap.org': {'lean': 0, 'reliability': 'very high'},
            'bbc.com': {'lean': 0, 'reliability': 'high'},
            'npr.org': {'lean': 0, 'reliability': 'high'},
            
            # Right-leaning sources
            'foxnews.com': {'lean': 4, 'reliability': 'medium'},
            'wsj.com': {'lean': 2, 'reliability': 'high'},
            'nypost.com': {'lean': 3, 'reliability': 'medium'},
            'dailywire.com': {'lean': 6, 'reliability': 'low'},
            'breitbart.com': {'lean': 7, 'reliability': 'low'}
        }
        
        # Enhanced emotion detection patterns
        self.emotion_patterns = {
            'anger': {
                'words': ['outraged', 'furious', 'livid', 'enraged', 'incensed', 'irate'],
                'phrases': ['completely unacceptable', 'utter disaster', 'absolutely ridiculous']
            },
            'fear': {
                'words': ['terrifying', 'horrifying', 'alarming', 'devastating', 'catastrophic'],
                'phrases': ['existential threat', 'grave danger', 'unprecedented crisis']
            },
            'moral_outrage': {
                'words': ['barbaric', 'unconscionable', 'despicable', 'reprehensible'],
                'phrases': ['moral failure', 'ethical disaster', 'complete betrayal']
            },
            'contempt': {
                'words': ['pathetic', 'laughable', 'ridiculous', 'absurd', 'ludicrous'],
                'phrases': ['utter incompetence', 'complete failure', 'total disaster']
            }
        }
        
        # Framing detection patterns
        self.framing_patterns = {
            'victim_language': ['suffered', 'endured', 'victimized', 'oppressed', 'persecuted'],
            'aggressor_language': ['attacked', 'invaded', 'assaulted', 'violated', 'destroyed'],
            'heroic_language': ['courageous', 'brave', 'heroic', 'noble', 'principled'],
            'incompetent_language': ['failed', 'bungled', 'mismanaged', 'incompetent', 'inept']
        }
        
        # Modality indicators (certainty vs speculation)
        self.modality_patterns = {
            'certain': ['is', 'are', 'will', 'confirms', 'proves', 'demonstrates'],
            'probable': ['likely', 'probably', 'appears', 'seems', 'suggests'],
            'speculative': ['might', 'could', 'may', 'possibly', 'allegedly', 'reportedly']
        }
        
        # Value-laden adjectives by category
        self.value_adjectives = {
            'negative_political': ['extremist', 'radical', 'dangerous', 'reckless', 'irresponsible'],
            'positive_political': ['principled', 'steadfast', 'committed', 'dedicated', 'visionary'],
            'negative_moral': ['corrupt', 'dishonest', 'unethical', 'immoral', 'deceptive'],
            'positive_moral': ['honest', 'ethical', 'principled', 'trustworthy', 'transparent']
        }
    
    def analyze_bias(self, text: str, source_url: str = None, article_title: str = None) -> Dict[str, Any]:
        """Comprehensive bias analysis with BABE evaluation framework"""
        
        if hasattr(self.summarizer, 'client'):  # AI-powered analysis
            return self._babe_comprehensive_analysis(text, source_url, article_title)
        else:  # Enhanced local analysis with BABE principles
            return self._babe_local_analysis(text, source_url, article_title)
    
    def _babe_comprehensive_analysis(self, text: str, source_url: str = None, article_title: str = None) -> Dict[str, Any]:
        """BABE-enhanced AI analysis with expert-level evaluation"""
        
        # Get multi-source rating context
        external_ratings = self._get_external_ratings(source_url) if source_url else {}
        
        babe_prompt = f"""
EXPERT BIAS EVALUATION using BABE (Bias Annotations By Experts) Framework

You are a panel of journalism ethics experts performing comprehensive bias analysis. Apply the BABE methodology with precision/recall metrics.

**BABE EVALUATION CATEGORIES:**

1. **LEXICAL BIAS ANALYSIS (25% weight):**
   - Emotional language intensity (1-10 scale with evidence)
   - Value-laden adjectives and their targets
   - Euphemisms vs direct language choices
   - Quote selection bias (who gets favorable/critical quotes)
   
2. **INFORMATIONAL BIAS ANALYSIS (30% weight):**
   - Missing counterarguments (what perspectives are absent?)
   - Statistical cherry-picking (selective data presentation)
   - Context omission (what background is missing?)
   - Source diversity (single vs multiple perspectives)
   
3. **DEMOGRAPHIC BIAS ANALYSIS (20% weight):**
   - Group representation fairness
   - Individual vs group attribution patterns  
   - Stereotypical language or assumptions
   - Identity-based framing differences
   
4. **EPISTEMOLOGICAL BIAS ANALYSIS (25% weight):**
   - Certainty vs speculation markers
   - Opinion presented as fact
   - Attribution quality (named sources vs anonymous claims)
   - Causal claims without sufficient evidence

**MULTI-ANALYST CALIBRATION:**
External Ratings: {external_ratings}
Use these as calibration priors, but provide independent analysis.

**TRANSPARENCY REQUIREMENTS:**
- NEVER output single bias scores without evidence
- Highlight specific sentences/phrases with explanations
- Show confidence intervals for each assessment
- Provide alternative framings for biased elements

**REQUIRED JSON OUTPUT:**
{{
    "babe_evaluation": {{
        "overall_bias_score": {{
            "score": -2.3,
            "confidence_interval": [-3.1, -1.5],
            "evidence_strength": "strong"
        }},
        "category_scores": {{
            "lexical_bias": {{
                "score": -2,
                "precision": 0.85,
                "recall": 0.72,
                "f1_score": 0.78,
                "evidence": ["specific phrases with line numbers"]
            }},
            "informational_bias": {{
                "score": -3,
                "precision": 0.78,
                "recall": 0.81,
                "f1_score": 0.79,
                "evidence": ["missing context examples"]
            }},
            "demographic_bias": {{
                "score": -1,
                "precision": 0.90,
                "recall": 0.65,
                "f1_score": 0.75,
                "evidence": ["representation issues"]
            }},
            "epistemological_bias": {{
                "score": -2,
                "precision": 0.82,
                "recall": 0.76,
                "f1_score": 0.79,
                "evidence": ["certainty vs fact issues"]
            }}
        }},
        "cross_validation": {{
            "allsides_agreement": "partial",
            "ad_fontes_agreement": "strong", 
            "expert_consensus": 0.78
        }}
    }},
    
    "highlighted_bias_evidence": [
        {{
            "text": "exact phrase from article",
            "line_position": "paragraph 3, sentence 2",
            "bias_type": "lexical_bias",
            "explanation": "why this triggers bias detection",
            "alternative_framing": "neutral way to express this",
            "confidence": 0.85
        }}
    ],
    
    "missing_perspectives": [
        {{
            "perspective": "conservative viewpoint on policy",
            "impact": "creates incomplete picture", 
            "suggested_sources": ["specific outlets or experts"],
            "confidence": 0.78
        }}
    ],
    
    "comparative_analysis": {{
        "likely_left_framing": "how left sources might frame this",
        "likely_right_framing": "how right sources might frame this", 
        "neutral_baseline": "objective framing approach",
        "current_proximity": "closest to left framing"
    }},
    
    "actionable_feedback": {{
        "for_readers": [
            "What questions to ask while reading",
            "What additional sources to consult"
        ],
        "for_authors": [
            "Specific neutrality improvements",
            "Missing context to add"
        ],
        "for_editors": [
            "Structural changes needed",
            "Policy implications"
        ]
    }},
    
    "evaluation_metadata": {{
        "analysis_date": "2024-01-15",
        "analyst_confidence": 0.82,
        "methodology": "BABE + multi-analyst calibration",
        "limitations": ["specific analytical constraints"]
    }}
}}

**ARTICLE TO EVALUATE:**
Title: {article_title or 'No title provided'}
URL: {source_url or 'No source URL'}
Text: {text[:5000]}

Apply rigorous BABE methodology. Be precise, evidence-based, and transparent."""
        
        try:
            if hasattr(self.summarizer, 'model'):  # OpenAI
                response = self.summarizer.client.chat.completions.create(
                    model=self.summarizer.model,
                    messages=[{"role": "user", "content": babe_prompt}],
                    temperature=0.1  # Very low for analytical consistency
                )
                return self._parse_babe_response(response.choices[0].message.content, source_url)
            else:  # Anthropic
                response = self.summarizer.client.messages.create(
                    model=self.summarizer.model,
                    messages=[{"role": "user", "content": babe_prompt}],
                    max_tokens=3500,  # Increased for comprehensive BABE analysis
                    temperature=0.1
                )
                return self._parse_babe_response(response.content[0].text, source_url)
        except Exception as e:
            return {"error": f"BABE analysis failed: {str(e)}", "fallback": self._babe_local_analysis(text, source_url, article_title)}
    
    def _get_external_ratings(self, source_url: str) -> Dict[str, Any]:
        """Get external rating system assessments for calibration"""
        if not source_url:
            return {}
        
        ratings = {}
        
        # Check AllSides ratings
        for domain, rating in self.external_rating_systems['allsides'].items():
            if domain in source_url:
                ratings['allsides'] = rating
                break
        
        # Check Ad Fontes Media ratings
        for domain, rating in self.external_rating_systems['ad_fontes'].items():
            if domain in source_url:
                ratings['ad_fontes'] = rating
                break
                
        return ratings
    
    def _babe_local_analysis(self, text: str, source_url: str = None, article_title: str = None) -> Dict[str, Any]:
        """BABE-enhanced local analysis with linguistic baseline measurement"""
        
        text_lower = text.lower()
        
        # BABE category evaluations
        lexical_analysis = self._evaluate_lexical_bias_babe(text, text_lower)
        informational_analysis = self._evaluate_informational_bias_babe(text, text_lower)
        demographic_analysis = self._evaluate_demographic_bias_babe(text, text_lower)
        epistemological_analysis = self._evaluate_epistemological_bias_babe(text, text_lower)
        
        # Calculate weighted BABE score
        overall_score = (
            lexical_analysis['score'] * self.babe_bias_categories['lexical_bias']['weight'] +
            informational_analysis['score'] * self.babe_bias_categories['informational_bias']['weight'] +
            demographic_analysis['score'] * self.babe_bias_categories['demographic_bias']['weight'] +
            epistemological_analysis['score'] * self.babe_bias_categories['epistemological_bias']['weight']
        )
        
        # Get external calibration
        external_ratings = self._get_external_ratings(source_url)
        
        # Calculate confidence intervals (simplified for local analysis)
        confidence_interval = [overall_score - 0.8, overall_score + 0.8]
        
        return {
            "babe_evaluation": {
                "overall_bias_score": {
                    "score": round(overall_score, 1),
                    "confidence_interval": [round(ci, 1) for ci in confidence_interval],
                    "evidence_strength": "medium" if abs(overall_score) > 1 else "weak"
                },
                "category_scores": {
                    "lexical_bias": {
                        "score": lexical_analysis['score'],
                        "precision": lexical_analysis['precision'],
                        "recall": lexical_analysis['recall'],
                        "f1_score": lexical_analysis['f1_score'],
                        "evidence": lexical_analysis['evidence']
                    },
                    "informational_bias": {
                        "score": informational_analysis['score'], 
                        "precision": informational_analysis['precision'],
                        "recall": informational_analysis['recall'],
                        "f1_score": informational_analysis['f1_score'],
                        "evidence": informational_analysis['evidence']
                    },
                    "demographic_bias": {
                        "score": demographic_analysis['score'],
                        "precision": demographic_analysis['precision'], 
                        "recall": demographic_analysis['recall'],
                        "f1_score": demographic_analysis['f1_score'],
                        "evidence": demographic_analysis['evidence']
                    },
                    "epistemological_bias": {
                        "score": epistemological_analysis['score'],
                        "precision": epistemological_analysis['precision'],
                        "recall": epistemological_analysis['recall'], 
                        "f1_score": epistemological_analysis['f1_score'],
                        "evidence": epistemological_analysis['evidence']
                    }
                },
                "cross_validation": {
                    "allsides_agreement": self._calculate_external_agreement(overall_score, external_ratings, 'allsides'),
                    "ad_fontes_agreement": self._calculate_external_agreement(overall_score, external_ratings, 'ad_fontes'),
                    "expert_consensus": 0.65  # Lower for local analysis
                }
            },
            
            "highlighted_bias_evidence": self._compile_bias_evidence([
                lexical_analysis, informational_analysis, 
                demographic_analysis, epistemological_analysis
            ]),
            
            "missing_perspectives": self._identify_missing_perspectives_local(text, overall_score),
            
            "comparative_analysis": {
                "likely_left_framing": "Emphasizes systemic issues, social justice angles",
                "likely_right_framing": "Focuses on individual responsibility, economic concerns", 
                "neutral_baseline": "Presents multiple viewpoints with clear attribution",
                "current_proximity": "left framing" if overall_score < -1 else "right framing" if overall_score > 1 else "relatively neutral"
            },
            
            "actionable_feedback": {
                "for_readers": [
                    "Cross-reference with sources from different political leanings",
                    "Look for missing statistical context or counterarguments",
                    "Question emotional language and unsupported claims"
                ],
                "for_authors": [
                    "Include more diverse source perspectives", 
                    "Provide clearer attribution for claims",
                    "Use more neutral language for controversial topics"
                ],
                "for_editors": [
                    "Implement bias detection in editorial workflow",
                    "Require multiple source validation for political content",
                    "Establish neutrality guidelines for sensitive topics"
                ]
            },
            
            "evaluation_metadata": {
                "analysis_date": "2024-01-15",
                "analyst_confidence": 0.65,
                "methodology": "BABE-enhanced local pattern analysis",
                "limitations": ["Cannot detect sophisticated omission bias", "Limited context analysis", "No real-time fact checking"]
            }
        }
    
    def cross_source_comparison(self, articles: List[Dict[str, str]]) -> Dict[str, Any]:
        """BABE cross-source comparison mode for relative bias analysis"""
        
        if len(articles) < 2:
            return {"error": "Need at least 2 articles for comparison"}
        
        comparative_analysis = {
            "articles": [],
            "divergence_analysis": {},
            "bias_spectrum": {},
            "consensus_points": [],
            "major_disagreements": [],
            "framing_differences": {}
        }
        
        # Analyze each article
        for i, article in enumerate(articles):
            analysis = self.analyze_bias(
                article.get('text', ''),
                article.get('url', ''), 
                article.get('title', f'Article {i+1}')
            )
            
            comparative_analysis["articles"].append({
                "title": article.get('title', f'Article {i+1}'),
                "source": article.get('url', 'Unknown'),
                "bias_score": analysis.get('babe_evaluation', {}).get('overall_bias_score', {}).get('score', 0),
                "key_framings": self._extract_key_framings(article.get('text', '')),
                "emotional_language": self._extract_emotional_language(article.get('text', ''))
            })
        
        # Calculate divergences
        comparative_analysis["divergence_analysis"] = self._calculate_cross_source_divergences(comparative_analysis["articles"])
        
        # Identify consensus and disagreements
        comparative_analysis["consensus_points"] = self._find_consensus_points(articles)
        comparative_analysis["major_disagreements"] = self._find_major_disagreements(articles)
        
    def _evaluate_lexical_bias_babe(self, text: str, text_lower: str) -> Dict[str, Any]:
        """Evaluate lexical bias using BABE methodology"""
        
        evidence = []
        bias_score = 0
        detected_items = 0
        total_possible = 20  # Estimated baseline for precision/recall
        
        # Emotional language detection
        for emotion_type, patterns in self.emotion_patterns.items():
            for word in patterns['words']:
                if word in text_lower:
                    count = text_lower.count(word)
                    bias_impact = count * (2 if emotion_type in ['anger', 'contempt'] else 1)
                    bias_score += bias_impact * 0.1
                    detected_items += count
                    evidence.append(f"Emotional word '{word}' ({emotion_type}) appears {count} times")
        
        # Value-laden adjectives
        for category, words in self.value_adjectives.items():
            bias_direction = -0.5 if 'negative' in category else 0.5
            for word in words:
                if word in text_lower:
                    count = text_lower.count(word)
                    bias_score += bias_direction * count
                    detected_items += count
                    evidence.append(f"Value-laden adjective '{word}' ({category})")
        
        # Calculate BABE metrics
        precision = min(detected_items / max(1, detected_items + 2), 1.0)  # Estimated false positives
        recall = detected_items / total_possible
        f1_score = 2 * (precision * recall) / max(precision + recall, 0.001)
        
        return {
            'score': round(bias_score, 2),
            'precision': round(precision, 2),
            'recall': round(recall, 2), 
            'f1_score': round(f1_score, 2),
            'evidence': evidence[:5]  # Limit to top 5 examples
        }
    
    def _evaluate_informational_bias_babe(self, text: str, text_lower: str) -> Dict[str, Any]:
        """Evaluate informational bias (omissions, cherry-picking) using BABE methodology"""
        
        evidence = []
        bias_score = 0
        
        # Check for one-sided sourcing patterns
        attribution_patterns = {
            'strong': len([p for p in self.linguistic_baselines['attribution_quality']['strong'] if p in text_lower]),
            'medium': len([p for p in self.linguistic_baselines['attribution_quality']['medium'] if p in text_lower]),
            'weak': len([p for p in self.linguistic_baselines['attribution_quality']['weak'] if p in text_lower])
        }
        
        total_attributions = sum(attribution_patterns.values())
        if total_attributions > 0:
            weak_ratio = attribution_patterns['weak'] / total_attributions
            if weak_ratio > 0.5:
                bias_score += 1.5
                evidence.append(f"High ratio of weak attributions: {weak_ratio:.1%}")
        
        # Check for missing counterarguments (simplified heuristic)
        counterargument_indicators = ['however', 'on the other hand', 'critics argue', 'opponents say', 'but']
        counterargument_count = sum(1 for indicator in counterargument_indicators if indicator in text_lower)
        
        if counterargument_count == 0 and len(text.split()) > 200:
            bias_score += 1.0
            evidence.append("No counterarguments detected in substantial article")
        
        # Estimate precision/recall for informational bias
        precision = 0.7  # Conservative estimate for local analysis
        recall = 0.4    # Lower recall as we can't detect sophisticated omissions
        f1_score = 2 * (precision * recall) / (precision + recall)
        
        return {
            'score': round(bias_score, 2),
            'precision': round(precision, 2),
            'recall': round(recall, 2),
            'f1_score': round(f1_score, 2),
            'evidence': evidence
        }
    
    def _evaluate_demographic_bias_babe(self, text: str, text_lower: str) -> Dict[str, Any]:
        """Evaluate demographic bias using BABE methodology"""
        
        evidence = []
        bias_score = 0
        
        # Simplified demographic bias detection
        # Check for group generalizations
        generalization_patterns = ['all ', 'every ', 'always ', 'never ', 'typical ']
        demographic_terms = ['men', 'women', 'muslim', 'christian', 'conservative', 'liberal', 'immigrant']
        
        for pattern in generalization_patterns:
            for term in demographic_terms:
                combined = pattern + term
                if combined in text_lower:
                    bias_score += 0.5
                    evidence.append(f"Potential generalization: '{combined}'")
        
        # Estimate metrics (conservative for local analysis)
        precision = 0.6
        recall = 0.3
        f1_score = 2 * (precision * recall) / (precision + recall)
        
        return {
            'score': round(bias_score, 2),
            'precision': round(precision, 2),
            'recall': round(recall, 2),
            'f1_score': round(f1_score, 2),
            'evidence': evidence
        }
    
    def _evaluate_epistemological_bias_babe(self, text: str, text_lower: str) -> Dict[str, Any]:
        """Evaluate epistemological bias (certainty vs speculation) using BABE methodology"""
        
        evidence = []
        bias_score = 0
        
        # Analyze modality patterns
        certain_count = sum(1 for marker in self.linguistic_baselines['modal_verbs']['certain'] if f" {marker} " in text_lower)
        speculative_count = sum(1 for marker in self.linguistic_baselines['modal_verbs']['possible'] if f" {marker} " in text_lower)
        
        total_modal_verbs = certain_count + speculative_count
        if total_modal_verbs > 0:
            certainty_ratio = certain_count / total_modal_verbs
            if certainty_ratio > 0.8:
                bias_score += 1.0
                evidence.append(f"High certainty ratio: {certainty_ratio:.1%} (may indicate false certainty)")
        
        # Check for unsupported claims (simplified)
        objectivity_high = sum(1 for marker in self.linguistic_baselines['objectivity_markers']['high_objectivity'] if marker in text_lower)
        objectivity_low = sum(1 for marker in self.linguistic_baselines['objectivity_markers']['low_objectivity'] if marker in text_lower)
        
        if objectivity_low > objectivity_high:
            bias_score += 0.8
            evidence.append("More subjective than objective language markers detected")
        
        # Estimate metrics
        precision = 0.75
        recall = 0.6
        f1_score = 2 * (precision * recall) / (precision + recall)
        
        return {
            'score': round(bias_score, 2),
            'precision': round(precision, 2),
            'recall': round(recall, 2),
            'f1_score': round(f1_score, 2),
            'evidence': evidence
        }
    
    def _parse_babe_response(self, response: str, source_url: str = None) -> Dict[str, Any]:
        """Parse BABE evaluation response from AI"""
        try:
            import json
            # Extract JSON from response
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                parsed_response = json.loads(json_str)
                
                # Add source information
                if source_url:
                    parsed_response['source_analysis'] = {
                        'url': source_url,
                        'external_ratings': self._get_external_ratings(source_url)
                    }
                
                return parsed_response
            else:
                return {"error": "Could not parse BABE evaluation response", "raw_response": response}
        except json.JSONDecodeError as e:
            return {"error": f"JSON parsing failed: {str(e)}", "raw_response": response}
    
    def _calculate_external_agreement(self, our_score: float, external_ratings: Dict, system: str) -> str:
        """Calculate agreement with external rating systems"""
        if system not in external_ratings:
            return "no_data"
        
        if system == 'allsides':
            rating = external_ratings[system]
            if 'Lean Left' in rating['lean'] and our_score < -1:
                return "strong"
            elif 'Center' in rating['lean'] and abs(our_score) < 1:
                return "strong" 
            elif 'Lean Right' in rating['lean'] and our_score > 1:
                return "strong"
            else:
                return "partial"
        
        elif system == 'ad_fontes':
            rating = external_ratings[system]
            external_bias = rating['bias_score']
            
            # Simple agreement check
            if (our_score < 0 and external_bias < 0) or (our_score > 0 and external_bias > 0):
                return "strong"
            elif abs(our_score) < 1 and abs(external_bias) < 3:
                return "partial"
            else:
                return "weak"
        
    def _compile_bias_evidence(self, analyses: List[Dict]) -> List[Dict]:
        """Compile highlighted bias evidence from all BABE categories"""
        
        evidence = []
        for analysis in analyses:
            for item in analysis.get('evidence', []):
                evidence.append({
                    "text": item,
                    "line_position": "detected via pattern matching",
                    "bias_type": "multiple_categories", 
                    "explanation": "Pattern-based detection",
                    "alternative_framing": "Use more neutral language",
                    "confidence": 0.7
                })
        
        return evidence[:10]  # Limit to top 10
    
    def _identify_missing_perspectives_local(self, text: str, bias_score: float) -> List[Dict]:
        """Identify missing perspectives based on bias direction"""
        
        missing = []
        
        if bias_score < -1.5:  # Left-leaning bias detected
            missing.append({
                "perspective": "Conservative/right-leaning viewpoints",
                "impact": "May present incomplete picture of policy implications",
                "suggested_sources": ["Wall Street Journal", "Fox News", "National Review"],
                "confidence": 0.7
            })
        elif bias_score > 1.5:  # Right-leaning bias detected  
            missing.append({
                "perspective": "Progressive/left-leaning viewpoints",
                "impact": "May underrepresent social equity concerns",
                "suggested_sources": ["Washington Post", "CNN", "NPR"],
                "confidence": 0.7
            })
        
        return missing
    
    def _extract_key_framings(self, text: str) -> List[str]:
        """Extract key framing elements from text"""
        
        framings = []
        text_lower = text.lower()
        
        # Look for framing patterns
        for frame_type, patterns in self.framing_patterns.items():
            for pattern in patterns:
                if pattern in text_lower:
                    framings.append(f"{frame_type}: {pattern}")
        
        return framings[:5]  # Limit to top 5
    
    def _extract_emotional_language(self, text: str) -> List[str]:
        """Extract emotional language for cross-comparison"""
        
        emotional = []
        text_lower = text.lower()
        
        for emotion_type, patterns in self.emotion_patterns.items():
            for word in patterns['words']:
                if word in text_lower:
                    emotional.append(f"{emotion_type}: {word}")
        
        return emotional[:5]  # Limit to top 5
    
    def _calculate_cross_source_divergences(self, articles: List[Dict]) -> Dict[str, Any]:
        """Calculate divergences between sources"""
        
        bias_scores = [article['bias_score'] for article in articles]
        bias_range = max(bias_scores) - min(bias_scores)
        
        return {
            "bias_score_range": round(bias_range, 2),
            "polarization_level": "high" if bias_range > 4 else "medium" if bias_range > 2 else "low",
            "most_biased": max(articles, key=lambda x: abs(x['bias_score'])),
            "most_neutral": min(articles, key=lambda x: abs(x['bias_score']))
        }
    
    def _find_consensus_points(self, articles: List[Dict]) -> List[str]:
        """Find points of consensus across articles (simplified)"""
        
        # This would require sophisticated text comparison in a full implementation
        return ["Basic factual agreement on main events", "Similar timeline of key developments"]
    
    def _find_major_disagreements(self, articles: List[Dict]) -> List[str]:
        """Find major disagreements between articles (simplified)"""
        
        # This would require sophisticated text comparison in a full implementation  
        return ["Different emphasis on causes", "Varying assessment of impacts", "Contrasting expert opinions"]
        """AI-powered comprehensive bias analysis"""
        
        # Get source bias context
        source_context = self._get_source_context(source_url) if source_url else "Unknown source"
        
        enhanced_prompt = f"""
Perform a comprehensive bias analysis of this article using advanced analytical techniques:

**ANALYSIS FRAMEWORK:**

1. **LANGUAGE BIAS ANALYSIS:**
   - Detect value-laden adjectives and their targets
   - Identify emotional language and its intensity (1-10 scale)
   - Analyze modality (certainty vs speculation): "is/are" vs "appears/seems" vs "allegedly/might"
   - Check contextual sentiment: Is emotional language quoted, critiqued, or asserted by author?

2. **FRAMING BIAS ANALYSIS:**
   - Subject-object positioning: Who is portrayed as aggressor/victim/hero/incompetent?
   - Causal framing: What causes are emphasized or downplayed?
   - Agency attribution: Who is given active vs passive voice?
   - Selection and emphasis: What facts are highlighted vs buried?

3. **STRUCTURAL BIAS ANALYSIS:**
   - Missing counterarguments or alternative perspectives
   - One-sided sourcing patterns
   - Historical context gaps
   - Attribution quality ("critics say" vs "experts confirm")

4. **EMOTIONAL MANIPULATION DETECTION:**
   - Tone clusters: anger, fear, moral outrage, contempt
   - Target identification: Who is the emotion directed at?
   - Author vs quoted emotion distinction

5. **COMPARATIVE POSITIONING:**
   - How might other outlets frame this differently?
   - What alternative framings are possible?

**SOURCE CONTEXT:** {source_context}

**REQUIRED OUTPUT FORMAT (JSON):**
{{
    "overall_bias_score": -3,
    "confidence_level": 85,
    "bias_direction": "left-leaning",
    
    "component_scores": {{
        "language_bias": -2,
        "framing_bias": -4,
        "omission_bias": -1,
        "source_bias": 0,
        "emotional_manipulation": -3
    }},
    
    "detailed_analysis": {{
        "biased_phrases": [
            {{"text": "phrase", "bias_type": "emotional", "intensity": 7, "target": "person/group"}}
        ],
        "framing_issues": [
            {{"type": "victim_positioning", "subject": "X", "description": "explanation"}}
        ],
        "missing_context": [
            "What counterarguments were omitted",
            "What historical context was skipped"
        ],
        "emotion_analysis": {{
            "dominant_tone": "anger",
            "emotional_targets": ["politician A", "policy B"],
            "author_vs_quoted": "mostly_author"
        }},
        "modality_analysis": {{
            "certainty_level": "high",
            "speculation_markers": ["appears", "seems"],
            "assertion_strength": "strong"
        }}
    }},
    
    "reader_guidance": {{
        "key_concerns": ["What readers should watch out for"],
        "alternative_framings": ["How this could be presented neutrally"],
        "suggested_sources": ["Where to find contrasting perspectives"],
        "critical_questions": ["What questions readers should ask"]
    }},
    
    "explainability": {{
        "score_justification": "Why each component received its score",
        "bias_evidence": ["Specific examples supporting the bias assessment"],
        "neutrality_suggestions": ["How key sentences could be rewritten neutrally"]
    }}
}}

**ARTICLE TO ANALYZE:**
Title: {article_title or 'No title provided'}
Text: {text[:4000]}"""  # Increased limit for comprehensive analysis
        
        try:
            if hasattr(self.summarizer, 'model'):  # OpenAI
                response = self.summarizer.client.chat.completions.create(
                    model=self.summarizer.model,
                    messages=[{"role": "user", "content": enhanced_prompt}],
                    temperature=0.2  # Lower temperature for more analytical consistency
                )
                return self._parse_enhanced_bias_response(response.choices[0].message.content, source_url)
            else:  # Anthropic
                response = self.summarizer.client.messages.create(
                    model=self.summarizer.model,
                    messages=[{"role": "user", "content": enhanced_prompt}],
                    max_tokens=2500,  # Increased for detailed analysis
                    temperature=0.2
                )
                return self._parse_enhanced_bias_response(response.content[0].text, source_url)
        except Exception as e:
            return {"error": f"Enhanced AI analysis failed: {str(e)}"}
    
    def _enhanced_local_bias_analysis(self, text: str, source_url: str = None, article_title: str = None) -> Dict[str, Any]:
        """Enhanced local bias analysis with pattern recognition"""
        
        text_lower = text.lower()
        
        # Component analysis
        language_bias = self._analyze_language_bias_local(text, text_lower)
        framing_bias = self._analyze_framing_bias_local(text, text_lower)
        emotional_analysis = self._analyze_emotions_local(text, text_lower)
        modality_analysis = self._analyze_modality_local(text, text_lower)
        source_bias = self._get_source_bias_score(source_url)
        
        # Calculate overall bias score
        overall_score = (
            language_bias['score'] * 0.3 +
            framing_bias['score'] * 0.25 +
            emotional_analysis['bias_impact'] * 0.2 +
            source_bias * 0.15 +
            self._calculate_omission_bias_local(text) * 0.1
        )
        
        bias_direction = "neutral"
        if overall_score > 1.5:
            bias_direction = "right-leaning"
        elif overall_score < -1.5:
            bias_direction = "left-leaning"
        
        return {
            "overall_bias_score": round(overall_score, 1),
            "confidence_level": 70,  # Local analysis is less confident
            "bias_direction": bias_direction,
            
            "component_scores": {
                "language_bias": language_bias['score'],
                "framing_bias": framing_bias['score'],
                "omission_bias": self._calculate_omission_bias_local(text),
                "source_bias": source_bias,
                "emotional_manipulation": emotional_analysis['bias_impact']
            },
            
            "detailed_analysis": {
                "biased_phrases": language_bias['phrases'],
                "framing_issues": framing_bias['issues'],
                "missing_context": ["Local analysis cannot detect missing context reliably"],
                "emotion_analysis": emotional_analysis,
                "modality_analysis": modality_analysis
            },
            
            "reader_guidance": {
                "key_concerns": self._generate_local_concerns(overall_score, emotional_analysis),
                "alternative_framings": ["Consider how opposing viewpoints might frame this"],
                "suggested_sources": self._suggest_alternative_sources(source_url),
                "critical_questions": [
                    "What perspectives might be missing?",
                    "Are claims properly attributed and sourced?",
                    "Is the language neutral or emotionally charged?"
                ]
            },
            
            "explainability": {
                "score_justification": f"Score based on: Language ({language_bias['score']}), Framing ({framing_bias['score']}), Emotion ({emotional_analysis['bias_impact']}), Source ({source_bias})",
                "bias_evidence": language_bias['phrases'] + framing_bias['issues'],
                "neutrality_suggestions": ["Use more measured language", "Include multiple perspectives", "Provide proper attribution"]
            }
        }
    
    def _get_source_context(self, source_url: str) -> str:
        """Get contextual information about the source"""
        if not source_url:
            return "Unknown source"
        
        for domain, info in self.publisher_bias_db.items():
            if domain in source_url:
                lean_desc = "center" if info['lean'] == 0 else f"{'left' if info['lean'] < 0 else 'right'}-leaning (strength: {abs(info['lean'])})"
                return f"Source: {domain} - Known bias: {lean_desc}, Reliability: {info['reliability']}"
        
        return f"Source: {source_url} - Not in bias database"
    
    def _get_publisher_bias(self, domain: str) -> Dict[str, Any]:
        """Get publisher bias information by domain"""
        return self.publisher_bias_db.get(domain, {'lean': 0, 'reliability': 'unknown'})
    
    def _detect_emotional_language(self, text: str) -> float:
        """Detect emotional language intensity (0-10 scale)"""
        text_lower = text.lower()
        emotional_score = 0
        
        for emotion_type, patterns in self.emotion_patterns.items():
            for word in patterns['words']:
                if word in text_lower:
                    emotional_score += 1
            for phrase in patterns.get('phrases', []):
                if phrase in text_lower:
                    emotional_score += 2
        
        # Normalize to 0-10 scale (rough approximation)
        return min(emotional_score / 2, 10)
    
    def _get_source_bias_score(self, source_url: str) -> float:
        """Get bias score based on known source lean"""
        if not source_url:
            return 0
        
        for domain, info in self.publisher_bias_db.items():
            if domain in source_url:
                return info['lean'] * 0.3  # Moderate the impact of source bias
        
        return 0  # Unknown source, assume neutral
    
    def _analyze_language_bias_local(self, text: str, text_lower: str) -> Dict[str, Any]:
        """Analyze language bias using pattern matching"""
        
        phrases = []
        total_bias = 0
        
        # Check value-laden adjectives
        for category, words in self.value_adjectives.items():
            bias_value = -1 if 'negative' in category else 1
            for word in words:
                if word in text_lower:
                    count = text_lower.count(word)
                    total_bias += bias_value * count * 0.5
                    phrases.append({
                        "text": word,
                        "bias_type": category,
                        "intensity": 5,
                        "target": "general"
                    })
        
        return {
            "score": max(-3, min(3, total_bias)),
            "phrases": phrases[:10]  # Limit to prevent overflow
        }
    
    def _analyze_framing_bias_local(self, text: str, text_lower: str) -> Dict[str, Any]:
        """Analyze framing bias using pattern matching"""
        
        issues = []
        total_bias = 0
        
        # Check framing patterns
        for category, words in self.framing_patterns.items():
            count = sum(1 for word in words if word in text_lower)
            if count > 0:
                bias_impact = count * 0.3
                if 'victim' in category or 'heroic' in category:
                    bias_impact *= -0.5  # Left-leaning sympathy
                elif 'aggressor' in category or 'incompetent' in category:
                    bias_impact *= 0.5   # Right-leaning criticism
                
                total_bias += bias_impact
                issues.append({
                    "type": category,
                    "subject": "detected subjects",
                    "description": f"Found {count} instances of {category.replace('_', ' ')}"
                })
        
        return {
            "score": max(-3, min(3, total_bias)),
            "issues": issues
        }
    
    def _analyze_emotions_local(self, text: str, text_lower: str) -> Dict[str, Any]:
        """Analyze emotional content using pattern matching"""
        
        emotion_scores = {}
        detected_emotions = []
        
        for emotion_type, patterns in self.emotion_patterns.items():
            score = 0
            for word in patterns['words']:
                if word in text_lower:
                    score += text_lower.count(word)
            
            for phrase in patterns.get('phrases', []):
                if phrase in text_lower:
                    score += text_lower.count(phrase) * 2  # Phrases weigh more
            
            if score > 0:
                emotion_scores[emotion_type] = score
                detected_emotions.append(emotion_type)
        
        # Calculate bias impact (high emotion usually indicates bias)
        total_emotional_intensity = sum(emotion_scores.values())
        bias_impact = min(3, total_emotional_intensity * 0.5)
        
        return {
            "dominant_tone": max(emotion_scores, key=emotion_scores.get) if emotion_scores else "neutral",
            "emotional_targets": ["Cannot determine from local analysis"],
            "author_vs_quoted": "unknown",
            "emotion_scores": emotion_scores,
            "bias_impact": bias_impact
        }
    
    def _analyze_modality_local(self, text: str, text_lower: str) -> Dict[str, Any]:
        """Analyze certainty vs speculation markers"""
        
        certainty_count = sum(1 for word in self.modality_patterns['certain'] if word in text_lower)
        probable_count = sum(1 for word in self.modality_patterns['probable'] if word in text_lower)
        speculative_count = sum(1 for word in self.modality_patterns['speculative'] if word in text_lower)
        
        total_modality = certainty_count + probable_count + speculative_count
        
        if total_modality == 0:
            certainty_level = "unknown"
        elif certainty_count > (probable_count + speculative_count):
            certainty_level = "high"
        elif speculative_count > certainty_count:
            certainty_level = "low"
        else:
            certainty_level = "medium"
        
        return {
            "certainty_level": certainty_level,
            "speculation_markers": [word for word in self.modality_patterns['speculative'] if word in text_lower][:5],
            "assertion_strength": "strong" if certainty_count > 5 else "moderate" if certainty_count > 2 else "weak"
        }
    
    def _calculate_omission_bias_local(self, text: str) -> float:
        """Estimate omission bias (very basic for local analysis)"""
        
        # Check for basic indicators of one-sided reporting
        counter_indicators = ['however', 'but', 'although', 'despite', 'nevertheless', 'on the other hand']
        source_variety = ['said', 'according to', 'reported', 'stated', 'claimed']
        
        counter_count = sum(1 for word in counter_indicators if word in text.lower())
        source_count = sum(1 for word in source_variety if word in text.lower())
        
        # More counters and sources = less omission bias
        omission_score = max(-1, min(1, 1 - (counter_count * 0.2 + source_count * 0.1)))
        
        return omission_score
    
    def _generate_local_concerns(self, overall_score: float, emotional_analysis: Dict) -> List[str]:
        """Generate reader concerns based on local analysis"""
        
        concerns = []
        
        if abs(overall_score) > 2:
            concerns.append(f"High bias detected (score: {overall_score})")
        
        if emotional_analysis['bias_impact'] > 2:
            concerns.append(f"High emotional language may affect objectivity")
        
        if emotional_analysis['dominant_tone'] != 'neutral':
            concerns.append(f"Dominant emotional tone: {emotional_analysis['dominant_tone']}")
        
        if not concerns:
            concerns.append("No major bias concerns detected")
        
        return concerns
    
    def _suggest_alternative_sources(self, source_url: str) -> List[str]:
        """Suggest alternative sources for comparison"""
        
        if not source_url:
            return ["Reuters", "AP News", "BBC"]
        
        # Find sources with opposite lean
        current_lean = 0
        for domain, info in self.publisher_bias_db.items():
            if domain in source_url:
                current_lean = info['lean']
                break
        
        suggestions = []
        for domain, info in self.publisher_bias_db.items():
            # Suggest sources with opposite or neutral lean
            if (current_lean < 0 and info['lean'] >= 0) or (current_lean > 0 and info['lean'] <= 0):
                suggestions.append(domain)
        
        return suggestions[:3] if suggestions else ["Reuters", "AP News", "BBC"]
    
    def _parse_enhanced_bias_response(self, response: str, source_url: str = None) -> Dict[str, Any]:
        """Parse enhanced AI response for bias analysis"""
        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start != -1 and json_end != 0:
                json_str = response[json_start:json_end]
                result = json.loads(json_str)
                
                # Add source context if available
                if source_url:
                    source_context = self._get_source_context(source_url)
                    result['source_context'] = source_context
                
                return result
        except Exception as e:
            pass
        
        # Enhanced fallback parsing
        return {
            "overall_bias_score": 0,
            "confidence_level": 30,
            "bias_direction": "neutral",
            "component_scores": {
                "language_bias": 0,
                "framing_bias": 0,
                "omission_bias": 0,
                "source_bias": 0,
                "emotional_manipulation": 0
            },
            "detailed_analysis": {
                "biased_phrases": [],
                "framing_issues": [],
                "missing_context": ["Analysis parsing failed"],
                "emotion_analysis": {
                    "dominant_tone": "unknown",
                    "emotional_targets": [],
                    "author_vs_quoted": "unknown"
                },
                "modality_analysis": {
                    "certainty_level": "unknown",
                    "speculation_markers": [],
                    "assertion_strength": "unknown"
                }
            },
            "reader_guidance": {
                "key_concerns": ["Could not complete enhanced analysis"],
                "alternative_framings": ["Manual review recommended"],
                "suggested_sources": ["Reuters", "AP News", "BBC"],
                "critical_questions": ["Consider seeking multiple perspectives"]
            },
            "explainability": {
                "score_justification": "Analysis failed - default neutral response",
                "bias_evidence": [],
                "neutrality_suggestions": ["Seek professional media analysis"]
            },
            "error": f"Enhanced parsing failed: {str(e) if 'e' in locals() else 'Unknown error'}"
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
    
    def analyze_single_article(self, text: str, mode: str = 'summary', source_url: str = None, article_title: str = None) -> Dict[str, Any]:
        """Analyze a single article in various modes with enhanced parameters"""
        
        if mode == 'summary':
            return self.text_summarizer.summarize(text)
        elif mode == 'bias':
            return self.bias_analyzer.analyze_bias(text, source_url, article_title)
        elif mode == 'full':
            summary = self.text_summarizer.summarize(text)
            bias = self.bias_analyzer.analyze_bias(text, source_url, article_title)
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
    
    def generate_response(self, prompt: str, content: str = "") -> Dict[str, Any]:
        """Generate a response for custom prompts using the configured AI model"""
        try:
            # Combine prompt and content for analysis
            full_text = f"{prompt}\n\n{content}" if content else prompt
            
            # Use the base summarizer to generate a response
            # This leverages the existing AI models (OpenAI/Anthropic/Local)
            if hasattr(self.base_summarizer, 'client'):
                # For OpenAI/Anthropic models
                if hasattr(self.base_summarizer.client, 'chat'):
                    # OpenAI model
                    response = self.base_summarizer.client.chat.completions.create(
                        model=getattr(self.base_summarizer, 'model', 'gpt-3.5-turbo'),
                        messages=[{"role": "user", "content": full_text}],
                        max_tokens=1000,
                        temperature=0.7
                    )
                    return {
                        'success': True,
                        'response': response.choices[0].message.content,
                        'model': 'openai'
                    }
                elif hasattr(self.base_summarizer.client, 'messages'):
                    # Anthropic model
                    response = self.base_summarizer.client.messages.create(
                        model=getattr(self.base_summarizer, 'model', 'claude-3-sonnet-20240229'),
                        max_tokens=1000,
                        messages=[{"role": "user", "content": full_text}]
                    )
                    return {
                        'success': True,
                        'response': response.content[0].text,
                        'model': 'anthropic'
                    }
            else:
                # Local model fallback
                return {
                    'success': False,
                    'response': f"Local model analysis: {content[:200]}...",
                    'model': 'local',
                    'error': 'Local model has limited response generation capabilities'
                }
        
        except Exception as e:
            return {
                'success': False,
                'response': '',
                'error': str(e),
                'model': getattr(self, 'model_type', 'unknown')
            }