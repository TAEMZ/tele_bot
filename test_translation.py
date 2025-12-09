#!/usr/bin/env python3
"""Test script to verify Google Translate API is working"""

import os
import sys

# Add app directory to path
sys.path.insert(0, '/app')

from app.translator import translate_to_english, translate_from_english, detect_language, get_api_key

def test_translation():
    print("=" * 60)
    print("Google Translate API Test")
    print("=" * 60)
    print()

    # Check API key
    api_key = get_api_key()
    if api_key:
        print(f"✓ API Key loaded: {api_key[:20]}...")
    else:
        print("✗ No API Key found!")
        return
    print()

    # Test 1: Language Detection
    print("Test 1: Language Detection")
    print("-" * 40)
    test_texts = {
        "Hello, how are you?": "en",
        "ራስ ይምታል": "am",
        "Mataan na dhukkuba": "om",
        "Madax ayaa i xanuunaya": "so",
    }

    for text, expected_lang in test_texts.items():
        detected = detect_language(text)
        status = "✓" if detected == expected_lang else "✗"
        print(f"{status} '{text}' → Detected: {detected} (Expected: {expected_lang})")
    print()

    # Test 2: Translation to English
    print("Test 2: Translation to English")
    print("-" * 40)
    amharic_text = "ራስ ይምታል"
    print(f"Original (Amharic): {amharic_text}")

    result = translate_to_english(amharic_text)

    if result.get('translation_available'):
        print(f"✓ Translated: {result['translated_text']}")
        print(f"  Source Language: {result['source_language']}")
        print(f"  Target Language: {result['target_language']}")
    else:
        print(f"✗ Translation failed: {result.get('error', 'Unknown error')}")
    print()

    # Test 3: Translation from English
    print("Test 3: Translation from English to Amharic")
    print("-" * 40)
    english_text = "I have a headache"
    print(f"Original (English): {english_text}")

    result = translate_from_english(english_text, 'am')

    if result.get('translation_available'):
        print(f"✓ Translated: {result['translated_text']}")
        print(f"  Source Language: {result['source_language']}")
        print(f"  Target Language: {result['target_language']}")
    else:
        print(f"✗ Translation failed: {result.get('error', 'Unknown error')}")
    print()

    # Test 4: Round-trip translation
    print("Test 4: Round-trip Translation (Amharic → English → Amharic)")
    print("-" * 40)
    original = "ራስ ይምታል"
    print(f"1. Original: {original}")

    # To English
    to_en = translate_to_english(original)
    if to_en.get('translation_available'):
        print(f"2. To English: {to_en['translated_text']}")

        # Back to Amharic
        back_to_am = translate_from_english(to_en['translated_text'], 'am')
        if back_to_am.get('translation_available'):
            print(f"3. Back to Amharic: {back_to_am['translated_text']}")
            print("✓ Round-trip successful!")
        else:
            print("✗ Translation back to Amharic failed")
    else:
        print("✗ Translation to English failed")
    print()

    print("=" * 60)
    print("Test Complete!")
    print("=" * 60)

if __name__ == "__main__":
    try:
        test_translation()
    except Exception as e:
        print(f"Error running tests: {e}")
        import traceback
        traceback.print_exc()
