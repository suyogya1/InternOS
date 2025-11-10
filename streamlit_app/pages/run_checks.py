import os
import requests
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Run Checks", page_icon="🧪", layout="wide")
API = os.getenv("INTERNOS_API_URL") or st.secrets.get("API_URL", "http://localhost:8000")

st.title("🧪 Run Checks")
with st.sidebar:
    st.subheader("Settings")
    st.write("**API:**", API)

attempt_id = st.number_input(
    "Attempt ID",
    min_value=1,
    value=int(st.session_state.get("attempt_id", 1)),
    step=1,
)

if st.button("Refresh metrics", type="primary"):
    try:
        r = requests.get(f"{API}/attempts/{attempt_id}/metrics", timeout=20)
        if r.ok:
            data = r.json()
            st.success(f"Attempt #{data['attempt_id']} — status: {data['status']}")
            metrics = data.get("metrics", [])
            if metrics:
                st.dataframe(pd.DataFrame(metrics), use_container_width=True)
            else:
                st.warning("No metrics yet.")
        else:
            st.error(f"{r.status_code} — {r.text}")
    except requests.RequestException as e:
        st.error(f"Request failed: {e}")
