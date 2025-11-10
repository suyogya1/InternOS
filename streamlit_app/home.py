
import os, glob, streamlit as st

st.set_page_config(page_title="InternOS", page_icon="🚀", layout="wide")
st.title("InternOS — Recruiter-Signal Simulator")
st.write("A living portfolio that measures real internship readiness.")

# 🔎 Diagnostics so we can see what Streamlit sees
import pathlib
root = pathlib.Path(__file__).parent
pages_dir = root / "pages"
st.caption("Diagnostics (temporary):")
st.code(f"__file__: {__file__}\nroot: {root}\npages exists: {pages_dir.exists()}\nfound: {glob.glob(str(pages_dir/'*.py'))}")

# Actual navigation (requires files above to exist)
st.page_link("pages/1_Start_Ticket.py",      label="Start Ticket",   icon="🏁")
st.page_link("pages/2_Run_Checks.py",        label="Run Checks",     icon="🧪")
st.page_link("pages/3_Submit_and_Score.py",  label="Submit & Score", icon="📤")
st.page_link("pages/4_Recruiter_View.py",    label="Recruiter View", icon="👤")

st.divider()
st.caption("Tip: Put API base in `.streamlit/secrets.toml` as `API_URL` or env var `INTERNOS_API_URL`.")

