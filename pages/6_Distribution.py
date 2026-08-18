from datetime import date
import streamlit as st

from data.store import load_stories, update_story, content_id
from utils.helpers import cloud_guard, page_header

cloud_guard()
page_header("Master Distribution", "Track one master across TikTok, Instagram Reels and YouTube Shorts.")
stories = [s for s in load_stories() if s.get("status") in {"MASTER","DISTRIBUTION","ANALYTICS"}]
if not stories:
    st.info("No master is ready for distribution.")
    st.stop()
idx = st.selectbox("Story", range(len(stories)), format_func=lambda i: f"{content_id(stories[i])} · {stories[i].get('title','')}")
story = stories[idx]
dist = story.get("distribution") or {}

with st.form("dist"):
    master_url = st.text_input("Master video URL / cloud location (optional)", value=dist.get("master_url", ""))
    publish_date = st.date_input("Publish date", date.today())
    tiktok = st.text_input("TikTok URL", value=dist.get("tiktok_url", ""))
    instagram = st.text_input("Instagram Reel URL", value=dist.get("instagram_url", ""))
    youtube = st.text_input("YouTube Short URL", value=dist.get("youtube_url", ""))
    save = st.form_submit_button("Save Distribution", type="primary")
    if save:
        payload = {"master_url":master_url,"publish_date":str(publish_date),"tiktok_url":tiktok,"instagram_url":instagram,"youtube_url":youtube}
        status = "ANALYTICS" if any([tiktok, instagram, youtube]) else "DISTRIBUTION"
        update_story(story["id"], {"distribution":payload,"status":status})
        st.success("Distribution saved.")
        st.rerun()
