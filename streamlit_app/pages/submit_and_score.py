import os
import requests
import streamlit as st

st.set_page_config(page_title="Submit & Score", page_icon="📤", layout="wide")
API = os.getenv("INTERNOS_API_URL") or st.secrets.get("API_URL", "http://localhost:8000")

st.title("📤 Submit & Score")
with st.sidebar:
    st.subheader("Settings")
    st.write("**API:**", API)

attempt_id = st.number_input(
    "Attempt ID",
    min_value=1,
    value=int(st.session_state.get("attempt_id", 1)),
    step=1,
)
pr_url = st.text_input("PR URL (optional)")
standup = st.text_area("Stand-up / PR description (scored for clarity)", height=160)
postmortem = st.text_area("Postmortem (optional; for incident drills)", height=160)

if st.button("Submit for grading", type="primary"):
    payload = {
        "attempt_id": int(attempt_id),
        "pr_url": pr_url or None,
        "standup_text": standup or None,
        "postmortem_text": postmortem or None,
    }
    try:
        r = requests.post(f"{API}/tickets/submit", json=payload, timeout=60)
        if r.ok:
            out = r.json()
            st.success("Grading complete.")
            st.subheader("Scores")
            st.json(out.get("scores", {}))
        else:
            st.error(f"{r.status_code} — {r.text}")
    except requests.RequestException as e:
        st.error(f"Request failed: {e}")
