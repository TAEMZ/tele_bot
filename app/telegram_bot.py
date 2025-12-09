
from app.model import safe_generate_response  # Change this import
from app.memory import add_to_memory, clear_user_memory, get_all_memories
from app.metrics import RequestTimer
import telebot
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = "7962443530:AAHH6mdIexuTKw9J2Js0SMtwJ5Jtfe8yNe8"

bot = telebot.TeleBot(TELEGRAM_TOKEN)

def detect_language(text: str) -> str:
    """Simple language detection for Amharic and Afan Oromo"""
    text_lower = text.lower()
    
    # Common Amharic characters (only actual Amharic Unicode)
    amharic_indicators = ['ሀ', 'ለ', 'ሐ', 'መ', 'ሠ', 'ረ', 'ሰ', 'ሸ', 'ቀ', 'በ', 'ተ', 'ቸ', 'ኀ', 'ነ',
                          'ኘ', 'አ', 'ከ', 'ኸ', 'ወ', 'ዐ', 'ዘ', 'ዠ', 'የ', 'ደ', 'ጀ', 'ገ', 'ጠ', 'ጨ',
                          'ጰ', 'ጸ', 'ፀ', 'ፈ', 'ፐ']
    
    # Better Afan Oromo words (avoid English overlaps)
    oromo_indicators = [
        'akkam', 'nagaa', 'fayyaa', 'dhukkuba', 'mataa', 'garaa', 
        'gammadaa', 'hooina', 'dhadachiisa', 'dhiifama', 'maqaa', 'sababaa',
        'tajaajila', 'dhangalaa', 'faayidaa', 'maaltu', 'maal', 'maali',
        'jirta', 'booda', 'guyyaa', 'jedhe', 'dhaan', 'irratti', 'keessa'
    ]
    
    # Check for Amharic characters
    amharic_count = 0
    amharic_found = []
    for char in text:
        if char in amharic_indicators:
            amharic_count += 1
            amharic_found.append(char)
    
    # Check for Afan Oromo words - use word boundaries to avoid partial matches
    import re
    oromo_count = 0
    oromo_found = []
    for word in oromo_indicators:
        # Use regex with word boundaries to match whole words only
        if re.search(r'\b' + re.escape(word) + r'\b', text_lower):
            oromo_count += 1
            oromo_found.append(word)
    
    # DEBUG PRINT
    print(f"🔍 LANGUAGE DETECTION DEBUG:")
    print(f"   Input text: '{text}'")
    print(f"   Amharic count: {amharic_count}, found: {amharic_found}")
    print(f"   Oromo count: {oromo_count}, found: {oromo_found}")
    print(f"   Final decision: {'am' if amharic_count > 0 else 'om' if oromo_count > 1 else 'en (default)'}")
    
    if amharic_count > 0:
        return "am"  # Amharic
    elif oromo_count > 1:  # Require at least 2 distinct Oromo words
        return "om"  # Afan Oromo
    else:
        return "am"  # Default to English (CHANGED THIS!)
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    welcome_msg = (
        "👋 ሰላም! Akkam jirta! I'm Ambomedic, your health assistant.\n\n"
        "I can help with health questions in multiple languages:\n"
        "• Amharic (አማርኛ)\n"
        "• Afan Oromo (Oromiffa)\n"
        "• English\n\n"
        "🔍 **Examples in Amharic:**\n"
        "• ራስ ምታት ምን ማለት ነው?\n"
        "• ሆድ ማቃጠል ምን ማድረግ አለብኝ?\n"
        "• ጉንፋን ካጋጠመኝ ምን ማድረግ አለብኝ?\n\n"
        "🔍 **Examples in Afan Oromo:**\n"
        "• Maqaan dhukkuba mataa maali?\n"
        "• Dhukkuba garaa yoo na qabe maaltu naaf tajaajila?\n"
        "• Gammadaa yoo na qabe maaltu naaf tajaajila?\n\n"
        "Commands:\n"
        "/clear - Clear conversation memory\n"
        "/language - Show language information\n\n"
        "Just ask your question in any language!"
    )
    bot.reply_to(message, welcome_msg)

@bot.message_handler(commands=['clear'])
def clear_memory(message):
    user_id = str(message.from_user.id)
    clear_user_memory(user_id)
    bot.reply_to(message, "✅ Conversation memory cleared. Starting fresh!")
    logger.info(f"Cleared memory for user {user_id}")

@bot.message_handler(commands=['memory'])
def show_memory(message):
    user_id = str(message.from_user.id)
    memories = get_all_memories(user_id)
    if not memories:
        bot.reply_to(message, "No conversation history found.")
        return

    memory_text = "📝 Your conversation history:\n\n"
    for i, mem in enumerate(memories[:5], 1):
        memory_text += f"{i}. {mem.get('memory', 'N/A')}\n"

    bot.reply_to(message, memory_text)

@bot.message_handler(commands=['language', 'luqaa'])
def language_info(message):
    """Show language support information"""
    lang_msg = (
        "🌍 **Language Support:**\n\n"
        "**Amharic (አማርኛ):**\n"
        "• ሰላም - Hello\n"
        "• ራስ ምታት - Headache\n"
        "• ሆድ ህመም - Stomach pain\n"
        "• ጉንፋን - Flu/Cold\n\n"
        "**Afan Oromo (Oromiffa):**\n"
        "• Akkam - Hello\n"
        "• Dhukkuba mataa - Headache\n"
        "• Dhukkuba garaa - Stomach pain\n"
        "• Gammadaa - Flu/Cold\n\n"
        "I automatically detect your language and respond accordingly!"
    )
    bot.reply_to(message, lang_msg)

def get_fallback_response(language: str) -> str:
    """Get a safe fallback response when AI fails"""
    fallbacks = {
        "am": "❌ ይቅርታ፣ በአሁኑ ሰዓት መልስ ማሰራጨት አልተቻለም። እባክዎ ቆይተው እንደገና ይሞክሩ።",
        "om": "❌ Dhiifama, odeeffannoo kennuu hin dandeenye. Yeroo booda irra deebi'ii yaali.",
        "en": "❌ Sorry, I couldn't generate a response right now. Please try again in a moment."
    }
    return fallbacks.get(language, fallbacks["en"])

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_message = message.text
    user_id = str(message.from_user.id)
    
    logger.info(f"📨 Received from user {user_id}: {user_message}")

    # Auto-detect language and pass to generate_response
    detected_language = detect_language(user_message)
    logger.info(f"🌍 Detected language2: {detected_language}")

    # Track request with metrics
    with RequestTimer(user_id=user_id) as timer:
        try:
            # Generate response using hybrid medical AI system - USE SAFE VERSION
            start_ai = time.time()
            
            # Use asyncio.run() to call async function from sync handler
            import asyncio
            response = asyncio.run(safe_generate_response(user_message, user_id=user_id, target_language=detected_language))
            
            ai_time = time.time() - start_ai

            # Set AI generation time for metrics
            timer.set_ai_time(ai_time)

            # Clean up response if needed
            if response and "Assistant:" in response:
                response = response.split("Assistant:")[-1].strip()

            # CRITICAL FIX: Validate response before sending
            if not response or response.strip() == "":
                logger.warning("⚠️ Empty response generated, using fallback")
                response = get_fallback_response(detected_language)
            
            logger.info(f"✅ Generated response: {response[:200]}...")
            bot.reply_to(message, response)

        except Exception as e:
            logger.error(f"❌ Error generating response: {e}")
            # Use fallback response instead of re-raising the exception
            fallback_response = get_fallback_response(detected_language)
            bot.reply_to(message, fallback_response)

    # Memory disabled for faster responses
    # Uncomment below to enable conversation memory (adds 5-10s delay)
    # try:
    #     add_to_memory(user_id, user_message, role="user")
    #     add_to_memory(user_id, response, role="assistant")
    # except Exception as e:
    #     logger.error(f"Memory storage error (non-critical): {e}")

# ADD THIS BLOCK AT THE END
if __name__ == "__main__":
    print("🤖 Starting Telegram bot...")
    print("🔑 API Key configured")
    print("💬 Bot is ready to receive messages...")
    print("🌍 Supports Amharic and Afan Oromo!")

    try:
        # Test the API connection first
        print("🧪 Testing API connection...")
        from app.model import safe_generate_response, debug_api_connection  # Add these imports
        
        # Run diagnostics
        print("🧪 Running API diagnostics...")
        api_working = debug_api_connection()
        
        if not api_working:
            print("❌ API diagnostics failed! Check your configuration.")
            print("💡 Make sure your ADDIS_ASSISTANT_API_KEY is set in .env file")
        else:
            print("✅ API diagnostics passed!")

        # Test with safe function
        test_response = safe_generate_response("test", "startup_test")
        print(f"🧪 API Test Result: {test_response[:100]}...")

        print("🚀 Starting bot polling...")
        bot.polling(none_stop=True, timeout=60)

    except Exception as e:
        print(f"❌ Bot failed to start: {e}")
        import traceback
        traceback.print_exc()