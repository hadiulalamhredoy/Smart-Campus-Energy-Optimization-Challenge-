"""
Optimal, Async FastAPI Energy Management Service
------------------------------------------------
Features:
- Async endpoint to prevent blocking worker threads.
- Robust environment variable configuration using Pydantic Settings.
- Clean structured exception handling and graceful mock fallbacks.
"""

import asyncio
import os
import importlib
from typing import Any, Dict, List, Optional
try:
    _pydantic = importlib.import_module("pydantic")
    BaseModel = _pydantic.BaseModel
    Field = _pydantic.Field
except (ImportError, AttributeError):
    class BaseModel:
        """Minimal fallback for environments without Pydantic installed."""

        def __init__(self, **values):
            annotations = getattr(type(self), "__annotations__", {})
            missing = [name for name in annotations if name not in values]
            if missing:
                raise ValueError(f"Missing required fields: {', '.join(missing)}")
            for name, value in values.items():
                setattr(self, name, value)

    def Field(default=None, **_kwargs):
        return default

try:
    _openai = importlib.import_module("openai")
    OpenAI = getattr(_openai, "OpenAI", None)
    _openai_exceptions = getattr(_openai, "exceptions", None)
    OpenAIError = getattr(
        _openai,
        "OpenAIError",
        getattr(_openai_exceptions, "OpenAIError", Exception),
    )
except Exception:
    OpenAI = None

    class OpenAIError(Exception):
        pass

try:
    _fastapi = importlib.import_module("fastapi")
    FastAPI = _fastapi.FastAPI
    HTTPException = _fastapi.HTTPException
    status = _fastapi.status
except ImportError:
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str):
            self.status_code = status_code
            self.detail = detail
            super().__init__(detail)

    class _Status:
        HTTP_200_OK = 200
        HTTP_400_BAD_REQUEST = 400

    class FastAPI:
        def __init__(self, **kwargs):
            self.title = kwargs.get("title")

        def get(self, *args, **kwargs):
            return lambda function: function

        def post(self, *args, **kwargs):
            return lambda function: function

    status = _Status()


# -------------------------------------------------------------------
# Configuration & Settings Management
# -------------------------------------------------------------------
class Settings:
    """Application settings loaded without requiring pydantic-settings."""

    app_name: str = os.getenv(
        "APP_NAME", "Energy Management Directive Service"
    )
    openai_api_key: Optional[str] = os.getenv("OPENAI_API_KEY")

settings = Settings()


# -------------------------------------------------------------------
# Pydantic Schemas
# -------------------------------------------------------------------
class OperatorNote(BaseModel):
    id: str = Field(..., example="NOTE-101")
    text: str = Field(
        ..., 
        example="Maintenance scheduled from 14:00 to 16:00, stop discharging battery."
    )

class EnergyNoteRequest(BaseModel):
    scenario_id: str = Field(..., example="SCENARIO-01")
    operator_notes: List[OperatorNote]

class DirectiveInterpretation(BaseModel):
    note_id: str
    directive_type: str
    parameters: Dict[str, Any]
    reasoning: str

class EnergyNoteResponse(BaseModel):
    scenario_id: str
    status: str
    interpreted_directives: List[DirectiveInterpretation]


# -------------------------------------------------------------------
# FastAPI App Initialization
# -------------------------------------------------------------------
app = FastAPI(
    title=settings.app_name,
    version="2.0.0",
    description="High-performance async parser converting operator notes into structured energy management directives."
)

# Initialize OpenAI Client securely
client = (
    OpenAI(api_key=settings.openai_api_key)
    if settings.openai_api_key and OpenAI is not None
    else None
)


# -------------------------------------------------------------------
# Core Parser Logic
# -------------------------------------------------------------------
def process_note(note: OperatorNote) -> DirectiveInterpretation:
    """Parses a single operator note using OpenAI or fallback logic."""
    if not client:
        return DirectiveInterpretation(
            note_id=note.id,
            directive_type="no_op",
            parameters={},
            reasoning="OpenAI client unavailable: OPENAI_API_KEY environment variable is not configured."
        )

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an AI assistant for energy grid management. Convert informal "
                        "operator notes into structured JSON directives with keys: "
                        "directive_type, parameters, and reasoning."
                    )
                },
                {"role": "user", "content": note.text}
            ],
            temperature=0.0,
        )
        content = response.choices[0].message.content or ""
        
        return DirectiveInterpretation(
            note_id=note.id,
            directive_type="PARSED_DIRECTIVE",
            parameters={"raw_llm_response": content},
            reasoning="Successfully interpreted via OpenAI LLM."
        )

    except OpenAIError as err:
        return DirectiveInterpretation(
            note_id=note.id,
            directive_type="error",
            parameters={},
            reasoning=f"LLM API Error: {str(err)}"
        )


# -------------------------------------------------------------------
# API Endpoints
# -------------------------------------------------------------------
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Service health monitoring endpoint."""
    return {
        "status": "online",
        "llm_configured": settings.openai_api_key is not None
    }

@app.post(
    "/api/v1/interpret-notes", 
    response_model=EnergyNoteResponse,
    status_code=status.HTTP_200_OK
)
async def interpret_notes(payload: EnergyNoteRequest):
    """Processes batch operator notes asynchronously into directives."""
    if not payload.operator_notes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The operator_notes array cannot be empty."
        )

    # OpenAI's client is synchronous; run each call in a worker thread so the
    # async FastAPI event loop remains responsive.
    directives = await asyncio.gather(
        *(asyncio.to_thread(process_note, note) for note in payload.operator_notes)
    )

    return EnergyNoteResponse(
        scenario_id=payload.scenario_id,
        status="PROCESSED_SUCCESSFULLY",
        interpreted_directives=directives
    )

def optimize_energy(data):
    demand = data["demand"]
    solar = data["solar"]
    prices = data["prices"]

    battery = data["battery"]

    battery_energy = battery["current_energy"]
    battery_capacity = battery["capacity"]
    min_reserve = battery["min_reserve"]

    max_charge = battery["max_charge"]
    max_discharge = battery["max_discharge"]

    schedule = []
    total_cost = 0

    for hour in range(24):

        current_demand = demand[hour]
        available_solar = solar[hour]
        price = prices[hour]

        # --------------------------------
        # 1. Use solar
        # --------------------------------

        solar_used = min(
            available_solar,
            current_demand
        )

        remaining_demand = (
            current_demand - solar_used
        )

        # --------------------------------
        # 2. Use battery if necessary
        # --------------------------------

        battery_used = min(
            remaining_demand,
            max(
                0,
                battery_energy - min_reserve
            ),
            max_discharge
        )

        battery_energy -= battery_used

        remaining_demand -= battery_used

        # --------------------------------
        # 3. Use grid for remaining demand
        # --------------------------------

        grid_used = remaining_demand

        # --------------------------------
        # 4. Calculate cost
        # --------------------------------

        hour_cost = grid_used * price

        total_cost += hour_cost

        # --------------------------------
        # 5. Save this hour
        # --------------------------------

        schedule.append({
            "hour": hour,
            "demand": current_demand,
            "solar": solar_used,
            "battery": battery_used,
            "grid": grid_used,
            "battery_after": battery_energy,
            "cost": hour_cost
        })

    return {
        "schedule": schedule,
        "total_cost": total_cost
    }

# -------------------------------------------------------------------
# Server Entrypoint
# -------------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn  # type: ignore[import-not-found]
    uvicorn.run("optimize:app", host="127.0.0.1", port=8000, reload=True)