import requests
import json
import os

def test_overflow():
    url = "http://localhost:8000/generate-pdf"
    
    user_data = {
        "EmailId": "long_text@example.com",
        "name": "User With A Very Very Very Long Name To Test Wrapping",
        "password": "password123",
        "mobileNo": "1234567890",
        "DOB": "1990-01-01",
        "city": "Metropolis Of The Future With A Long Name",
        "state": "California",
        "district": "Los Angeles",
        "country": "USA"
    }
    
    # Very long multiline description
    description = """This is a line with a newline character.\nAnd another one right below it.\n\nThis is a very long paragraph that should definitely wrap across multiple lines in the final PDF document to ensure that the layout remains intact and doesn't overlap with any other sections of the form. We are testing the robustness of the word-wrap logic specifically for the FIRST INFORMATION REPORT narrative section which often contains extended details. If this text is long enough, it should ideally continue gracefully. Let's add more text: Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur."""
    
    complaint_data = {
        "complainant": {"personal_info": {"nature_of_complaint": "Theft Of High Value Digital Assets"}},
        "incident": {
            "place_of_incident": "Cyber Cafe At The Corner Of 5th and Main Street, Near the Old Clock Tower", 
            "type_of_incident": "Digital Theft", 
            "date_of_incident": "2023-01-01", 
            "time_of_incident": "12:00"
        },
        "complaint_submission": {"police_station": "Central Cyber Crime Unit", "district": "Metropolitan District"},
        "complaint_detail": {"complaint_description": description}
    }
    
    with open("userData.json", "w") as f:
        json.dump(user_data, f)
    with open("complaint_data.json", "w") as f:
        json.dump(complaint_data, f)
        
    try:
        print("Testing /generate-pdf for overflow...")
        response = requests.post(url)
        if response.status_code == 200:
            with open("overflow_test.pdf", "wb") as f:
                f.write(response.content)
            print("✅ PDF generated as overflow_test.pdf")
        else:
            print(f"❌ Failed: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_overflow()
