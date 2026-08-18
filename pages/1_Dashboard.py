import pandas as pd
import streamlit as st

from data.store import load_stories, content_id
from utils.helpers import cloud_guard, page_header, status_label

cloud_guard()
page_header("Executive Dashboard", "Capture an idea anywhere, turn it into a complete 10-scene production blueprint, then track it to publication.")

stories = load_stories()

c1, c2, c3, c4 = st.columns(4)
c1.metric("Stories", len(stories))
c2.metric("Blueprint review", sum(s.get("status") == "BLUEPRINT_REVIEW" for s in stories))
c3.metric("In production", sum(s.get("status") == "PRODUCTION" for s in stories))
c4.metric("Published", sum(s.get("status") == "ANALYTICS" for s in stories))

st.markdown("### Quick capture")
st.info("Use **Create Story** from the sidebar. On mobile, enter only the seed/title, choose story mode, and tap Generate Full Blueprint.")

if stories:
    rows = []
    for story in stories:
        bp = story.get("blueprint") or {}
        rows.append({
            "ID": content_id(story),
            "Title": story.get("title", ""),
            "Country": bp.get("country", story.get("country", "")),
            "Mode": story.get("story_mode", "").replace("_", " ").title(),
            "Status": status_label(story.get("status", "")),
            "Updated": (story.get("updated_at") or "")[:16].replace("T", " "),
        })
    st.markdown("### Recent stories")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.success("Cloud workspace is empty and ready for the first MORQEVA story.")
