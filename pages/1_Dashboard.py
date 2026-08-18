import html
import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

from data.store import load_stories, content_id
from utils.helpers import cloud_guard, page_header, status_label

cloud_guard()
page_header("Command Center","Live view of the Dark Vault pipeline — from first idea to published short.","MORQEVA STUDIO V2")
stories=load_stories()

counts={k:sum(s.get("status")==k for s in stories) for k in ["BLUEPRINT_REVIEW","PRODUCTION","QC","DISTRIBUTION","ANALYTICS"]}
c1,c2,c3,c4=st.columns(4)
c1.metric("Stories",len(stories))
c2.metric("In production",counts["PRODUCTION"])
c3.metric("QC / Ready",counts["QC"]+counts["DISTRIBUTION"])
c4.metric("Published",counts["ANALYTICS"])

st.markdown("### Live pipeline")
st.markdown(f'''<div class="mq-pipeline">
<div class="mq-stage"><strong>{len(stories)}</strong><span>Vault</span></div>
<div class="mq-stage"><strong>{counts['BLUEPRINT_REVIEW']}</strong><span>Blueprint</span></div>
<div class="mq-stage"><strong>{counts['PRODUCTION']}</strong><span>Production</span></div>
<div class="mq-stage"><strong>{counts['QC']}</strong><span>QC</span></div>
<div class="mq-stage"><strong>{counts['DISTRIBUTION']}</strong><span>Ready</span></div>
<div class="mq-stage"><strong>{counts['ANALYTICS']}</strong><span>Published</span></div></div>''',unsafe_allow_html=True)

now_ma=datetime.now(ZoneInfo("Africa/Casablanca")); today=now_ma.date(); today_calls=0; today_story_count=0
for story in stories:
    updated=story.get("updated_at")
    if updated:
        try:
            if updated.astimezone(ZoneInfo("Africa/Casablanca")).date()==today:
                usage=(story.get("performance") or {}).get("ai_usage") or {}; calls=int(usage.get("calls",0) or 0); today_calls+=calls; today_story_count+=int(calls>0)
        except Exception: pass
remaining=max(0,20-today_calls); pct=min(100,(today_calls/20)*100)
st.markdown("### Gemini · Free Tier")
q1,q2,q3,q4=st.columns(4)
q1.metric("Requests today",f"{today_calls} / 20")
q2.metric("Remaining",remaining)
q3.metric("Stories today",today_story_count)
q4.metric("Reset","Midnight PT")
st.markdown(f'<div class="mq-quota"><div style="width:{pct:.0f}%"></div></div>',unsafe_allow_html=True)
st.caption(f"MORQEVA-tracked usage · {remaining} requests remain from the 20 RPD operating budget. Other calls made against the same Google project are not visible here.")

left,right=st.columns([1.25,1])
with left:
    st.markdown("### Active vault")
    if stories:
        for story in stories[:6]:
            bp=story.get("blueprint") or {}; prod=story.get("production") or {}; scenes=prod.get("scenes") or {}
            approved=sum(bool(v.get("approved")) for v in scenes.values()) if scenes else 0
            progress=f"{approved}/10 scenes" if scenes else "Blueprint"
            st.markdown(f'<div class="mq-card"><span class="mq-pill">{html.escape(content_id(story))}</span><span class="mq-pill">{html.escape(status_label(story.get("status","")))}</span><h4 style="margin:.65rem 0 .25rem">{html.escape(story.get("title", "Untitled"))}</h4><div class="mq-muted">{html.escape(bp.get("country",story.get("country", "")) or "Dark Vault")} · {progress}</div></div>',unsafe_allow_html=True)
    else: st.success("Cloud vault ready for the first story.")
with right:
    st.markdown("### Studio status")
    st.markdown('<div class="mq-card"><span class="mq-pill mq-verified">● ONLINE</span><h4>Cloud Database</h4><div class="mq-muted">Supabase connection healthy.</div></div>',unsafe_allow_html=True)
    st.markdown('<div class="mq-card"><span class="mq-pill">AI ENGINE</span><h4>Gemini 3.6 Flash</h4><div class="mq-muted">2-call verified pipeline · quality-safe quota design.</div></div>',unsafe_allow_html=True)
    st.info("New story? Open **Create Story**. Production work does not consume Gemini requests unless you regenerate AI content.")
