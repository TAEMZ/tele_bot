import os
from dotenv import load_dotenv
import json, re, logging, requests
import httpx
import app.tools as tools
from app.memory import get_relevant_context

# Load environment variables
load_dotenv()

# API configuration
ADDIS_API_URL = "https://api.addisassistant.com/api/v1/chat_generate"
ADDIS_API_KEY = os.environ.get("ADDIS_ASSISTANT_API_KEY", "sk_ffee3fb8-108c-46fc-8a06-8db8b26a035b_3d005604e58bc8bb7ec35bd5313ef5b5f5c117fb020d0e20de39217418c59947")
MAX_CHARS = 4000

# Set up logging
logger = logging.getLogger(__name__)

def debug_api_connection():
    """Test the API connection and settings"""
    print("🔍 Debugging API Connection...")
    
    # Check API key
    api_key = os.environ.get("ADDIS_ASSISTANT_API_KEY")
    if not api_key:
        print("❌ API Key not found in environment variables")
        return False
    
    print(f"✅ API Key found: {api_key[:20]}...")
    print(f"✅ API URL: {ADDIS_API_URL}")
    
    # Test a simple request
    test_prompt = "Hello"
    try:
        headers = {
            "Content-Type": "application/json",
            "X-API-Key": api_key,
        }
        
        data = {
            "prompt": test_prompt,
            "target_language": "en",
            "generation_config": {
                "temperature": 0.7,
                "max_tokens": 100
            }
        }
        
        print("🔄 Sending test request...")
        response = requests.post(ADDIS_API_URL, headers=headers, json=data, timeout=10)
        print(f"✅ Response status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ API Response: {result}")
            return True
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return False

def detect_medical_intent(text: str) -> dict:
    """
    Detect if the user is asking about medical symptoms, drugs, or general health
    Returns scores for different medical intents
    """
    text_lower = text.lower().strip()
    
    medical_keywords = {
        'symptoms': [
            # Physical symptoms
            'hurt', 'pain', 'ache', 'fever', 'cough', 'headache', 'stomach', 'nausea', 
            'dizzy', 'vomit', 'throw up', 'temperature', 'sore', 'burning', 'itching',
            'rash', 'swelling', 'bleeding', 'infection', 'inflamation', 'cold', 'flu',
            # Mental health symptoms  
            'anxiety', 'depression', 'stress', 'worry', 'nervous', 'panic', 'mood',
            'attention', 'focus', 'concentration', 'adhd', 'add', 'ocd', 'bipolar',
            'sleep', 'insomnia', 'tired', 'fatigue', 'energy',
            # Amharic symptoms
            'የሆድ', 'ራስ', 'ህመም', 'ትኩሳት', 'ሳል', 'መቅማት', 'ማዞር', 'ጉንፋን', 'መጉንፈን',
            'መደንገግ', 'መራመድ', 'ማቃጠል', 'ማቅማት', 'ማድነግ', 'ማድረቅ',
            # Oromo symptoms
            'dhukkuba', 'hooina', 'dhadachiisa', 'dhiifama', 'gammadaa', 'rifachuu'
        ],
        'drugs': [
            'medicine', 'pill', 'tablet', 'drug', 'medication', 'aspirin', 'paracetamol',
            'ibuprofen', 'antibiotic', 'prescription', 'dose', 'treatment', 'መድሀኒት',
            'ፅድት', 'ዶክተር', 'ህክምና', 'dhangalaa', 'dhangalaaa', 'tijaajila'
        ],
        'diagnosis': [
            'diagnose', 'what is', 'what are', 'symptom of', 'cause of', 'why do i',
            'do i have', 'am i sick', 'is this', 'could this be', 'test for', 'signs of',
            'ምንድን', 'ለምን', 'የትኛው', 'እንዴት', 'maali', 'maal', 'maqaa', 'sababaa'
        ],
        'treatment': [
            'treat', 'cure', 'help', 'remedy', 'what should i do', 'how to', 'way to',
            'solution', 'fix', 'relief', 'get better', 'prevent', 'avoid', 'stop',
            'መፍትሔ', 'ማከም', 'አማራጭ', 'መንገድ', 'faayidaa', 'tajaajila', 'naaf', 'maaltu'
        ],
        'current_events': [
            # Disease outbreaks and viruses
            'outbreak', 'epidemic', 'pandemic', 'marburg', 'ebola', 'virus', 'variant',
            'covid', 'corona', 'monkeypox', 'mpox', 'zika', 'dengue', 'cholera',
            # News and updates
            'latest', 'recent', 'breaking', 'news', 'update', 'current', 'today',
            'this week', 'this month', 'new cases', 'spreading', 'spread',
            # Organizations and official sources
            'who', 'cdc', 'health ministry', 'world health',
            # Geographic/regional
            'ethiopia', 'africa', 'region', 'country', 'city',
            # Amharic
            'ወረርሽኝ', 'በሽታ', 'ቫይረስ', 'አዲስ', 'ዜና', 'መረጃ', 'ወቅታዊ',
            # Oromo
            'dhibee', 'oduu', 'haaraa', 'ammaa'
        ]
    }
    
    intent_scores = {category: 0 for category in medical_keywords.keys()}
    
    for category, keywords in medical_keywords.items():
        for keyword in keywords:
            if keyword in text_lower:
                intent_scores[category] += 1
                # Don't break - count all matches for better scoring
    
    logger.info(f"Medical intent scores for '{text}': {intent_scores}")
    return intent_scores

def clean_response(text: str) -> str:
    """Remove unwanted formatting & truncate."""
    if not text:
        return ""
    
    # Remove thinking tags and formatting
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    
    # Clean up and truncate
    text = text.strip()
    if len(text) > MAX_CHARS:
        text = text[:MAX_CHARS] + "..."
    
    return text

def get_fallback_response(language: str) -> str:
    """Get fallback response when AI fails"""
    fallbacks = {
        "am": "❌ ይቅርታ፣ በአሁኑ ሰዓት መልስ ማሰራጨት አልተቻለም። እባክዎ ቆይተው እንደገና ይሞክሩ።",
        "om": "❌ Dhiifama, odeeffannoo kennuu hin dandeenye. Yeroo booda irra deebi'ii yaali.", 
        "en": "❌ Sorry, I couldn't generate a response right now. Please try again in a moment."
    }
    return fallbacks.get(language, fallbacks["en"])

def format_tool_result(name: str, result: dict) -> str:
    """Convert tool output into readable sentences for the user."""
    if "error" in result:
        error_msg = result['error']

        # Check if we should fallback to internet search
        if result.get("use_internet_search") and result.get("search_query"):
            # Automatically perform internet search for unknown symptoms
            search_result = call_tool("internet_search", {"query": result["search_query"]})
            return format_tool_result("internet_search", search_result)

        # Provide helpful context for errors
        if name == "drug_info":
            # Extract possible drug name from error
            if "not found" in error_msg.lower():
                return (
                    "⚠️ I couldn't find that exact drug name in the database.\n\n"
                    "💡 Suggestions:\n"
                    "- Check the spelling (e.g., 'paracetamol' not 'parsnemol')\n"
                    "- Try the generic name instead of brand name\n"
                    "- Common pain relievers: paracetamol, ibuprofen, aspirin\n\n"
                    "If you're unsure about the drug name, describe your symptoms and I can help!"
                )

        return f"⚠️ {error_msg}"

    if name == "drug_info":
        purpose = result.get('purpose', 'N/A')[:200]
        warnings = result.get('warnings', 'N/A')[:300]
        return (
            f"💊 **{result.get('brand_name', result.get('generic_name', 'Drug'))} Information:**\n\n"
            f"**Generic Name:** {result.get('generic_name', 'N/A')}\n"
            f"**Manufacturer:** {result.get('manufacturer_name', 'N/A')}\n\n"
            f"**Purpose:** {purpose}\n\n"
            f"**⚠️ Important Warnings:** {warnings}\n\n"
            f"💡 Always follow dosage instructions and consult a doctor if symptoms persist."
        )
    elif name == "get_current_time":
        return f"⏰ Current time: {result.get('time')}"
    elif name == "internet_search":
        summary = result.get("summary", "No results found.")
        return f"🔍 **Medical Information:**\n\n{summary}\n\n💡 Always consult healthcare professionals for personalized advice."
    elif name == "drug_interactions":
        summary = result.get("summary", "No results found.")
        return f"⚠️ **Drug Interaction Information:**\n\n{summary}\n\n💡 Consult your doctor or pharmacist before combining medications."
    elif name == "get_symptom_advice":
        advice = result.get("advice", {})
        symptom = result.get("symptom", "your symptom")

        # Extract medication from the result (it's stored differently in the tool response)
        medication = None
        if "medication_note" in result:
            # Extract medication name from note
            import re
            match = re.search(r'taking (\w+)', result["medication_note"])
            if match:
                medication = match.group(1)

        response = f"I understand you're experiencing {symptom}. Here's what can help:\n\n"

        # Medication timeline
        if medication and advice.get("medication_timeline"):
            response += f"💊 **About {medication.title()}:**\n"
            response += f"{advice['medication_timeline']}\n\n"

        # Relief tips
        if advice.get("relief_tips"):
            response += "💡 **What to try right now:**\n"
            for tip in advice["relief_tips"]:
                response += f"• {tip}\n"
            response += "\n"

        # Warning signs
        if advice.get("when_to_worry"):
            response += "🚨 **See a doctor immediately if you have:**\n"
            for warning in advice["when_to_worry"]:
                response += f"• {warning}\n"
            response += "\n"

        # Common causes
        if advice.get("common_causes"):
            response += f"Common triggers: {', '.join(advice['common_causes'])}\n\n"

        response += "If your symptoms don't improve in the next few hours or get worse, please see a healthcare professional."
        return response
    else:
        return str(result)

def call_tool(name: str, arguments: dict):
    """Dispatch to available tool functions."""
    logger.info(f"Calling tool: {name} with {arguments}")
    if hasattr(tools, name):
        func = getattr(tools, name)
        return func(**arguments)
    return {"error": f"Tool {name} not found"}



async def generate_direct_response(user_prompt: str, target_language: str = "am") -> str:
    """
    Direct call to Addis API without medical tools
    Used for general conversation and final response generation
    """
    logger.info(f"🎯 Direct API call for: '{user_prompt}' in {target_language}")
    
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": ADDIS_API_KEY,
    }
    
    # Use the exact same format as the working example
    data = {
        'prompt': user_prompt,
        'target_language': target_language
    }
    
    try:
        # SHORTER TIMEOUT to prevent hanging
        async with httpx.AsyncClient() as client:
            response = await client.post(ADDIS_API_URL, headers=headers, json=data, timeout=15.0)
        
            if response.status_code != 200:
                error_msg = f"API Error: {response.status_code}"
                logger.error(error_msg)
                return f"⚠️ {error_msg}"
            
            result = response.json()
            logger.info(f"📦 Raw API response: {result}")
            
            # Use the exact same extraction as working example
            reply = result.get("data", {}).get("response_text", "") or ""
            
            return clean_response(reply)
        
    except httpx.TimeoutException:
        error_msg = "API request timed out (took too long)"
        logger.error(error_msg)
        return "⏰ The response is taking too long. Please try again with a shorter question."
    except httpx.ConnectError:
        error_msg = "Connection lost with API server"
        logger.error(error_msg)
        return "🔌 Connection issue. Please try again in a moment."
    except Exception as e:
        logger.error(f"❌ Direct API call failed: {str(e)}")
        return f"⚠️ Request error: {str(e)}"
    
async def generate_medical_response(user_prompt: str, intent_scores: dict, target_language: str) -> str:
    """
    Generate medical response using tools + AI hybrid approach
    """
    logger.info(f"🩺 Generating medical response for: '{user_prompt}'")
    
    tool_responses = []
    
    # PRIORITY: Current events - search internet FIRST for outbreaks, news, recent developments
    if intent_scores.get('current_events', 0) > 0:
        logger.info("🌍 Detected current events intent - prioritizing internet search")
        import datetime
        current_year = datetime.datetime.now().year
        
        # Optimize search query with year for recent results
        search_query = f"{user_prompt} {current_year}"
        logger.info(f"🔎 Searching for: '{search_query}'")
        
        from app.tools import internet_search
        search_response = await internet_search(search_query)
        if "error" not in search_response:
            formatted_search = format_tool_result("internet_search", search_response)
            tool_responses.append(formatted_search)
            logger.info("✅ Added internet search results for current events")
        else:
            logger.warning(f"⚠️ Internet search failed: {search_response.get('error')}")
    
    # Symptom detection and advice
    if intent_scores['symptoms'] > 0 or intent_scores['diagnosis'] > 0:
        logger.info("🔍 Detected symptom/diagnosis intent - using symptom advice tool")
        symptom_response = call_tool("get_symptom_advice", {"symptom": user_prompt})
        if "error" not in symptom_response:
            formatted_symptom = format_tool_result("get_symptom_advice", symptom_response)
            tool_responses.append(formatted_symptom)
            logger.info("✅ Added symptom advice to response")
    
    # Drug information
    if intent_scores['drugs'] > 0:
        logger.info("💊 Detected drug intent - using drug info tool")
        # Simple drug name extraction (can be improved)
        drug_keywords = ['aspirin', 'paracetamol', 'ibuprofen', 'penicillin', 'antibiotic']
        for drug in drug_keywords:
            if drug in user_prompt.lower():
                drug_response = call_tool("drug_info", {"drug_name": drug})
                if "error" not in drug_response:
                    formatted_drug = format_tool_result("drug_info", drug_response)
                    tool_responses.append(formatted_drug)
                    logger.info(f"✅ Added {drug} info to response")
                break
    
    # Internet search for general medical information
    if intent_scores['diagnosis'] > 0 and not tool_responses:
        logger.info("🔎 No specific tools matched - using internet search")
        from app.tools import internet_search
        search_response = await internet_search(user_prompt)
        if "error" not in search_response:
            formatted_search = format_tool_result("internet_search", search_response)
            tool_responses.append(formatted_search)
            logger.info("✅ Added internet search results to response")
    
    # If we have tool responses, enhance them with AI
    if tool_responses:
        tool_context = "\n\n".join(tool_responses)
        
        # Check if internet search was used (contains "Source:" in results)
        has_internet_sources = "Source:" in tool_context
        
        # Build source citation instruction only if internet search was used
        source_instructions = ""
        if has_internet_sources:
            source_instructions = "\n        7. IMPORTANT: Include ALL source URLs from the Medical Context Information above\n        8. Format sources clearly at the end like: 'Sources: [URL1], [URL2]'"
        
        # Use Addis API to create a natural response incorporating tool data
        enhanced_prompt = f"""
        Medical Context Information:
        {tool_context}
        
        User's Question: {user_prompt}
        
        Please provide a helpful, natural response in {target_language} that:
        1. Uses the medical information above as reference
        2. Is empathetic, helpful and informative
        3. Provides practical advice when appropriate
        4. Suggests professional medical care for serious concerns
        5. Does not refuse to help or provide information
        6. Speaks in a warm, caring tone
        {source_instructions}
        
        Remember: You are a medical assistant providing helpful information, not refusing help.
        """
        
        logger.info("🤖 Enhancing tool responses with AI")
        return await generate_direct_response(enhanced_prompt, target_language)
    else:
        # Fallback to direct AI with medical guidance prompt
        medical_guided_prompt = f"""
        User is asking about medical concerns: {user_prompt}
        
        Please provide helpful medical guidance in {target_language} that:
        - Offers practical, evidence-based information
        - Suggests when to see a doctor for proper diagnosis
        - Provides general health information
        - Is empathetic and does not refuse to help
        - Encourages professional care for serious symptoms
        
        Speak as a helpful medical assistant, not as someone who refuses to provide information.
        """
        
        logger.info("🔄 Using medical-guided AI response (fallback)")
        return await generate_direct_response(medical_guided_prompt, target_language)

async def generate_response(user_prompt: str, user_id: str = None, target_language: str = "am") -> str:
    """
    Main response generator with hybrid medical AI system
    Uses both medical tools and Addis API intelligently
    """
    logger.info(f"🎯 Main response for: '{user_prompt}' in {target_language}")
    
    # Step 1: Detect medical intent
    intent_scores = detect_medical_intent(user_prompt)
    total_medical_score = sum(intent_scores.values())
    
    # Step 2: Route to appropriate system
    if total_medical_score > 0:
        logger.info(f"🩺 Medical intent detected (score: {total_medical_score}) - using hybrid system")
        return await generate_medical_response(user_prompt, intent_scores, target_language)
    else:
        logger.info("💬 General conversation detected - using direct AI")
        return await generate_direct_response(user_prompt, target_language)

async def safe_generate_response(user_prompt: str, user_id: str = None, target_language: str = "am") -> str:
    """
    Safe wrapper around generate_response with caching and fallback handling
    """
    try:
        # 1. Check Cache
        from app.cache_manager import get_cached_response, cache_response
        cached = get_cached_response(user_prompt, target_language)
        if cached:
            logger.info(f"⚡ Cache Hit for: '{user_prompt}'")
            return cached

        # 2. Generate Response
        response = await generate_response(user_prompt, user_id, target_language)

        # Validate response
        if not response or response.strip() == "":
            logger.warning(f"⚠️ Empty response from generate_response for: '{user_prompt}'")
            return get_fallback_response(target_language)

        # 3. Save to Cache (ONLY if it's a valid response, not an error/fallback)
        is_error = response.strip().startswith(("⚠️", "❌", "Error", "API Error"))
        if not is_error:
            cache_response(user_prompt, target_language, response)
        else:
            logger.warning(f"⚠️ Skipping cache for error response: {response[:50]}...")

        return response

    except Exception as e:
        logger.error(f"❌ Error in safe_generate_response: {e}")
        return get_fallback_response(target_language)

# def test_hybrid_system():
#     """Test the hybrid medical AI system"""
#     print("🧪 Testing Hybrid Medical AI System...")
    
#     test_cases = [
#         {"prompt": "I have a headache", "language": "en", "expected": "medical"},
#         {"prompt": "What is aspirin?", "language": "en", "expected": "medical"}, 
#         {"prompt": "How can I treat fever?", "language": "en", "expected": "medical"},
#         {"prompt": "Hello, how are you?", "language": "en", "expected": "general"},
#         {"prompt": "ራስ ምታት አለብኝ", "language": "am", "expected": "medical"},
#         {"prompt": "ሰላም", "language": "am", "expected": "general"},
#         {"prompt": "Dhukkuba mataa qaba", "language": "om", "expected": "medical"},
#     ]
    
#     for test in test_cases:
#         print(f"\n🔍 Testing: '{test['prompt']}' in {test['language']}")
#         try:
#             intent = detect_medical_intent(test["prompt"])
#             total_score = sum(intent.values())
#             detected_type = "medical" if total_score > 0 else "general"
            
#             print(f"   Intent: {intent}")
#             print(f"   Detected: {detected_type} (expected: {test['expected']})")
            
#             response = safe_generate_response(test["prompt"], "test_user", test["language"])
#             print(f"   Response: {response[:100]}...")
            
#         except Exception as e:
#             print(f"   ❌ Error: {e}")

# if __name__ == "__main__":
#     # Set up logging for standalone testing
#     logging.basicConfig(
#         level=logging.INFO,
#         format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
#     )
    
#     print("🚀 Testing Hybrid Medical AI System")
#     print("=" * 50)
    
#     # Run API diagnostics first
#     print("🧪 Running API diagnostics...")
#     api_working = debug_api_connection()
    
#     if not api_working:
#         print("❌ API diagnostics failed! Check your configuration.")
#         print("💡 Make sure your ADDIS_ASSISTANT_API_KEY is set in .env file")
#     else:
#         print("✅ API diagnostics passed!")
    
#     # Run the hybrid system tests
#     test_hybrid_system()