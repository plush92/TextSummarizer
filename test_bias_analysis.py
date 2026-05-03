#!/usr/bin/env python3
"""
Quick test of the dynamic bias analysis logic
"""

def analyze_bias(text):
    """Test the bias analysis logic with different texts"""
    text_lower = text.lower() if text else ''
    words = text_lower.split()
    total_words = len(words)
    
    # Same indicators as in the main app
    left_indicators = ['human rights', 'civil rights', 'press freedom', 'criticism', 'ban', 'targeting', 'suppression', 
                     'activists', 'protesters', 'social justice', 'inequality', 'discrimination', 'marginalized', 
                     'progressive', 'reform', 'democratic values', 'transparency', 'accountability']
    
    right_indicators = ['security', 'threat', 'national security', 'terrorism', 'law and order', 'traditional', 
                  'conservative', 'stability', 'economic growth', 'free market', 'strong leadership', 
                  'patriotic', 'defense', 'enforcement', 'order', 'authority']
    
    neutral_indicators = ['according to', 'reported', 'statement', 'announced', 'said', 'data shows', 
                        'statistics indicate', 'research suggests', 'study found', 'officials state']
    
    # Calculate weights
    left_weight = sum(text_lower.count(term) for term in left_indicators)
    right_weight = sum(text_lower.count(term) for term in right_indicators) 
    neutral_weight = sum(text_lower.count(term) for term in neutral_indicators)
    
    # Calculate bias score
    if total_words > 0:
        left_ratio = (left_weight / total_words) * 100
        right_ratio = (right_weight / total_words) * 100
        neutral_ratio = (neutral_weight / total_words) * 100
        
        raw_score = (right_ratio - left_ratio) * 2
        neutrality_factor = min(neutral_ratio * 0.3, 2.0)
        bias_score = raw_score * (1 - neutrality_factor/10)
        bias_score = max(-5, min(5, bias_score))
    else:
        bias_score = 0
        left_ratio = right_ratio = neutral_ratio = 0
    
    # Determine direction
    if abs(bias_score) < 0.5:
        direction = "Center/Neutral"
    elif bias_score < 0:
        direction = "Left-leaning"
    else:
        direction = "Right-leaning"
    
    return {
        'bias_score': bias_score,
        'direction': direction,
        'left_weight': left_weight,
        'right_weight': right_weight,
        'neutral_weight': neutral_weight,
        'total_words': total_words,
        'left_ratio': left_ratio,
        'right_ratio': right_ratio,
        'neutral_ratio': neutral_ratio,
        'raw_score': raw_score if total_words > 0 else 0
    }

# Test with different articles
if __name__ == "__main__":
    
    # Test 1: Al Jazeera article (should lean left due to press freedom, human rights, targeting, criticism)
    al_jazeera_text = """Israel's government has moved to shut down the operations of the Al Jazeera television network in the country, branding it a mouthpiece for Hamas. Prime Minister Benjamin Netanyahu said the cabinet agreed to the closure while the war in Gaza is ongoing. The shut down of Al Jazeera in Israel has been criticised by a number of human rights and press groups who called it targeting critical voices and silencing Arab media. The Association for Civil Rights said the ban serves a politically motivated agenda aimed at suppressing press freedom."""
    
    # Test 2: Security-focused article (should lean right)
    security_text = """The government announced new national security measures to combat terrorism threats. Officials said the law and order policies will ensure stability and protect traditional values. Conservative leaders praised the strong leadership approach to defense, citing the need for enforcement and authority in maintaining economic growth and free market principles."""
    
    # Test 3: Neutral reporting (should be center)
    neutral_text = """According to officials, the new policy was announced yesterday. The statement reported that various groups have different opinions. Data shows mixed reactions from stakeholders. Research suggests the impact remains to be determined. Study found that implementation will take several months."""
    
    print("=== BIAS ANALYSIS TESTING ===\n")
    
    print("1. AL JAZEERA ARTICLE:")
    result1 = analyze_bias(al_jazeera_text)
    print(f"   Bias Score: {result1['bias_score']:.2f}")
    print(f"   Direction: {result1['direction']}")
    print(f"   Left indicators: {result1['left_weight']}, Right indicators: {result1['right_weight']}")
    print(f"   Total words: {result1['total_words']}")
    print(f"   Raw score: {result1['raw_score']:.2f}")
    
    print("\n2. SECURITY-FOCUSED ARTICLE:")
    result2 = analyze_bias(security_text)
    print(f"   Bias Score: {result2['bias_score']:.2f}")
    print(f"   Direction: {result2['direction']}")
    print(f"   Left indicators: {result2['left_weight']}, Right indicators: {result2['right_weight']}")
    print(f"   Total words: {result2['total_words']}")
    print(f"   Raw score: {result2['raw_score']:.2f}")
    
    print("\n3. NEUTRAL REPORTING:")
    result3 = analyze_bias(neutral_text)
    print(f"   Bias Score: {result3['bias_score']:.2f}")
    print(f"   Direction: {result3['direction']}")
    print(f"   Left indicators: {result3['left_weight']}, Right indicators: {result3['right_weight']}")
    print(f"   Total words: {result3['total_words']}")
    print(f"   Raw score: {result3['raw_score']:.2f}")
    
    print("\n=== VERIFICATION ===")
    print("✅ Different articles should produce different scores")
    print(f"Al Jazeera: {result1['bias_score']:.2f} vs Security: {result2['bias_score']:.2f} vs Neutral: {result3['bias_score']:.2f}")
    
    if result1['bias_score'] != result2['bias_score'] != result3['bias_score']:
        print("✅ SUCCESS: All three articles have different bias scores!")
    else:
        print("❌ FAILURE: Some articles have the same scores")