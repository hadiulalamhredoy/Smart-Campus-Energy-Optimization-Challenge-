import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


URL = "http://127.0.0.1:8000/api/v1/interpret-notes"


payload = {
    "scenario_id": "SCENARIO-01",
    "operator_notes": [
        {
            "id": "NOTE-101",
            "text": "Maintenance scheduled from 14:00 to 16:00, stop discharging battery."
        },
        {
            "id": "NOTE-102",
            "text": "Good morning team, keep working safely!"
        }
    ]
}

def test_interpret_notes():
    headers = {"Content-Type": "application/json"}
    
    try:
        # API-তে POST Request পাঠানো
        request = Request(
            URL,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST",
        )
        with urlopen(request, timeout=10) as response:
            status_code = response.status
            response_body = response.read().decode("utf-8")
        
        print("Status Code:", status_code)
        
        if status_code == 200:
            print("\n--- API Response Success ---")
            print(json.dumps(json.loads(response_body), indent=2))
        else:
            print("\n--- Error Response ---")
            print(response_body)
            
    except HTTPError as error:
        error_body = error.read().decode("utf-8", errors="replace")
        print(f"\nAPI Error ({error.code}): {error_body}")
    except URLError as error:
        print(f"\nError: FastAPI server is unavailable: {error.reason}")

if __name__ == "__main__":
    test_interpret_notes()

    
