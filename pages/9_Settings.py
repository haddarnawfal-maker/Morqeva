import streamlit as st
from config.settings import MASTER_RULES, VERSION
from utils.helpers import page_header

page_header("Settings", "Cloud readiness, AI engine status and locked MORQEVA production rules.")

def secret_exists(path):
    try:
        cur = st.secrets
        for part in path:
            cur = cur[part]
        return bool(cur)
    except Exception:
        return False

c1,c2,c3 = st.columns(3)
try:
    conn = st.connection("sql", type="sql")
    conn.query("select 1", ttl=0)
    db_status = "Connected"
except Exception:
    db_status = "Missing"

c1.metric("Cloud Database", db_status)
c2.metric("Gemini API", "Connected" if secret_exists(["GEMINI_API_KEY"]) else "Missing")
c3.metric("Version", VERSION)

st.markdown("### AI generation")
try:
    model = st.secrets.get("GEMINI_MODEL", "gemini-3.6-flash")
    grounding = st.secrets.get("ENABLE_GROUNDING", True)
except Exception:
    model = "gemini-3.6-flash"
    grounding = True
st.write("**Model:**", model)
st.write("**Google Search grounding:**", "Enabled" if grounding else "Disabled")
st.info("Verified Real and Folklore modes require live Google Search grounding. MORQEVA refuses to silently downgrade those modes to unverified model-memory output.")

st.markdown("### Locked master format")
for k,v in MASTER_RULES.items():
    st.write(f"**{k.replace('_',' ').title()}** — {v}")
