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