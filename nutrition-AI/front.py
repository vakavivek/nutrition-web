import os

import requests
import streamlit as st

try:
    API_URL = st.secrets["API_URL"]
except Exception:
    API_URL = os.getenv("API_URL", "http://127.0.0.1:8091")
API_URL = API_URL.rstrip("/")

st.set_page_config("Food Nutrition Assistant")
st.title("🍎 Food Nutrition Assistant")
st.caption("Search a food name to see USDA nutrition per 100 g.")

for key, default in {"state_id": None, "result": None, "options": None}.items():
    if key not in st.session_state:
        st.session_state[key] = default

food_query = st.text_input("Food name", placeholder="e.g. chicken biryani, idli, paneer")
if st.button("Search nutrition", disabled=not food_query.strip()):
    st.session_state.state_id = None
    st.session_state.options = None
    st.session_state.result = None
    with st.spinner("Searching USDA foods..."):
        try:
            response = requests.post(f"{API_URL}/search-food", json={"query": food_query}, timeout=120)
            response.raise_for_status()
            data = response.json()
            if data["status"] == "need_confirmation":
                st.session_state.state_id = data["state_id"]
                st.session_state.options = data["options"]
            elif data["status"] == "done":
                st.session_state.result = data
            else:
                st.error(data.get("message", "Unable to find that food."))
        except requests.exceptions.Timeout:
            st.error("The nutrition backend is taking too long. Please try again.")
        except requests.exceptions.RequestException as exc:
            st.error(f"Could not connect to the nutrition backend: {exc}")

if st.session_state.options:
    st.subheader("Which food did you mean?")
    for option in st.session_state.options:
        if st.button(option, key=f"food-option-{option}"):
            try:
                response = requests.post(
                    f"{API_URL}/confirm-food",
                    json={"state_id": st.session_state.state_id, "food": option}, timeout=120,
                )
                response.raise_for_status()
                st.session_state.result = response.json()
                st.session_state.options = None
                st.session_state.state_id = None
                st.rerun()
            except requests.exceptions.RequestException as exc:
                st.error(f"Could not confirm food: {exc}")

if st.session_state.result:
    result = st.session_state.result
    st.success(f"Food: {result['food']}")
    st.subheader("Nutrition")
    for name, value in result["nutrition"].items():
        st.write(f"**{name}**: {value}")
    st.subheader("Explanation & recipe ideas")
    st.write(result["explanation"])
