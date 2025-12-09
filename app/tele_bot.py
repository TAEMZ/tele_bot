from app.model import generate_response
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
    
    # Common Amharic words/characters
    amharic_indicators = ['ሀ', 'ለ', 'ሐ', 'መ', 'ሠ', 'ረ', 'ሰ', 'ሸ', 'ቀ', 'በ', 'ተ', 'ቸ', 'ኀ', 'ነ', 'ኘ', 'አ', 'ከ', 'ኸ', 'ወ', 'ዐ', 'ዘ', 'ዠ', 'የ', 'ደ', 'ጀ', 'ገ', 'ጠ', 'ጨ', 'ጰ', 'ጸ', 'ፀ', 'ፈ', 'ፐ', 'ች', 'ን', 'ም', 'ው', 'ዎ', 'ና', 'ኝ']
    
    # Common Afan Oromo words
    oromo_indicators = ['akka', 'fi', 'kan', 'tti', 'irra', 'waan', 'hin', 'ni', 'jedhe', 'dhaan', 'irratti', 'kana', 'keessa', 'booda', 'dura', 'gara', 'waliin', 'jira', 'dha', 'tahe', 'qaba', 'nam', 'mana', 'bira', 'hojii', 'bara', 'guyyaa']
    
    # Check for Amharic characters
    amharic_count = sum(1 for char in text if char in amharic_indicators)
    
    # Check for Afan Oromo words
    oromo_count = sum(1 for word in oromo_indicators if word in text_lower)
    
    if amharic_count > 0:
        return "am"  # Amharic
    elif oromo_count > 2:  # If multiple Oromo words detected
        return "om"  # Afan Oromo
    else:
        return "am"  # Default to Amharic

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    welcome_msg = (
        "👋 ሰላም! Akkam jirta! የጤና ረዳት ቦት ነኝ።\n\n"
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

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    user_message = message.text
    user_id = str(message.from_user.id)
    logger.info(f"Received message from user {user_id}: {user_message}")

    # Auto-detect language and pass to generate_response
    detected_language = detect_language(user_message)
    logger.info(f"Detected language: {detected_language}")

    # Track request with metrics (language is now handled by Addis Assistant API)
    with RequestTimer(user_id=user_id) as timer:
        try:
            # Generate response with automatic translation - pass detected language
            start_ai = time.time()
            response = generate_response(user_message, user_id=user_id, target_language=detected_language)
            ai_time = time.time() - start_ai

            # Set AI generation time for metrics
            timer.set_ai_time(ai_time)

            if "Assistant:" in response:
                response = response.split("Assistant:")[-1].strip()

            logger.info(f"Generated response: {response}")
            bot.reply_to(message, response)

        except Exception as e:
            logger.error(f"Error generating response: {e}")
            bot.reply_to(message, "Sorry, I encountered an error. Please try again.")
            raise  # Re-raise to mark as error in metrics

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
        test_response = generate_response("test", "startup_test")
        print(f"🧪 API Test Result: {test_response[:100]}...")

        print("🚀 Starting bot polling...")
        bot.polling(none_stop=True, timeout=60)

    except Exception as e:
        print(f"❌ Bot failed to start: {e}")
        import traceback
        traceback.print_exc()
