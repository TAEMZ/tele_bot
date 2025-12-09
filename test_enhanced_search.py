"""
Quick test for enhanced internet search with content extraction
"""
from app.tools import internet_search

def test_enhanced_search():
    print("🧪 Testing Enhanced Internet Search")
    print("=" * 60)
    
    query = "Marburg virus Ethiopia 2024"
    print(f"Query: {query}\n")
    
    result = internet_search(query, num_results=2)
    
    if "error" in result:
        print(f"❌ Error: {result['error']}")
    else:
        print("✅ Search successful!\n")
        print("Results:")
        print("-" * 60)
        print(result['summary'])
        print("-" * 60)
        
        # Check if we got detailed content
        has_details = "Details:" in result['summary'] or "Summary:" in result['summary']
        has_sources = "Source:" in result['summary']
        
        print(f"\n✅ Has source citations: {has_sources}")
        print(f"✅ Has detailed content: {has_details}")

if __name__ == "__main__":
    test_enhanced_search()
