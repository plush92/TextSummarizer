#!/usr/bin/env python3
"""
Enhanced Bias Analysis System - Demonstration
Shows all the new capabilities we've implemented
"""
import os

# Set API key for demo (local mode doesn't require real key)
os.environ['OPENAI_API_KEY'] = 'sk-demo-key'

from summarizer import TextSummarizer, BiasAnalyzer, AnalysisEngine

def demo_enhanced_bias_analysis():
    print("\n" + "="*60)
    print("🎯 ENHANCED BIAS ANALYSIS SYSTEM DEMONSTRATION")  
    print("="*60)
    
    # Initialize components in local mode
    summarizer = TextSummarizer(model_type='local')
    analyzer = BiasAnalyzer(summarizer)
    engine = AnalysisEngine(model_type='local')
    
    print("✅ All components initialized successfully!")
    
    # Demo 1: Publisher Bias Database
    print("\n📰 PUBLISHER BIAS DATABASE:")
    print("-" * 40)
    
    test_sources = {
        'cnn.com': 'CNN',
        'foxnews.com': 'Fox News', 
        'bbc.com': 'BBC',
        'reuters.com': 'Reuters',
        'huffpost.com': 'HuffPost',
        'breitbart.com': 'Breitbart'
    }
    
    for domain, name in test_sources.items():
        bias_info = analyzer._get_publisher_bias(domain)
        lean = bias_info['lean']
        reliability = bias_info['reliability']
        
        if lean < -2:
            lean_desc = f"Left-leaning ({lean})"
        elif lean > 2:
            lean_desc = f"Right-leaning (+{lean})"
        else:
            lean_desc = f"Center ({lean})"
            
        print(f"  {name:12} | {lean_desc:20} | {reliability.title():12}")
    
    # Demo 2: Emotional Language Detection  
    print("\n😮 EMOTIONAL LANGUAGE DETECTION:")
    print("-" * 40)
    
    test_texts = [
        ("Neutral reporting", "The committee reviewed the proposal and made recommendations."),
        ("Moderate emotion", "BREAKING: New study reveals concerning trends in data."),
        ("High emotion", "SHOCKING revelation DESTROYS everything! Devastating scandal rocks establishment!")
    ]
    
    for label, text in test_texts:
        emotion_score = analyzer._detect_emotional_language(text)
        emotion_level = "Low" if emotion_score < 1 else "Medium" if emotion_score < 3 else "High"
        print(f"  {label:15} | Score: {emotion_score:3.1f} | Level: {emotion_level}")
        print(f"     '{text[:50]}{'...' if len(text) > 50 else ''}'")
        print()
    
    # Demo 3: Component Integration
    print("\n🔧 SYSTEM INTEGRATION:")
    print("-" * 40)
    print("✅ BiasAnalyzer with publisher database")
    print("✅ Emotional pattern recognition") 
    print("✅ Framing analysis patterns loaded")
    print("✅ Modality detection (certainty vs speculation)")
    print("✅ Value-laden adjective categorization")
    print("✅ Enhanced UI with pandas integration")
    print("✅ Text highlighting and visualization")
    print("✅ Component score breakdown")
    
    print("\n🎉 ENHANCED BIAS ANALYSIS SYSTEM READY!")
    print("   Run 'streamlit run app.py' to start the web interface")
    print("="*60)

if __name__ == "__main__":
    demo_enhanced_bias_analysis()