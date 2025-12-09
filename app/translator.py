"""
Automatic language detection and translation using Google Translate API
Uses API Key authentication (simpler than service account)
"""

import os
import logging
import requests
import re
from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)

# Google Translate API endpoint
TRANSLATE_API_URL = "https://translation.googleapis.com/language/translate/v2"

def get_api_key():
    """Get the Google Translate API key from environment"""
    api_key = os.environ.get('GOOGLE_TRANSLATE_API_KEY')
    if not api_key:
        logger.warning("GOOGLE_TRANSLATE_API_KEY not set. Translation will be disabled.")
    return api_key

def detect_language(text: str) -> str:
    """
    Detect the language of the given text.
    Uses character-based detection for Ethiopian languages (Amharic, Tigrinya)
    Falls back to langdetect for other languages.

    Args:
        text: Input text to detect language

    Returns:
        Language code (e.g., 'en', 'am', 'om', 'ti', 'so')
    """
    try:
        # First, check for Ethiopic script (Amharic, Tigrinya, etc.)
        # Ethiopic Unicode range: U+1200 to U+137F
        ethiopic_chars = re.findall(r'[\u1200-\u137F]', text)
        if ethiopic_chars:
            # If text contains Ethiopic script, it's likely Amharic or Tigrinya
            # We'll default to Amharic and let Google Translate detect the exact language
            logger.info(f"Detected Ethiopic script (Amharic/Tigrinya)")
            return 'am'  # Default to Amharic, Google will auto-detect the exact one

        # Check for Arabic script (Somali can sometimes use Arabic script)
        arabic_chars = re.findall(r'[\u0600-\u06FF]', text)
        if arabic_chars:
            logger.info(f"Detected Arabic script")
            return 'ar'

        # Use langdetect for Latin-script languages (English, Oromo, Somali, etc.)
        lang_code = detect(text)
        logger.info(f"Detected language: {lang_code}")
        return lang_code
    except LangDetectException as e:
        logger.warning(f"Language detection failed: {e}. Defaulting to English.")
        return 'en'
    except Exception as e:
        logger.error(f"Unexpected error in language detection: {e}")
        return 'en'

def translate_text(text: str, target_language: str = 'en', source_language: str = None) -> dict:
    """
    Translate text to target language using Google Translate REST API.

    Args:
        text: Text to translate
        target_language: Target language code (default: 'en')
        source_language: Source language code (optional, will auto-detect if not provided)

    Returns:
        Dictionary with:
            - translated_text: The translated text
            - source_language: Detected or provided source language
            - target_language: Target language
            - original_text: Original input text
    """
    api_key = get_api_key()

    if not api_key:
        logger.warning("Translation client not available. Returning original text.")
        return {
            'translated_text': text,
            'source_language': source_language or 'unknown',
            'target_language': target_language,
            'original_text': text,
            'translation_available': False
        }

    try:
        # Build request parameters
        params = {
            'key': api_key,
            'q': text,
            'target': target_language,
            'format': 'text'
        }

        if source_language:
            params['source'] = source_language

        # Make API request
        response = requests.post(TRANSLATE_API_URL, params=params, timeout=10)
        response.raise_for_status()

        result = response.json()

        if 'data' in result and 'translations' in result['data']:
            translation_data = result['data']['translations'][0]
            translated_text = translation_data['translatedText']
            detected_lang = translation_data.get('detectedSourceLanguage', source_language)

            logger.info(f"Translated from {detected_lang} to {target_language}")

            return {
                'translated_text': translated_text,
                'source_language': detected_lang,
                'target_language': target_language,
                'original_text': text,
                'translation_available': True
            }
        else:
            raise Exception("Unexpected API response format")

    except requests.exceptions.RequestException as e:
        logger.error(f"Translation API request failed: {e}")
        return {
            'translated_text': text,
            'source_language': source_language or 'unknown',
            'target_language': target_language,
            'original_text': text,
            'translation_available': False,
            'error': str(e)
        }
    except Exception as e:
        logger.error(f"Translation failed: {e}")
        return {
            'translated_text': text,
            'source_language': source_language or 'unknown',
            'target_language': target_language,
            'original_text': text,
            'translation_available': False,
            'error': str(e)
        }

def translate_to_english(text: str) -> dict:
    """
    Convenience function to translate text to English.
    Auto-detects source language.

    Args:
        text: Text to translate

    Returns:
        Dictionary with translation details
    """
    return translate_text(text, target_language='en')

def translate_from_english(text: str, target_language: str) -> dict:
    """
    Convenience function to translate from English to target language.

    Args:
        text: English text to translate
        target_language: Target language code

    Returns:
        Dictionary with translation details
    """
    return translate_text(text, target_language=target_language, source_language='en')

def is_english(text: str) -> bool:
    """
    Check if text is in English.

    Args:
        text: Text to check

    Returns:
        True if text is in English, False otherwise
    """
    # Check for Ethiopic script first
    ethiopic_chars = re.findall(r'[\u1200-\u137F]', text)
    if ethiopic_chars:
        return False

    # Check for Arabic script
    arabic_chars = re.findall(r'[\u0600-\u06FF]', text)
    if arabic_chars:
        return False

    try:
        lang = detect(text)
        return lang == 'en'
    except:
        return True  # Default to English if detection fails
