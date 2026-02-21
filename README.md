# InternOS Backend Quickstart


## 1) Setup
python -m venv .venv && source .venv/bin/activate # Windows: .venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.sample .env


## 2) Seed a sample ticket
# Option A: local path repo\ nmkdir -p ../tickets/sample_repos/bugfix_api
# Put a tiny FastAPI app + tests there (or point tickets/sample_bug_ticket.json to your repo)


# Insert the ticket into DB via uvicorn startup or curl:
python - <<'PY'
from app.db import engine, SessionLocal
from app.models import Base, Ticket
import json
Base.metadata.create_all(bind=engine)
s = SessionLocal()
obj = json.load(open("../tickets/sample_bug_ticket.json"))
if not s.query(Ticket).filter_by(id=obj["id"]).first():
s.add(Ticket(id=obj["id"], kind=obj["kind"], repo_url=obj["repo_url"], rubric_json=obj["rubric_json"], time_limit=obj["time_limit"]))
s.commit()
print("Ticket seeded")
PY


## 3) Run API
uvicorn app.main:app --reload --port 8000


## 4) Run Streamlit UI (separate shell)
cd ../streamlit_app
streamlit run Home.py --server.port 8501


### Streamlit Secrets
# Create `.streamlit/secrets.toml` with:
# API_URL = "http://localhost:8000"


## 5) n8n integration (optional)
# In .env set N8N_WEBHOOK_URL to your n8n webhook URL.
# On submit, the backend POSTs the attempt payload to n8n.


### Example n8n nodes
- **Webhook (POST)** → **IF** `scores.overall >= 0.75` → **Send Email**
- **Webhook (POST)** → **Google Sheets** append row (handle, attempt_id, overall, coverage)
- **Webhook (POST)** → **Badge mint** (future)


## 6) Notes
- For Postgres, set DATABASE_URL accordingly and install `psycopg`.
- The rubric in `rubric.py` is tunable; weights can be per‑ticket later.
- Complexity via `radon`; lint via `flake8`; tests via `pytest`; coverage via `coverage`.