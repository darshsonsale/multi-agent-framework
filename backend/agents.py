import json
from openai import OpenAI
from dotenv import load_dotenv
from fir_schema import FIR_SCHEMA
 
load_dotenv()
client = OpenAI()

# -----------------------------
# INTENT
# -----------------------------
def intent_agent(message):
    res = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Classify: Theft / Cybercrime / Harassment / other\nMessage: {message}"
        }]
    )
    return res.choices[0].message.content.strip()


# -----------------------------
# EXTRACTOR (🔥 CONTEXT-AWARE)
# -----------------------------
def extractor_agent(message, last_field=None):

    # If answering a question → map directly
    if last_field:
        keys = last_field.split(".")
        data = current = {}

        for k in keys[:-1]:
            current[k] = {}
            current = current[k]

        current[keys[-1]] = message.strip()
        return data

    # 🔥 UPDATED PROMPT (MATCH NEW SCHEMA)
    prompt = f"""
Extract structured FIR data from user message.

STRICT RULES:
- Follow this exact schema:

complainant.personal_info.nature_of_complaint
accused.name_of_accused
accused.address_of_accused
incident.place_of_incident
incident.type_of_incident
incident.date_of_incident
incident.time_of_incident
complaint_submission.knows_police_station
complaint_submission.police_station
complaint_detail.complaint_description

- Extract ONLY what is clearly mentioned
- Do NOT guess anything
- Return ONLY JSON
- Do NOT create extra fields

Message:
{message}
"""

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            response_format={"type": "json_object"},
            messages=[{"role": "user", "content": prompt}]
        )

        return json.loads(res.choices[0].message.content)

    except:
        return {}


# -----------------------------
# MERGE
# -----------------------------
def merge_json(old, new):
    for k, v in new.items():
        if isinstance(v, dict):
            old[k] = merge_json(old.get(k, {}), v)
        elif isinstance(v, list):
            old[k] = v
        elif v is not None:
            old[k] = v
    return old


# -----------------------------
# FIND MISSING
# -----------------------------
def find_missing(data, schema, path=""):
    missing = []

    for k, v in schema.items():
        current_path = f"{path}.{k}" if path else k

        # Get current value safely
        value = data.get(k, None)

        # CASE 1: Nested object
        if isinstance(v, dict) and "required" not in v:
            if not isinstance(value, dict):
                value = {}  # if missing, treat as empty dict

            missing += find_missing(value, v, current_path)

        # CASE 2: Field
        else:
            if v.get("required"):
                if value is None or value == "":
                    missing.append(current_path)

    return missing


# -----------------------------
# QUESTION GENERATOR
# -----------------------------
def generate_question(field_path):

    mapping = {
        "nature_of_complaint": "What happened? Please describe your complaint.",
        "place_of_incident": "Where did the incident happen?",
        "type_of_incident": "What type of incident was it?",
        "date_of_incident": "When did the incident happen (date)?",
        "time_of_incident": "What time did the incident happen?",
        "knows_police_station": "Do you know the police station? (yes/no)",
        "police_station": "Which police station?",
        "complaint_description": "Please describe the incident in detail.",
        "name_of_accused": "Do you know the accused person's name?",
        "address_of_accused": "Do you know the accused person's address?"
    }

    key = field_path.split(".")[-1]

    return mapping.get(key, f"Enter {key.replace('_', ' ')}")


# -----------------------------
# DIALOGUE (🔥 RETURNS FIELD)
# -----------------------------
def dialogue_agent(fir):

    missing = find_missing(fir, FIR_SCHEMA)

    if not missing:
        return None, None

    field = missing[0]
    question = generate_question(field)

    return question, field


# -----------------------------
# VALIDATION
# -----------------------------
def validation_agent(fir):
    return []


# -----------------------------
# REVIEW
# -----------------------------
def review_agent(fir, intent):
    return {
        "status": "READY",
        "intent": intent,
        "fir": fir
    }


# -----------------------------
# DESCRIPTION AGENT (Automated FIR Narration)
# -----------------------------
def description_agent(fir_data):
    # Skip if almost no data
    if not fir_data:
        return fir_data

    prompt = f"""
    Based on the following structured data, write a purely factual paragraph describing the incident:
    {json.dumps(fir_data, indent=2)}

    STRICT RULES:
    1. Focus ONLY on the information provided (incident details, place, time, accused).
    2. Do NOT use any formal salutations or honorifics like "Sir", "Respected", "Police Officer", etc.
    3. Do NOT use any introductory phrases like "To the Officer in Charge".
    4. Start the paragraph directly with the facts of the incident.
    5. Ensure the description is detailed and professional but remains purely factual.
    6. Return ONLY the drafted paragraph text.
    """

    try:
        res = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        description = res.choices[0].message.content.strip()
        
        # Update the FIR data
        if "complaint_detail" not in fir_data:
            fir_data["complaint_detail"] = {}
        fir_data["complaint_detail"]["complaint_description"] = description
        
        return fir_data
    except Exception as e:
        print(f"⚠️ Description Agent error: {e}")
        return fir_data
