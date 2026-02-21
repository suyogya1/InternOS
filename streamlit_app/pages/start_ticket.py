import os
import requests
import streamlit as st

st.set_page_config(page_title="Start Ticket", page_icon="🏁", layout="wide")
API = os.getenv("INTERNOS_API_URL") or st.secrets.get("API_URL", "http://localhost:8000")

st.title("🏁 Start Ticket")
with st.sidebar:
    st.subheader("Settings")
    st.write("**API:**", API)

handle = st.text_input("Your handle", value=st.session_state.get("handle", "suyogya"))
ticket_id = st.number_input("Ticket ID", min_value=1, value=1, step=1)

if st.button("Start Ticket", type="primary"):
    try:
        r = requests.post(f"{API}/tickets/start", json={"handle": handle, "ticket_id": int(ticket_id)}, timeout=20)
        if r.ok:
            data = r.json()
            st.success(f"Attempt #{data['attempt_id']} created.")
            st.code(f"Repo cloned at: {data['repo_path']}", language="bash")
            st.session_state["attempt_id"] = data["attempt_id"]
            st.session_state["handle"] = handle
        else:
            st.error(f"{r.status_code} — {r.text}")
    except requests.RequestException as e:
        st.error(f"Request failed: {e}")
