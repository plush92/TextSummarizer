#!/usr/bin/env python3
"""
Test script for the enhanced bias analysis system
"""
import os

# Set dummy API key for testing BEFORE any imports
os.environ['OPENAI_API_KEY'] = 'sk-dummy-key-for-testing'

from summarizer import TextSummarizer, BiasAnalyzer, AnalysisEngine
import pandas as pd

def test_enhanced_system():
    print("Testing Enhanced Bias Analysis System")
    print("=" * 50)
    
    try:
        # Create TextSummarizer instance with local model (no API key required)
        summarizer = TextSummarizer(model_type='local')
        print("✅ TextSummarizer created successfully (local mode)")
        
        # Create BiasAnalyzer with the summarizer instance
        analyzer = BiasAnalyzer(summarizer)
        print("✅ BiasAnalyzer created successfully")
        
        # Test publisher bias database
        print("\nTesting Publisher Bias Database:")
        test_domains = ['cnn.com', 'foxnews.com', 'bbc.com', 'reuters.com']
        for domain in test_domains:
            score = analyzer._get_publisher_bias(domain)
            print(f"  {domain}: {score}")
        
        # Test emotion patterns
        print("\nTesting Emotional Language Detection:")
        test_texts = [
            "This shocking revelation destroys everything we thought we knew!",
            "The data shows a moderate increase in economic indicators.",
            "BREAKING: Devastating scandal rocks the political establishment!"
        ]
        
        for text in test_texts:
            emotion_score = analyzer._detect_emotional_language(text)
            print(f"  '{text[:30]}...': {emotion_score}")
        
        # Test AnalysisEngine initialization  
        engine = AnalysisEngine(model_type='local')
        print("✅ AnalysisEngine created successfully (local mode)")
        
        print("\n✅ All enhanced bias analysis components working!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_enhanced_system()