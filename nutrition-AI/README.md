# Food Nutrition Assistant

A text-only food nutrition app with a Streamlit frontend and FastAPI backend.
Users enter a food name, choose from USDA food-description matches when needed,
then receive nutrition per 100 g and a Mistral-generated explanation.

## What runs in production

- Lightweight normalized text search over the included USDA metadata (5,431 foods)
- USDA Excel nutrition lookup
- Mistral explanation with a local fallback if the API is unavailable
- FastAPI and Streamlit

CLIP, PyTorch, Transformers, image upload, and image inference are not part of
the production runtime or backend dependency list. The historical FAISS and
embedding files remain in `data/` for offline experiments only; the deployed
application does not load them.

## Local setup

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pip install -r requirements-front.txt
export MISTRAL_API_KEY="your-key"
uvicorn api:app --reload --port 8091
```

In another terminal:

```bash
source .venv/bin/activate
export API_URL="http://127.0.0.1:8091"
streamlit run front.py
```

Try `chicken biryani`, `idli`, `paneer`, or `chicken curry`.

## API

- `GET /health` checks service availability.
- `POST /search-food` with `{"query": "idli"}` searches USDA descriptions.
- `POST /confirm-food` with the returned `state_id` and an offered `food`
  completes an ambiguous search.

## Render deployment

The included `render.yaml` deploys two free web services. Set `MISTRAL_API_KEY`
as a secret in Render; do not add it to this repository. Render passes the API
service URL to the frontend through `API_URL` automatically. Deploy the API
first, wait for its `/health` endpoint to return `mode: text-only`, then deploy
the frontend. The application performs no model download or heavyweight ML
model load at startup or request time, making it suitable for a 512 MB instance.
