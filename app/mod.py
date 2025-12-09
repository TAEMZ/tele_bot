
import os
from dotenv import load_dotenv
import json, re, logging, requests
import app.tools as tools
from app.memory import get_relevant_context

ADDIS_API_URL = "https://api.addisassistant.com/api/v1/chat_generate"
load_dotenv()
ADDIS_API_KEY = os.environ.get("ADDIS_ASSISTANT_API_KEY", "sk_ffee3fb8-108c-46fc-8a06-8db8b26a035b_3d005604e58bc8bb7ec35bd5313ef5b5f5c117fb020d0e20de39217418c59947")
MAX_CHARS = 4000

def clean_response(text: str) -> str:
    """Remove unwanted formatting & truncate."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"\*(.*?)\*", r"\1", text)
    text = re.sub(r"\n\s*\n", "\n\n", text)
    return text.strip()[:MAX_CHARS]

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
    logger = logging.getLogger(__name__)
    logger.info(f"Calling tool: {name} with {arguments}")
    if hasattr(tools, name):
        func = getattr(tools, name)
        return func(**arguments)
    return {"error": f"Tool {name} not found"}

def generate_response(user_prompt: str, user_id: str = None, target_language: str = "am") -> str:
    """
    Generate a response to user prompt using Addis Assistant API.
    Args:
        user_prompt: The user's message
        user_id: Telegram user ID (optional)
        target_language: Language code (default 'am') - NOW SUPPORTS 'om' TOO
    Returns:
        str: The assistant's reply
    """
    logger = logging.getLogger(__name__)

    # Build conversation history if available
    conversation_history = []
    # If you want to use memory, you can fetch context here
    # if user_id:
    #     context = get_relevant_context(user_id, user_prompt, limit=5)
    #     for line in context.splitlines():
    #         if line.startswith("User:"):
    #             conversation_history.append({"role": "user", "content": line[5:].strip()})
    #         elif line.startswith("Assistant:"):
    #             conversation_history.append({"role": "assistant", "content": line[10:].strip()})

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": ADDIS_API_KEY,
    }
    data = {
        "prompt": user_prompt,
        "target_language": target_language,  # This now supports 'am' or 'om'
        "generation_config": {
            "temperature": 0.7
        }
    }
    if conversation_history:
        data["conversation_history"] = conversation_history

    try:
        response = requests.post(ADDIS_API_URL, headers=headers, json=data, timeout=30)
        print(f"API Call - Language: {target_language}, Status: {response.status_code}")
        if response.status_code != 200:
            error_data = response.json()
            error_message = error_data.get("error", {}).get("message", "Unknown error")
            logger.error(f"Addis Assistant API error: {error_message}")
            return f"⚠️ Sorry, Addis Assistant API error: {error_message}"
        result = response.json()
        # The response text may be under 'response_text' or 'text'
        reply = result.get("data", {}).get("response_text", "") or ""
        return clean_response(reply)
    except Exception as e:
        logger.error(f"Addis Assistant API request failed: {str(e)}")
        return f"⚠️ Sorry, Addis Assistant API request failed: {str(e)}"
       
