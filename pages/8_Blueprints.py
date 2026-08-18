import streamlit as st
from config.settings import MASTER_RULES
from utils.helpers import page_header

page_header("Blueprints & Templates", "The master rules MORQEVA must follow every time.")

st.markdown("### Dark Vault master process")
st.code("SEED → RESEARCH → FACT SAFETY → 5 HOOKS → 10 SCENES → FLOW → VIBES / SYMPHONY → CAPCUT → QC → DISTRIBUTE → ANALYZE", language="text")

for k,v in MASTER_RULES.items():
    st.markdown(f"**{k.replace('_',' ').title()}:** {v}")

st.markdown("### Story standards")
st.markdown("- Worldwide obscure subjects; Morocco appears regularly but is never forced.\n- Real old documented material is preferred.\n- Verified facts, folklore, uncertainty and fiction must never be silently mixed.\n- Dark Vault is mysterious because the subject is interesting—not because fake ghosts are added.\n- English is the main on-screen language; natural Darija in Latin/French letters sits smaller underneath.")
