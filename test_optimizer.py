"""
API Validation Client for Async Energy Optimization Service (test_optimization.py)
----------------------------------------------------------------------------------
Run this script while 'optimize.py' is running on http://127.0.0.1:8000
"""

import sys
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE_URL = "http://127.0.0.1:8000"


def test_health_endpoint():
    """Validates the health check endpoint."""
    print("\n[1/2] Testing Health Endpoint (/health)...")
    try:
        with urlopen(f"{BASE_URL}/health", timeout=5) as response:
            status_code = response.status
            payload = json.loads(response.read().decode("utf-8"))
        print(f"Status Code: {status_code}")
        print("Response Payload:")
        print(json.dumps(payload, indent=2))
        return status_code == 200
    except (URLError, OSError):
        print("Error: Could not connect to FastAPI server.")
        print("Ensure 'python -m uvicorn optimize:app --reload' is running in another terminal.")
        return False


def test_interpret_notes_endpoint():
    """Validates the batch note parsing endpoint."""
    print("\n[2/2] Testing Interpret Notes Endpoint (/api/v1/interpret-notes)...")
    
    payload = {
        "scenario_id": "SCENARIO-01",
        "operator_notes": [
            {
                "id": "NOTE-101",
                "text": "Maintenance scheduled from 14:00 to 16:00, stop discharging battery."
            },
            {
                "id": "NOTE-102",
                "text": "High solar generation expected at 12:00, maximize battery charge rate."
            }
        ]
    }

    try:
        request = Request(
            f"{BASE_URL}/api/v1/interpret-notes",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=10) as response:
            status_code = response.status
            response_payload = json.loads(response.read().decode("utf-8"))
        print(f"Status Code: {status_code}")
        print("Response Payload:")
        print(json.dumps(response_payload, indent=2))
        return status_code == 200
    except (HTTPError, URLError, OSError, ValueError) as err:
        print(f"Request failed: {err}")
        return False


if __name__ == "__main__":
    print("=" * 60)
    print("STARTING API SUITE FOR OPTIMIZE.PY")
    print("=" * 60)
    
    health_ok = test_health_endpoint()
    if health_ok:
        test_interpret_notes_endpoint()
    else:
        sys.exit(1)