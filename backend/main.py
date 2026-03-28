import os
import json
import subprocess
from datetime import datetime
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import httpx
from pydantic import BaseModel 
from supabase import create_client, Client
from dotenv import load_dotenv
from graph import graph
from pdf_generator import generate_efir_pdf

load_dotenv()

SUPABASE_URL = os.getenv("REACT_APP_SUPABASE_URL") or os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("REACT_APP_SUPABASE_ANON_KEY") or os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    print("⚠️ Supabase credentials missing in .env")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_URL and SUPABASE_KEY else None

SARVAM_API_KEY = os.getenv("SARVAM_API_KEY")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    state: dict | None = None

class LoginRequest(BaseModel):
    email: str
    password: str

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str

FILE_NAME = "complaint_data.json"
USER_DATA_FILE = "userData.json"

@app.get("/")
def home():
    return {"message": "Backend running 🚀"}

@app.post("/voice-to-text")
async def voice_to_text(file: UploadFile = File(...)):
    if not SARVAM_API_KEY:
        print("⚠️ SARVAM_API_KEY missing in .env")
        raise HTTPException(status_code=500, detail="Sarvam API Key not configured")

    try:
        # Read the uploaded file
        content = await file.read()
        
        # Call Sarvam AI REST API
        async with httpx.AsyncClient(timeout=30.0) as client:
            files = {"file": (file.filename or "audio.wav", content, file.content_type or "audio/wav")}
            data = {"model": "saaras:v3"}
            
            headers = {"api-subscription-key": SARVAM_API_KEY}
            
            response = await client.post(
                "https://api.sarvam.ai/speech-to-text",
                headers=headers,
                files=files,
                data=data
            )
            
            if response.status_code != 200:
                print(f"❌ Sarvam AI API Error: {response.status_code} - {response.text}")
                # Fallback check if response has detail
                err_msg = response.json().get("detail", "Voice processing failed") if response.headers.get("content-type") == "application/json" else "Voice processing failed"
                raise HTTPException(status_code=response.status_code, detail=err_msg)
            
            res_data = response.json()
            transcript = res_data.get("transcript", "")
            
            print(f"🎙️ Sarvam AI Transcript: {transcript}")
            return {"transcript": transcript}

    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Voice Processing Failure: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process voice: {str(e)}")

@app.post("/login")
def login(req: LoginRequest):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
    
    try:
        # Use database query instead of Auth
        response = supabase.table("user").select("*").eq("EmailId", req.email).execute()
        
        if not response.data:
            print(f"❌ No user found for {req.email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
            
        user = response.data[0]
        
        # Plain-text password check (assume stored in 'password' column)
        if str(user.get("password")) != req.password:
            print(f"❌ Password mismatch for {req.email}")
            raise HTTPException(status_code=401, detail="Invalid email or password")
            
        # Store all user data (including password for final submission schema)
        user_data = {k: v for k, v in user.items()}
        user_data["last_login"] = datetime.now().isoformat()
        
        with open(USER_DATA_FILE, "w") as f:
            json.dump(user_data, f, indent=4)
            
        print(f"👤 User {req.email} logged in. Saved to {USER_DATA_FILE}")
        
        return {"success": True, "user": user_data}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/submit")
def submit():
    form_data = get_consolidated_data()
    if not form_data:
        raise HTTPException(status_code=400, detail="Missing data: Login and complete FIR first.")

    try:
        with open("formData.json", "w") as ff:
            json.dump(form_data, ff, indent=4)
            
        print(f"📦 Merged data saved to formData.json")

        # --- Automation Step ---
        script_path = os.path.join("automation", "submit_fir.js")
        if os.path.exists(script_path):
            try:
                print(f"🚀 Running automation script: {script_path}")
                # We use shell=True on Windows for 'node' to be found correctly if it's in the PATH
                result = subprocess.run(
                    ["node", script_path],
                    capture_output=True,
                    text=True,
                    check=True,
                    shell=True 
                )
                print(f"✅ Automation success: {result.stdout}")
                return {"success": True, "message": "Data merged and automation completed! ✅"}
            except subprocess.CalledProcessError as e:
                print(f"❌ Automation failed: {e.stderr}")
                return {"success": False, "message": f"Merged, but automation failed: {e.stderr}"}
        else:
            print(f"⚠️ No script found at {script_path}. Returning merge success.")
            return {"success": True, "message": "Data merged as formData.json ✅ (Automation script location: automation/submit_fir.js)"}
    
    except Exception as e:
        print(f"❌ Merging error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/generate-pdf")
def generate_pdf_endpoint():
    form_data = get_consolidated_data()
    if not form_data:
        raise HTTPException(status_code=400, detail="Missing data: FIR partially complete.")
    
    try:
        # Save temporary JSON for the generator
        temp_json = "formData.json"
        pdf_path = "FIR_Report.pdf"
        
        with open(temp_json, "w") as f:
            json.dump(form_data, f, indent=4)
            
        # Call the generator
        generate_efir_pdf(temp_json, pdf_path)
        
        return FileResponse(pdf_path, media_type="application/pdf", filename=pdf_path)
    except Exception as e:
        print(f"❌ PDF generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def get_consolidated_data():
    if not os.path.exists(USER_DATA_FILE) or not os.path.exists(FILE_NAME):
        return None
    
    try:
        with open(USER_DATA_FILE, "r") as uf:
            user = json.load(uf)
        with open(FILE_NAME, "r") as cf:
            complaint = json.load(cf)

        # Splitting names for the target schema
        full_name = user.get("name", "")
        name_parts = full_name.split(" ")
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        # Constructing the final formData.json
        return {
            "credentials": {
                "username": user.get("EmailId", "---"),
                "password": user.get("password") or "12345678"
            },
            "complainantDetail": {
                "personalInformation": {
                    "uid": "---", # Better default
                    "firstName": first_name or "---",
                    "middleName": user.get("middleName", "---"),
                    "lastName": last_name or "---",
                    "natureOfComplaint": complaint.get("complainant", {}).get("personal_info", {}).get("nature_of_complaint", "---"),
                    "emailId": user.get("EmailId", "---"),
                    "mobileCountryCode": "91",
                    "mobileNo": user.get("mobileNo", "---"),
                    "landlineStd": "---",
                    "landlineCode": "---",
                    "landlineNo": "---",
                    "dateOfBirth": user.get("DOB", "---")
                },
                "address": {
                    "houseNo": "---",
                    "streetName": "---",
                    "colony": "---",
                    "village": user.get("city", "---"),
                    "tehsil": "---",
                    "country": user.get("country", "INDIA"),
                    "state": user.get("state", "---"),
                    "district": user.get("district", "---"),
                    "policeStation": complaint.get("complaint_submission", {}).get("police_station", "---"),
                    "pincode": "---"
                },
                "identification": {
                    "countryOfNationality": "INDIA",
                    "records": [
                        { "type": "Aadhaar", "number": "---" }
                    ]
                }
            },
            "accusedDetail": [
                {
                    "name": complaint.get("accused", {}).get("name_of_accused", "Unknown"),
                    "address": complaint.get("accused", {}).get("address_of_accused", "Unknown")
                }
            ],
            "incidentDetail": {
                "placeOfIncident": complaint.get("incident", {}).get("place_of_incident", ""),
                "typeOfIncident": complaint.get("incident", {}).get("type_of_incident", ""),
                "isDateTimeKnown": "yes",
                "incidentDate": complaint.get("incident", {}).get("date_of_incident", ""),
                "incidentTime": complaint.get("incident", {}).get("time_of_incident", "")
            },
            "complaintSubmissionDetails": {
                "knowPoliceStation": complaint.get("knows_police_station", "yes"),
                "district": complaint.get("complaint_submission", {}).get("district") or user.get("district", ""),
                "policeStation": complaint.get("complaint_submission", {}).get("police_station", "")
            },
            "complaintDetail": {
                "dateOfComplaint": datetime.now().strftime("%Y-%m-%d"),
                "description": complaint.get("complaint_detail", {}).get("complaint_description", ""),
                "remarks": ""
            }
        }
    except Exception as e:
        print(f"⚠️ Data consolidation error: {e}")
        return None

@app.post("/register")
def register(req: RegisterRequest):
    if not supabase:
        raise HTTPException(status_code=500, detail="Supabase not configured")
        
    try:
        # Check if user already exists
        check_response = supabase.table("user").select("EmailId").eq("EmailId", req.email).execute()
        if check_response.data:
             raise HTTPException(status_code=400, detail="User already exists")

        # Insert into custom table
        response = supabase.table("user").insert({
            "EmailId": req.email,
            "password": req.password,
            "name": req.name
        }).execute()
        
        print(f"🆕 New user registered: {req.email}")
        return {"success": True, "message": "Registration successful! You can now log in."}
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Registration error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/chat")
def chat(req: ChatRequest):

    # 1. NEW SESSION START: Delete old file
    if req.state is None:
        if os.path.exists(FILE_NAME):
            os.remove(FILE_NAME)
            print(f"🗑️ Deleted old {FILE_NAME}")

        state = {
            "messages": [{"role": "user", "content": req.message}],
            "fir": {},
            "intent": None,
            "errors": [],
            "next_question": None,
            "review": None,
            "last_question": None
        }
    else:
        state = req.state
        state["messages"].append({
            "role": "user",
            "content": req.message
        })

    result = graph.invoke(state)
    
    # 2. UPDATE ON EVERY MESSAGE
    fir_data = result.get("fir", {})
    with open(FILE_NAME, "w") as f:
        json.dump(fir_data, f, indent=4)
        
    print(f"📝 Updated {FILE_NAME}")

    next_question = result.get("next_question")
    is_complete = next_question is None

    return {
        "reply": next_question or "FIR Completed ✅",
        "fir": fir_data,
        "state": result,
        "is_complete": is_complete
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
