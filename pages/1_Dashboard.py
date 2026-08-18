import html
import streamlit as st
from datetime import datetime
from zoneinfo import ZoneInfo
from data.store import load_stories, content_id
from utils.helpers import cloud_guard, page_header, status_label

cloud_guard()
page_header("Executive Dashboard","High-level control of MORQEVA: pipeline, active stories, production readiness and AI usage.","MORQEVA · COMMAND CENTER")
stories=load_stories()
counts={k:sum(s.get("status")==k for s in stories) for k in ["BLUEPRINT_REVIEW","PRODUCTION","QC","MASTER","DISTRIBUTION","ANALYTICS"]}

now_ma=datetime.now(ZoneInfo("Africa/Casablanca")); today=now_ma.date(); tracked_calls=0; stories_today=0
for story in stories:
    updated=story.get("updated_at")
    if not updated: continue
    try:
        if updated.astimezone(ZoneInfo("Africa/Casablanca")).date()==today:
            usage=(story.get("performance") or {}).get("ai_usage") or {}; calls=int(usage.get("calls",0) or 0)
            tracked_calls+=calls; stories_today+=int(calls>0)
    except Exception: pass

active=sum(counts[k] for k in ["BLUEPRINT_REVIEW","PRODUCTION","QC","MASTER","DISTRIBUTION"])
st.markdown(f'''<div class="mq-topgrid">
<div class="mq-stat"><small>Total stories</small><b>{len(stories)}</b></div>
<div class="mq-stat"><small>Active pipeline</small><b>{active}</b></div>
<div class="mq-stat"><small>In production</small><b>{counts['PRODUCTION']}</b></div>
<div class="mq-stat"><small>Published</small><b>{counts['ANALYTICS']}</b></div></div>''',unsafe_allow_html=True)

st.markdown('<div class="mq-section"><h3>Pipeline</h3><span>FROM IDEA TO PUBLISH</span></div>',unsafe_allow_html=True)
st.markdown(f'''<div class="mq-pipeline">
<div class="mq-stage"><strong>{len(stories)}</strong><span>Vault</span></div>
<div class="mq-stage {'active' if counts['BLUEPRINT_REVIEW'] else ''}"><strong>{counts['BLUEPRINT_REVIEW']}</strong><span>Blueprint</span></div>
<div class="mq-stage {'active' if counts['PRODUCTION'] else ''}"><strong>{counts['PRODUCTION']}</strong><span>Production</span></div>
<div class="mq-stage {'active' if counts['QC'] else ''}"><strong>{counts['QC']}</strong><span>QC</span></div>
<div class="mq-stage {'active' if counts['MASTER']+counts['DISTRIBUTION'] else ''}"><strong>{counts['MASTER']+counts['DISTRIBUTION']}</strong><span>Ready</span></div>
<div class="mq-stage {'active' if counts['ANALYTICS'] else ''}"><strong>{counts['ANALYTICS']}</strong><span>Published</span></div></div>''',unsafe_allow_html=True)

left,right=st.columns([1.55,.75])
with left:
    st.markdown('<div class="mq-section"><h3>Active stories</h3><span>PRIORITY WORKSPACE</span></div>',unsafe_allow_html=True)
    active_stories=[s for s in stories if s.get("status")!="ANALYTICS"][:6]
    if active_stories:
        for story in active_stories:
            bp=story.get("blueprint") or {}; prod=story.get("production") or {}; scenes=prod.get("scenes") or {}
            approved=sum(bool(v.get("approved")) for v in scenes.values()) if scenes else 0
            status=status_label(story.get("status","")); country=bp.get("country",story.get("country", "")) or "Dark Vault"
            progress=approved*10 if scenes else (15 if story.get("status")=="BLUEPRINT_REVIEW" else 0)
            st.markdown(f'''<div class="mq-story"><div class="mq-story-head"><div><span class="mq-pill">{html.escape(content_id(story))}</span><span class="mq-pill">{html.escape(status)}</span><h4>{html.escape(story.get('title','Untitled'))}</h4><div class="mq-muted">{html.escape(country)} · {approved}/10 scenes approved</div></div><div class="mq-muted">{progress}%</div></div><div class="mq-progress"><i style="width:{progress}%"></i></div></div>''',unsafe_allow_html=True)
    else: st.success("Nothing pending. The active pipeline is clear.")
with right:
    st.markdown('<div class="mq-section"><h3>Gemini usage</h3><span>FREE TIER</span></div>',unsafe_allow_html=True)
    pct=min(100,(tracked_calls/20)*100)
    st.markdown(f'''<div class="mq-card"><span class="mq-pill">20 RPD LIMIT</span><h2 style="margin:.7rem 0 .1rem">{tracked_calls}<span style="font-size:.9rem;color:#858897"> MORQEVA calls today</span></h2><div class="mq-quota"><div style="width:{pct:.0f}%"></div></div><div class="mq-muted">Google project limit: 20 requests/day · MORQEVA-tracked usage only · {stories_today} story generation(s) today</div></div>''',unsafe_allow_html=True)
    st.warning("Actual remaining Google quota cannot be read reliably from the app. A 429 means the project quota is exhausted even if MORQEVA tracked fewer than 20 calls.")
    st.markdown('<div class="mq-section"><h3>Systems</h3><span>HEALTH</span></div>',unsafe_allow_html=True)
    st.markdown('''<div class="mq-card"><div class="mq-health"><b>Cloud database</b><span>● ONLINE</span></div><div class="mq-health"><b>Story engine</b><span>● READY</span></div><div class="mq-health"><b>Production stack</b><span>● READY</span></div></div>''',unsafe_allow_html=True)
