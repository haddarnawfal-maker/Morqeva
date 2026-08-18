from datetime import date
import html
import streamlit as st
from data.store import load_stories,update_story,content_id
from utils.helpers import cloud_guard,page_header
cloud_guard(); page_header("Distribution Console","One master. Four channels. One publishing record.","MORQEVA · RELEASE DESK")
stories=[s for s in load_stories() if s.get("status") in {"MASTER","DISTRIBUTION","ANALYTICS"}]
if not stories: st.markdown('<div class="mq-card"><span class="mq-pill">NO MASTER</span><h3>Distribution queue is empty</h3><div class="mq-muted">A video appears here immediately after it passes Quality Control.</div></div>',unsafe_allow_html=True); st.stop()
idx=st.selectbox("Release",range(len(stories)),format_func=lambda i:f"{content_id(stories[i])} · {stories[i].get('title','')}"); story=stories[idx]; dist=story.get("distribution") or {}
channels=[("TikTok",dist.get("tiktok_url","")),("Instagram",dist.get("instagram_url","")),("YouTube",dist.get("youtube_url","")),("Facebook",dist.get("facebook_url",""))]; live=sum(bool(v) for _,v in channels)
st.markdown(f'''<div class="mq-card"><span class="mq-pill">{html.escape(content_id(story))}</span><span class="mq-pill {'mq-verified' if live else ''}">{live}/4 LIVE</span><h3>{html.escape(story.get('title','Untitled'))}</h3><div class="mq-progress"><i style="width:{live*25}%"></i></div><div class="mq-muted" style="margin-top:8px">Publishing coverage · {live*25}%</div></div>''',unsafe_allow_html=True)
st.markdown('<div class="mq-section"><h3>Channel status</h3><span>PUBLICATION MATRIX</span></div>',unsafe_allow_html=True)
cols=st.columns(4)
for col,(name,url) in zip(cols,channels):
 with col: st.markdown(f'<div class="mq-stat"><small>{name}</small><b style="font-size:.95rem">{"● LIVE" if url else "○ WAITING"}</b></div>',unsafe_allow_html=True)
st.markdown('<div class="mq-section"><h3>Release details</h3><span>SAVE AFTER PUBLISHING</span></div>',unsafe_allow_html=True)
with st.form("dist"):
 master_url=st.text_input("Master video / cloud location",value=dist.get("master_url",""),placeholder="Optional master asset URL")
 publish_date=st.date_input("Publish date",date.today())
 c1,c2=st.columns(2); tiktok=c1.text_input("TikTok",value=dist.get("tiktok_url",""),placeholder="Paste published URL"); instagram=c2.text_input("Instagram Reels",value=dist.get("instagram_url",""),placeholder="Paste published URL"); youtube=c1.text_input("YouTube Shorts",value=dist.get("youtube_url",""),placeholder="Paste published URL"); facebook=c2.text_input("Facebook Reels",value=dist.get("facebook_url",""),placeholder="Paste published URL")
 save=st.form_submit_button("Save release status",type="primary",use_container_width=True)
 if save:
  payload={"master_url":master_url,"publish_date":str(publish_date),"tiktok_url":tiktok,"instagram_url":instagram,"youtube_url":youtube,"facebook_url":facebook}; status="ANALYTICS" if any([tiktok,instagram,youtube,facebook]) else "DISTRIBUTION"; update_story(story["id"],{"distribution":payload,"status":status}); st.success("Release desk updated."); st.rerun()
