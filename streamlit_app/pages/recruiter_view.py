import os
import requests
import streamlit as st

st.set_page_config(page_title="Recruiter View", page_icon="👤", layout="wide")
API = os.getenv("INTERNOS_API_URL") or st.secrets.get("API_URL", "http://localhost:8000")

st.title("👤 Recruiter View")
with st.sidebar:
    st.subheader("Settings")
    st.write("**API:**", API)

handle = st.text_input("Candidate handle", value=st.session_state.get("handle", "suyogya"))

if st.button("Generate Signal Report", type="primary"):
    try:
        r = requests.get(f"{API}/recruiter/{handle}", timeout=20)
        if r.ok:
            payload = r.json()
            snapshot = payload.get("snapshot", {})
            summary = snapshot.get("summary", {})
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Tickets shipped", summary.get("tickets_shipped", 0))
            cov = summary.get("coverage", 0.0)
            c2.metric("Coverage (avg)", f"{cov*100:.1f}%")
            c3.metric("Cyclomatic avg", summary.get("avg_cyclomatic", 0.0))
            c4.metric("PR size (avg)", summary.get("pr_size", 0.0))
            st.subheader("Scores")
            st.json(summary.get("scores", {}))
        else:
            st.error(f"{r.status_code} — {r.text}")
    except requests.RequestException as e:
        st.error(f"Request failed: {e}")
