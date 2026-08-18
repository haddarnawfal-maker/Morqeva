import pandas as pd
import plotly.express as px
import streamlit as st

from data.store import load_stories, update_story, content_id
from utils.helpers import cloud_guard, page_header

cloud_guard()
page_header("Performance Analytics", "Measure what actually works: views, retention, shares, saves and follower gain.")
stories = [s for s in load_stories() if s.get("status") == "ANALYTICS"]
if not stories:
    st.info("Publish the first video to begin collecting real performance data.")
    st.stop()

idx = st.selectbox("Story", range(len(stories)), format_func=lambda i: f"{content_id(stories[i])} · {stories[i].get('title','')}")
story = stories[idx]
perf = story.get("performance") or {}

platforms = ["TikTok","Instagram Reels","YouTube Shorts"]
with st.form("analytics"):
    updated = {}
    for p in platforms:
        st.markdown(f"### {p}")
        cur = perf.get(p, {})
        c1,c2,c3,c4 = st.columns(4)
        views = c1.number_input("Views", min_value=0, value=int(cur.get("views",0)), key=f"v_{p}")
        likes = c2.number_input("Likes", min_value=0, value=int(cur.get("likes",0)), key=f"l_{p}")
        shares = c3.number_input("Shares", min_value=0, value=int(cur.get("shares",0)), key=f"s_{p}")
        saves = c4.number_input("Saves", min_value=0, value=int(cur.get("saves",0)), key=f"sv_{p}")
        c5,c6,c7 = st.columns(3)
        retention = c5.number_input("Avg retention %", min_value=0.0, max_value=100.0, value=float(cur.get("retention",0.0)), key=f"r_{p}")
        completion = c6.number_input("Completion %", min_value=0.0, max_value=100.0, value=float(cur.get("completion",0.0)), key=f"c_{p}")
        followers = c7.number_input("Followers gained", min_value=0, value=int(cur.get("followers_gained",0)), key=f"f_{p}")
        updated[p] = {"views":views,"likes":likes,"shares":shares,"saves":saves,"retention":retention,"completion":completion,"followers_gained":followers}
    if st.form_submit_button("Save Analytics", type="primary"):
        update_story(story["id"], {"performance":updated})
        st.success("Analytics saved.")
        st.rerun()

rows=[]
for s in stories:
    for platform, m in (s.get("performance") or {}).items():
        rows.append({"Story":content_id(s),"Platform":platform,"Views":m.get("views",0),"Retention":m.get("retention",0)})
if rows:
    df=pd.DataFrame(rows)
    st.plotly_chart(px.bar(df,x="Story",y="Views",color="Platform",barmode="group"),use_container_width=True)
