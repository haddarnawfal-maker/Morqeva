import streamlit as st

from data.store import load_stories, update_story, content_id
from models.story_blueprint import StoryBlueprint
from utils.helpers import cloud_guard, page_header

cloud_guard()
page_header("Quality Control", "One final check before the MORQEVA master leaves the vault.")
stories = [s for s in load_stories() if s.get("status") == "QC"]
if not stories:
    st.info("No stories are waiting for QC.")
    st.stop()
idx = st.selectbox("Story", range(len(stories)), format_func=lambda i: f"{content_id(stories[i])} · {stories[i].get('title','')}")
story = stories[idx]
bp = StoryBlueprint.model_validate(story.get("blueprint") or {})

checks = [
    "Exactly 10 scenes are present and correctly ordered",
    "Final runtime is 60–65 seconds",
    "There is NO narration / talking host",
    "English is the large primary caption and Darija is smaller underneath",
    "All captions are readable before each scene changes",
    "Music supports the mood without overpowering SFX",
    "Scene-specific SFX are present where useful",
    "Visual style and location/characters remain coherent",
    "No obvious AI morphing, malformed anatomy or accidental text/watermarks",
    "Claims match their VERIFIED / FOLKLORE / FICTION wording",
    "Final export is 9:16 and ideally 1080×1920",
]
with st.form("qc"):
    results = [st.checkbox(item, value=False) for item in checks]
    notes = st.text_area("QC notes")
    passed = st.form_submit_button("✓ Pass QC → Master", type="primary", use_container_width=True)
    if passed:
        if not all(results):
            st.error("Complete every QC check before passing the master.")
        else:
            update_story(story["id"], {"status":"MASTER", "production": {**(story.get("production") or {}), "qc_notes":notes}})
            st.success("QC passed.")
            st.rerun()
