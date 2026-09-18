ENERGY MANAGEMENT DIRECTIVE INTERPRETATION SERVICE

PROJECT OVERVIEW

This high-performance, asynchronous FastAPI service parses informal
operator notes into structured JSON directives using OpenAI's LLM capabilities.
It enables energy grid management systems to automatically integrate
human operator instructions into optimization routines.

PROJECT STRUCTURE

Hackathon 2026/
│
├── optimize.py               # Main FastAPI asynchronous server
├── test_optimization.py      # Automated validation test script
├── requirements.txt          # Project dependencies
└── readme.txt                # Documentation and setup guide

PREREQUISITES & INSTALLATION

Python 3.9+ installed on your environment.

Install all required dependencies using pip:

pip install -r requirements.txt

ENVIRONMENT CONFIGURATION (OPTIONAL)

To use real OpenAI LLM parsing, set your API key in the environment:

On Windows (Command Prompt / PowerShell):
set OPENAI_API_KEY=your_actual_openai_api_key

On Bash / Git Bash:
export OPENAI_API_KEY="your_actual_openai_api_key"

Note: If no API key is provided, the service defaults to structured
fallback responses to ensure continuous API availability without crashing.

RUNNING THE SERVER

Start the asynchronous server using Python's Uvicorn module:

python -m uvicorn optimize:app --reload

The server will start running locally at: http://127.0.0.1:8000

TESTING THE ENDPOINTS

Open a secondary terminal window while the server is running and execute:

python test_optimization.py

This test suite verifies:

Service health check endpoint (/health)

Batch operator note parsing endpoint (/api/v1/interpret-notes)

API ENDPOINTS SUMMARY

GET /health

Verifies server status and LLM configuration state.

POST /api/v1/interpret-notes

Input Payload:
{
"scenario_id": "SCENARIO-01",
"operator_notes": [
{
"id": "NOTE-101",
"text": "Maintenance scheduled from 14:00 to 16:00, stop discharging battery."
}
]
}

Output Payload:
Structured directives with decision reasoning and directive parameters.
