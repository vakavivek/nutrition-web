"""Optional Mistral explanation support with a local fallback."""

import os
from functools import lru_cache

from dotenv import load_dotenv

load_dotenv()


@lru_cache(maxsize=1)
def get_llm():
    """Create the Mistral client only when an explanation is requested."""
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        return None
    try:
        from langchain_mistralai.chat_models import ChatMistralAI
        return ChatMistralAI(api_key=api_key, temperature=0.3, max_retries=1, timeout=30)
    except Exception as exc:
        print(f"Mistral client unavailable ({type(exc).__name__}); using a local summary.")
        return None


def explain_nutrition_with_recipes(food: dict, nutrition: dict) -> str:
    """Use Mistral to explain nutrition and suggest recipe ideas when available."""
    prompt = f"""
You are a nutrition assistant.

Food: {food.get('Main food description', food)}
Nutrition per 100 g:
calories: {nutrition.get('calories')}
Protein: {nutrition.get('Protein')}
carbohydrates: {nutrition.get('Carbohydrates')}
Fat: {nutrition.get('Fats')}

Tasks:
1. Explain this nutrition in simple, non-medical language.
2. Suggest 2 healthy recipe or preparation ideas.
3. Do not calculate or modify nutrition numbers.
4. Keep it concise (4-6 lines).
"""
    llm = get_llm()
    if llm is not None:
        try:
            return llm.invoke(prompt).content
        except Exception as exc:
            print(f"Mistral explanation unavailable ({type(exc).__name__}); using a local summary.")

    food_name = food.get("Main food description", "This food")
    return (
        f"Per 100 g, {food_name} provides {nutrition.get('calories', 'N/A')} kcal, "
        f"{nutrition.get('Protein', 'N/A')} g protein, "
        f"{nutrition.get('Carbohydrates', 'N/A')} g carbohydrates, and "
        f"{nutrition.get('Fats', 'N/A')} g fat. "
        "For a meal idea, serve it with vegetables and whole grains, or add it to a balanced bowl or wrap."
    )
