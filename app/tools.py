import datetime
import requests
import httpx
from bs4 import BeautifulSoup
from langchain_community.utilities import SearxSearchWrapper
from typing import Optional
# -------------------------------
# 1. Initialize SearxNG for web searches
# -------------------------------
search = SearxSearchWrapper(searx_host="http://searxng:8080")  # Updated for Docker internal network
OPENFDA_BASE = "https://api.fda.gov"

# -------------------------------
# Symptom and medication advice database
# -------------------------------
SYMPTOM_ADVICE = {
    "headache": {
        "common_causes": ["tension", "dehydration", "eye strain", "lack of sleep", "stress"],
        "relief_tips": [
            "Rest in a quiet, dark room",
            "Stay hydrated - drink plenty of water",
            "Apply a cold or warm compress to your head or neck",
            "Gently massage your temples and neck",
            "Ensure you're not hungry - low blood sugar can cause headaches"
        ],
        "when_to_worry": [
            "Sudden severe headache (worst headache of your life)",
            "Headache with fever, stiff neck, confusion, or vision changes",
            "Headache after head injury",
            "Headache that worsens over days despite medication",
            "New headache pattern in people over 50"
        ],
        "medication_timeline": "Paracetamol/ibuprofen usually works within 30-60 minutes. If no relief after 4 hours, may need reassessment."
    },
    "fever": {
        "relief_tips": [
            "Rest and stay hydrated",
            "Take paracetamol or ibuprofen as directed",
            "Dress in light clothing",
            "Keep room temperature comfortable"
        ],
        "when_to_worry": [
            "Fever above 39.4°C (103°F)",
            "Fever lasting more than 3 days",
            "Severe headache, stiff neck, or confusion",
            "Difficulty breathing or chest pain"
        ],
        "medication_timeline": "Fever reducers (paracetamol, ibuprofen) work in 30-60 minutes. Temperature should start dropping within 1 hour."
    },
    "stomach": {
        "common_causes": ["indigestion", "food poisoning", "stress", "overeating", "infection"],
        "relief_tips": [
            "Avoid solid food for a few hours if nauseous",
            "Sip water or clear fluids slowly",
            "Try ginger tea or peppermint tea",
            "Avoid spicy, fatty, or acidic foods",
            "Rest in a comfortable position"
        ],
        "when_to_worry": [
            "Severe abdominal pain lasting more than 2 hours",
            "Blood in vomit or stool",
            "Signs of dehydration (very dark urine, dizziness)",
            "Fever with stomach pain",
            "Unable to keep any fluids down for 24 hours"
        ],
        "medication_timeline": "Antacids work within 5-10 minutes. Other stomach medicines may take 30-60 minutes."
    },
    "nausea": {
        "relief_tips": [
            "Sip clear fluids slowly (water, ginger ale)",
            "Eat bland foods like crackers or toast",
            "Avoid strong smells",
            "Get fresh air",
            "Try ginger or peppermint"
        ],
        "when_to_worry": [
            "Persistent vomiting for more than 24 hours",
            "Signs of dehydration",
            "Severe abdominal pain",
            "Blood in vomit"
        ]
    },
    "cough": {
        "common_causes": ["cold", "flu", "allergies", "throat irritation"],
        "relief_tips": [
            "Stay hydrated - drink warm liquids",
            "Use honey (for adults and children over 1 year)",
            "Breathe in steam from a hot shower",
            "Use a humidifier",
            "Avoid smoking and irritants"
        ],
        "when_to_worry": [
            "Cough lasting more than 3 weeks",
            "Coughing up blood",
            "Difficulty breathing or wheezing",
            "High fever with cough",
            "Chest pain"
        ],
        "medication_timeline": "Cough suppressants work within 30 minutes. Full effect in 1-2 hours."
    },
    "cold": {
        "relief_tips": [
            "Rest and sleep well",
            "Drink plenty of fluids",
            "Gargle with warm salt water for sore throat",
            "Use saline nasal drops",
            "Take paracetamol for aches and fever"
        ],
        "when_to_worry": [
            "Symptoms lasting more than 10 days",
            "High fever (above 38.5°C) for more than 3 days",
            "Difficulty breathing",
            "Severe headache or sinus pain"
        ]
    },
    "pain": {
        "medication_timeline": "Most pain relievers (paracetamol, ibuprofen) take 30-60 minutes to work. Peak effect at 1-2 hours."
    },
    "dizzy": {
        "relief_tips": [
            "Sit or lie down immediately",
            "Drink water - dehydration can cause dizziness",
            "Avoid sudden movements",
            "Get fresh air",
            "Avoid bright lights"
        ],
        "when_to_worry": [
            "Severe dizziness with chest pain",
            "Fainting or loss of consciousness",
            "Dizziness with severe headache",
            "Numbness or weakness",
            "Dizziness persisting for several days"
        ]
    }
}

def get_symptom_advice(symptom: str, medication_taken: str = None) -> dict:
    """
    Provide medical advice for common symptoms and medication effectiveness.
    """
    symptom_lower = symptom.lower().strip()

    # Find matching symptom (try exact match first, then partial)
    advice = None
    matched_symptom = None

    # Exact match
    if symptom_lower in SYMPTOM_ADVICE:
        advice = SYMPTOM_ADVICE[symptom_lower]
        matched_symptom = symptom_lower
    else:
        # Partial match - check if any key is in symptom or vice versa
        for key in SYMPTOM_ADVICE:
            if key in symptom_lower or symptom_lower in key:
                advice = SYMPTOM_ADVICE[key]
                matched_symptom = key
                break

    # Also check common aliases (including Oromo translations)
    symptom_aliases = {
        # English aliases
        "stomach ache": "stomach",
        "stomachache": "stomach",
        "belly": "stomach",
        "tummy": "stomach",
        "head": "headache",
        "migraine": "headache",
        "temperature": "fever",
        "vomit": "nausea",
        "throw up": "nausea",
        "dizziness": "dizzy",
        "vertigo": "dizzy",
        # Oromo translations
        "garaa": "stomach",        # stomach in Oromo
        "dhukkuba garaa": "stomach",  # stomach pain
        "mataa": "headache",       # head/headache in Oromo
        "dhukkuba mataa": "headache",  # headache
        "ho'ina": "fever",         # fever in Oromo
        "qufa'aa": "nausea",       # nausea in Oromo
        "qufaa": "cough",          # cough in Oromo
        "zukaa": "cold",           # cold/flu in Oromo
        "ciniinsa": "pain",        # pain in Oromo
    }

    if not advice:
        for alias, canonical in symptom_aliases.items():
            if alias in symptom_lower:
                advice = SYMPTOM_ADVICE.get(canonical)
                matched_symptom = canonical
                break

    if not advice:
        # Fallback: use internet search for unknown symptoms
        return {
            "error": f"I don't have specific guidance for '{symptom}' in my database. Let me search the internet for information.",
            "use_internet_search": True,
            "search_query": f"{symptom} symptoms treatment medical advice"
        }

    response = {
        "symptom": matched_symptom or symptom,
        "advice": advice
    }

    if medication_taken:
        response["medication_note"] = (
            f"You mentioned taking {medication_taken}. "
            f"{advice.get('medication_timeline', 'Most medications take 30-60 minutes to work.')}"
        )

    return response

# -------------------------------
# 2. Web search / knowledge lookup
# -------------------------------
async def internet_search(query: str, num_results: int = 3, searx_host: Optional[str] = None):
    """
    Query the SearXNG search API, fetch actual page content, and return detailed summaries.
    Now extracts real content from pages for more specific information.
    """
    if searx_host is None:
        searx_host = "http://searxng:8080"  # or read from env like os.getenv("SEARX_HOST")

    # Build URL. Use `/search` endpoint and request JSON format.
    params = {
        "q": query,
        "format": "json",
        "pageno": 1,
        "language": "en",  # optional
    }
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                f"{searx_host}/search",
                params=params,
                headers={
                    "X-Forwarded-For": "127.0.0.1",
                    "X-Real-IP": "127.0.0.1",
                    "User-Agent": "medical-bot/1.0"
                }
            )

            resp.raise_for_status()
            data = resp.json()

            # Extract top results from JSON (structure depends on SearXNG)
            results = data.get("results", [])
            top = results[:num_results]

            if not top:
                return {"query": query, "summary": "No results found."}

            # Enhanced: Extract actual content from each page
            detailed_results = []
            for r in top:
                title = r.get("title") or ""
                url = r.get("url") or ""
                content_snippet = r.get("content", "")  # SearXNG provides snippets
                
                # Try to fetch more content from the actual page
                page_content = ""
                try:
                    page_resp = await client.get(url, timeout=5.0, headers={"User-Agent": "medical-bot/1.0"})
                    if page_resp.status_code == 200:
                        soup = BeautifulSoup(page_resp.content, 'html.parser')
                        
                        # Extract main text content (remove scripts, styles)
                        for script in soup(["script", "style", "nav", "footer", "header"]):
                            script.decompose()
                        
                        # Get text from paragraphs
                        paragraphs = soup.find_all('p')
                        text_content = ' '.join([p.get_text().strip() for p in paragraphs[:5]])  # First 5 paragraphs
                        
                        if text_content:
                            page_content = text_content[:500]  # Limit to 500 chars per page
                except Exception as e:
                    # If page fetch fails, use the snippet from search results
                    page_content = content_snippet[:300] if content_snippet else ""
                
                # Combine title, URL, and extracted content
                result_text = f"**{title}**\nSource: {url}\n"
                if page_content:
                    result_text += f"Details: {page_content}...\n"
                elif content_snippet:
                    result_text += f"Summary: {content_snippet}...\n"
                
                detailed_results.append(result_text)

        summary = "\n\n".join(detailed_results)
        return {"query": query, "summary": summary}

    except Exception as e:
        return {"query": query, "error": str(e)}


# -------------------------------
# 3. Current time
# -------------------------------
def get_current_time():
    return {"time": datetime.datetime.now().isoformat()}


# -------------------------------
# 4. Drug info via OpenFDA
# -------------------------------
def drug_info(drug_name: str):
    """
    Fetch detailed drug information from OpenFDA (brand or generic).
    """
    try:
        # Try both brand and generic
        url = f"{OPENFDA_BASE}/drug/label.json?search=openfda.brand_name:{drug_name}+openfda.generic_name:{drug_name}&limit=1"
        response = requests.get(url, timeout=10)

        if response.status_code == 404:
            return {"error": f"Drug '{drug_name}' not found in OpenFDA database. Please check the spelling or try the generic name (e.g., 'paracetamol' instead of 'parsnemol')."}

        response.raise_for_status()
        data = response.json()
        if "results" in data and data["results"]:
            result = data["results"][0]
            openfda = result.get("openfda", {})
            return {
                "brand_name": ", ".join(openfda.get("brand_name", [])),
                "generic_name": ", ".join(openfda.get("generic_name", [])),
                "manufacturer_name": ", ".join(openfda.get("manufacturer_name", [])),
                "purpose": " ".join(result.get("purpose", ["No purpose info available."])),
                "indications_and_usage": " ".join(result.get("indications_and_usage", ["No indications info available."])),
                "warnings": " ".join(result.get("warnings", ["No warnings available."]))
            }
        else:
            return {"error": f"No data found for '{drug_name}' in OpenFDA. Please check the spelling."}
    except requests.exceptions.RequestException as e:
        return {"error": f"Unable to fetch drug information: {str(e)}"}
    except Exception as e:
        return {"error": f"Error processing drug information: {str(e)}"}

def drug_interactions(drug_name: str, other_drug: str = None):
    """
    Check possible drug interactions using SearxNG.
    """
    try:
        if other_drug:
            query = f"{drug_name} {other_drug} drug interaction site:drugs.com OR site:medlineplus.gov OR site:webmd.com"
        else:
            query = f"{drug_name} drug interactions site:drugs.com OR site:medlineplus.gov OR site:webmd.com"

        results = search.search(query)
        top_results = results[:3]
        summary = "\n".join([f"{r['title']} ({r['url']})" for r in top_results])
        if not summary:
            return {"query": query, "summary": "No interaction info found."}
        return {"query": query, "summary": summary}
    except Exception as e:
        return {"error": str(e)}

