import pandas as pd
import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

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

st.markdown("### Gemini status")
now_ma = datetime.now(ZoneInfo("Africa/Casablanca"))
today = now_ma.date()
today_calls = 0
today_story_count = 0
for story in stories:
    updated = story.get("updated_at")
    if updated:
        try:
            if updated.astimezone(ZoneInfo("Africa/Casablanca")).date() == today:
                usage = (story.get("performance") or {}).get("ai_usage") or {}
                today_calls += int(usage.get("calls", 0) or 0)
                if usage.get("calls", 0):
                    today_story_count += 1
        except Exception:
            pass

q1, q2, q3, q4 = st.columns(4)
q1.metric("Tracked Gemini calls today", today_calls)
q2.metric("Stories using AI today", today_story_count)
q3.metric("Free-tier cost", "$0")
q4.metric("Daily reset", "Midnight Pacific")
st.caption("MORQEVA tracks the Gemini calls it makes. Google does not expose a reliable exact 'credits remaining' number to this app; the project-specific Rate Limits/Usage dashboard in Google AI Studio is the source of truth. A 429 can also be caused by requests/minute or tokens/minute, not only the daily request limit.")

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
            "Updated": story.get("updated_at").strftime("%Y-%m-%d %H:%M") if story.get("updated_at") else "",
        })
    st.markdown("### Recent stories")
    st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
else:
    st.success("Cloud workspace is empty and ready for the first MORQEVA story.")
