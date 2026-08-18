import html
import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo

from data.store import load_stories, content_id
from utils.helpers import cloud_guard, page_header, status_label

cloud_guard()
page_header("Command Center","Everything moving through MORQEVA, in one operational view.","MORQEVA · LIVE STUDIO")
stories=load_stories()
counts={k:sum(s.get("status")==k for s in stories) for k in ["BLUEPRINT_REVIEW","PRODUCTION","QC","MASTER","DISTRIBUTION","ANALYTICS"]}

now_ma=datetime.now(ZoneInfo("Africa/Casablanca")); today=now_ma.date(); today_calls=0; today_story_count=0
for story in stories:
    updated=story.get("updated_at")
    if updated:
        try:
            if updated.astimezone(ZoneInfo("Africa/Casablanca")).date()==today:
                usage=(story.get("performance") or {}).get("ai_usage") or {}; calls=int(usage.get("calls",0) or 0); today_calls+=calls; today_story_count+=int(calls>0)
        except Exception: pass
remaining=max(0,20-today_calls)

st.markdown(f'''<div class="mq-topgrid">
<div class="mq-stat"><small>Total vault</small><b>{len(stories)}</b></div>
<div class="mq-stat"><small>Producing</small><b>{counts['PRODUCTION']}</b></div>
<div class="mq-stat"><small>Awaiting QC</small><b>{counts['QC']}</b></div>
<div class="mq-stat"><small>Published</small><b>{counts['ANALYTICS']}</b></div>
</div>''',unsafe_allow_html=True)

st.markdown('<div class="mq-section"><h3>Pipeline</h3><span>LIVE WORKFLOW</span></div>',unsafe_allow_html=True)
st.markdown(f'''<div class="mq-pipeline">
<div class="mq-stage"><strong>{len(stories)}</strong><span>Vault</span></div>
<div class="mq-stage {'active' if counts['BLUEPRINT_REVIEW'] else ''}"><strong>{counts['BLUEPRINT_REVIEW']}</strong><span>Blueprint</span></div>
<div class="mq-stage {'active' if counts['PRODUCTION'] else ''}"><strong>{counts['PRODUCTION']}</strong><span>Production</span></div>
<div class="mq-stage {'active' if counts['QC'] else ''}"><strong>{counts['QC']}</strong><span>QC</span></div>
<div class="mq-stage {'active' if counts['MASTER']+counts['DISTRIBUTION'] else ''}"><strong>{counts['MASTER']+counts['DISTRIBUTION']}</strong><span>Ready</span></div>
<div class="mq-stage {'active' if counts['ANALYTICS'] else ''}"><strong>{counts['ANALYTICS']}</strong><span>Published</span></div></div>''',unsafe_allow_html=True)

left,right=st.columns([1.55,.75])
with left:
    st.markdown('<div class="mq-section"><h3>Active vault</h3><span>RECENT STORIES</span></div>',unsafe_allow_html=True)
    if stories:
        for story in stories[:6]:
            bp=story.get("blueprint") or {}; prod=story.get("production") or {}; scenes=prod.get("scenes") or {}
            approved=sum(bool(v.get("approved")) for v in scenes.values()) if scenes else 0
            status=status_label(story.get("status","")); country=bp.get("country",story.get("country", "")) or "Dark Vault"
            progress=approved*10 if scenes else (15 if story.get("status")=="BLUEPRINT_REVIEW" else 0)
            st.markdown(f'''<div class="mq-story"><div class="mq-story-head"><div><span class="mq-pill">{html.escape(content_id(story))}</span><span class="mq-pill">{html.escape(status)}</span><h4>{html.escape(story.get('title','Untitled'))}</h4><div class="mq-muted">{html.escape(country)} · {approved}/10 scenes approved</div></div><div class="mq-muted">{progress}%</div></div><div class="mq-progress"><i style="width:{progress}%"></i></div></div>''',unsafe_allow_html=True)
    else: st.success("Vault ready. Create the first story.")
with right:
    st.markdown('<div class="mq-section"><h3>AI budget</h3><span>FREE TIER</span></div>',unsafe_allow_html=True)
    pct=min(100,(today_calls/20)*100)
    st.markdown(f'''<div class="mq-card"><span class="mq-pill">GEMINI 3.6 FLASH</span><h2 style="margin:.7rem 0 .1rem">{remaining}<span style="font-size:.9rem;color:#858897"> / 20 left</span></h2><div class="mq-quota"><div style="width:{pct:.0f}%"></div></div><div class="mq-muted">{today_calls} requests tracked today · {today_story_count} stories · resets midnight PT</div></div>''',unsafe_allow_html=True)
    st.markdown('<div class="mq-section"><h3>Systems</h3><span>HEALTH</span></div>',unsafe_allow_html=True)
    st.markdown('''<div class="mq-card"><div class="mq-health"><b>Cloud database</b><span>● ONLINE</span></div><div class="mq-health"><b>Story engine</b><span>● READY</span></div><div class="mq-health"><b>Production stack</b><span>● READY</span></div></div>''',unsafe_allow_html=True)
    st.caption("Production work uses no Gemini quota unless AI content is regenerated.")
