import pandas as pd
import streamlit as st

from components.story_ui import render_research, render_scene, render_sources
from data.store import load_stories, content_id
from models.story_blueprint import StoryBlueprint
from utils.helpers import cloud_guard, page_header, status_label

cloud_guard()
page_header("Story Library", "Every MORQEVA story and its complete intelligence blueprint in one cloud workspace.")
stories = load_stories()

if not stories:
    st.info("No stories yet. Create the first one from Create Story.")
    st.stop()

labels = [f"{content_id(s)} · {s.get('title','Untitled')} · {status_label(s.get('status',''))}" for s in stories]
selected = st.selectbox("Story", range(len(stories)), format_func=lambda i: labels[i])
story = stories[selected]
bp_raw = story.get("blueprint") or {}

if not bp_raw:
    st.warning("This record has no blueprint yet.")
    st.stop()

bp = StoryBlueprint.model_validate(bp_raw)
st.markdown(f"## {content_id(story)} · {bp.final_title}")
t1, t2, t3 = st.tabs(["Research", "10 scenes", "Sources"])
with t1:
    render_research(bp)
with t2:
    for s in bp.scenes:
        render_scene(s)
with t3:
    render_sources(bp)
