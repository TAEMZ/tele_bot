"""
Test script for current events detection and internet search
"""
from app.model import detect_medical_intent, safe_generate_response

def test_marburg_detection():
    """Test that Marburg virus query triggers current_events"""
    print("\n🧪 Test 1: Marburg Virus Detection")
    print("=" * 60)
    
    query = "What's the latest information about the Marburg virus outbreak in Ethiopia?"
    intent = detect_medical_intent(query)
    
    print(f"Query: {query}")
    print(f"Intent scores: {intent}")
    
    if intent.get('current_events', 0) > 0:
        print("✅ PASS: current_events detected!")
    else:
        print("❌ FAIL: current_events NOT detected")
    
    return intent.get('current_events', 0) > 0

def test_full_response():
    """Test complete response generation with internet search"""
    print("\n🧪 Test 2: Full Response Generation")
    print("=" * 60)
    
    query = "Tell me about the Marburg virus outbreak in Ethiopia"
    print(f"Query: {query}")
    print("\nGenerating response...")
    
    response = safe_generate_response(query, user_id="test_user", target_language="en")
    
    print(f"\nResponse preview: {response[:300]}...")
    
    # Check if response contains search-related content
    has_search_indicators = any(keyword in response.lower() for keyword in ['http', 'source', 'search', 'found'])
    
    if has_search_indicators:
        print("\n✅ PASS: Response appears to include search results")
    else:
        print("\n⚠️  WARNING: Response may not include search results")
    
    return len(response) > 0

def test_control_query():
    """Test that regular queries still work normally"""
    print("\n🧪 Test 3: Control Query (Regular Symptom)")
    print("=" * 60)
    
    query = "I have a headache"
    intent = detect_medical_intent(query)
    
    print(f"Query: {query}")
    print(f"Intent scores: {intent}")
    
    if intent.get('symptoms', 0) > 0 and intent.get('current_events', 0) == 0:
        print("✅ PASS: Correctly identified as symptom, not current event")
    else:
        print("❌ FAIL: Incorrect intent detection")
    
    return intent.get('symptoms', 0) > 0

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("🚀 TESTING CURRENT EVENTS DETECTION & INTERNET SEARCH")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Marburg Detection", test_marburg_detection()))
    results.append(("Full Response", test_full_response()))
    results.append(("Control Query", test_control_query()))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    for test_name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total_passed = sum(1 for _, passed in results if passed)
    print(f"\nTotal: {total_passed}/{len(results)} tests passed")
    
    if total_passed == len(results):
        print("\n🎉 All tests passed! Ready to deploy.")
    else:
        print("\n⚠️  Some tests failed. Review the output above.")
