"""FastAPI service for text-only USDA food search and nutrition analysis."""

import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from pipeline import confirm_food_choice, search_food_query

app = FastAPI(title="Nutrition AI API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Sufficient for a single Render free instance; choices expire on service restart.
STATE_STORE: dict[str, list[dict]] = {}


class FoodSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=200)


class FoodConfirmationRequest(BaseModel):
    state_id: str
    food: str


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "nutrition-ai-api", "mode": "text-only"}


@app.post("/search-food")
def search_food(payload: FoodSearchRequest) -> dict:
    result = search_food_query(payload.query)
    if result["status"] == "need_confirmation":
        state_id = str(uuid.uuid4())
        STATE_STORE[state_id] = result.pop("candidates")
        result["state_id"] = state_id
    return result


@app.post("/confirm-food")
def confirm_food(payload: FoodConfirmationRequest) -> dict:
    candidates = STATE_STORE.pop(payload.state_id, None)
    if candidates is None:
        raise HTTPException(status_code=404, detail="That food selection has expired. Search again and choose an option.")
    result = confirm_food_choice(candidates, payload.food)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result["message"])
    return result
