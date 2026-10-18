"""Text-only food search and nutrition analysis pipeline."""

from llm.mistral import explain_nutrition_with_recipes
from retrieval.faiss_search import search_food_by_text
from usda.fetch_nutrition_excel import fetch_usda_nutrition_from_excel


def _result_for_food(food: dict) -> dict:
    nutrition = fetch_usda_nutrition_from_excel(food["Food code"])
    if nutrition is None:
        return {"status": "error", "message": "Nutrition data was not found for this food."}
    return {
        "status": "done", "food": food["Main food description"], "nutrition": nutrition,
        "explanation": explain_nutrition_with_recipes(food=food, nutrition=nutrition),
    }


def search_food_query(query: str, top_k: int = 5) -> dict:
    """Search USDA food descriptions without loading a vision or embedding model."""
    candidates = search_food_by_text(query, top_k=top_k)
    if not candidates:
        return {"status": "error", "message": "No matching foods were found. Try a simpler food name."}
    exact_match = next((item for item in candidates if item["exact_match"]), None)
    if exact_match:
        return _result_for_food(exact_match)
    return {
        "status": "need_confirmation",
        "options": [item["Main food description"] for item in candidates],
        "candidates": candidates,
    }


def confirm_food_choice(candidates: list[dict], chosen_food: str) -> dict:
    selected = next((item for item in candidates if item["Main food description"] == chosen_food), None)
    if selected is None:
        return {"status": "error", "message": "Choose one of the displayed food options."}
    return _result_for_food(selected)
