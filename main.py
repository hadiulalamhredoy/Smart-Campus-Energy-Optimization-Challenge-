import os
import json
import importlib
import uvicorn
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Dict, Any

app = FastAPI(
    title="BUP Smart Campus Energy API with LLM",
    version="1.0.0"
)


try:
    OpenAI = importlib.import_module("openai").OpenAI
except (ImportError, AttributeError):
    OpenAI = None

client = (
    OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    if OpenAI and os.getenv("OPENAI_API_KEY")
    else None
)

# ==========================================
# 1. DATA MODELS & SCHEMAS
# ==========================================

class OperatorNote(BaseModel):
    id: str = Field(..., example="NOTE-01")
    text: str = Field(..., example="Maintenance scheduled from 14:00 to 16:00, stop discharging battery.")

class DirectiveInterpretation(BaseModel):
    note_id: str
    directive_type: str
    parameters: Dict[str, Any]
    reasoning: str

class OptimizationRequest(BaseModel):
    scenario_id: str
    operator_notes: List[OperatorNote] = Field(default_factory=list)

class OptimizationResponse(BaseModel):
    scenario_id: str
    status: str
    interpreted_directives: List[DirectiveInterpretation]

# ==========================================
# 2. SYSTEM PROMPT & LLM INTERPRETER FUNCTION
# ==========================================

SYSTEM_PROMPT = """
You are an expert energy management LLM agent for the BUP Smart Campus system.
Parse operator notes into actionable energy directives:
1. 'BATTERY_DISCHARGE_RESTRICTION': {"start_hour": int, "end_hour": int, "max_discharge_kw": float}
2. 'GRID_IMPORT_LIMIT': {"start_hour": int, "end_hour": int, "max_grid_kw": float}
3. 'no_op': For conversational/irrelevant notes.
Output ONLY JSON matching this format.
"""

def interpret_note_with_llm(note: OperatorNote) -> DirectiveInterpretation:
    try:
        if client is None:
            return DirectiveInterpretation(
                note_id=note.id,
                directive_type="no_op",
                parameters={},
                reasoning="OpenAI client is unavailable or OPENAI_API_KEY is not set"
            )
        response = client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Note ID: {note.id}\nNote: \"{note.text}\""}
            ],
            temperature=0.0
        )
        content = response.choices[0].message.content
        if not content:
            raise ValueError("The LLM returned an empty response")
        result_json = json.loads(content)
        if not isinstance(result_json, dict):
            raise ValueError("The LLM response must be a JSON object")
        return DirectiveInterpretation(
            note_id=note.id,
            directive_type=result_json.get("directive_type", "no_op"),
            parameters=result_json.get("parameters", {}),
            reasoning=result_json.get("reasoning", "Processed via OpenAI LLM")
        )
    except (json.JSONDecodeError, ValueError, RuntimeError, Exception) as e:
        return DirectiveInterpretation(
            note_id=note.id,
            directive_type="no_op",
            parameters={},
            reasoning=f"LLM Error: {str(e)}"
        )




# ==========================================
# 3. API ENDPOINTS
# ==========================================

@app.get("/health")
async def health():
    return {"status": "healthy"}







@app.post("/api/v1/interpret-notes", response_model=OptimizationResponse)
async def process_notes(request: OptimizationRequest):
    directives = [interpret_note_with_llm(note) for note in request.operator_notes]
    return OptimizationResponse(
        scenario_id=request.scenario_id,
        status="PROCESSED_SUCCESSFULLY",
        interpreted_directives=directives
    )

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)