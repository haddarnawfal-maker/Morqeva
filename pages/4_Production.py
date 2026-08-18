import html
import pandas as pd
import streamlit as st
from components.story_ui import capcut_dataframe
from config.settings import FLOW_URL,VIBES_URL,SYMPHONY_URL
from data.store import load_stories,update_story,content_id
from models.story_blueprint import StoryBlueprint
from utils.helpers import cloud_guard,page_header,production_defaults
cloud_guard(); page_header("Production Studio","Build the 10-scene master from still → motion → approval.","MORQEVA · PRODUCTION")
stories=[s for s in load_stories() if s.get("status") in {"PRODUCTION","QC","MASTER"}]
if not stories: st.info("No approved blueprints are waiting for production."); st.stop()
idx=st.selectbox("Active story",range(len(stories)),format_func=lambda i:f"{content_id(stories[i])} · {stories[i].get('title','')}")
story=stories[idx]; bp=StoryBlueprint.model_validate(story.get("blueprint") or {}); production=story.get("production") or production_defaults(bp.model_dump(mode="json")); states=production.get("scenes") or {}
approved_count=sum(bool(states.get(str(i),{}).get("approved")) for i in range(1,11)); image_count=sum(bool(states.get(str(i),{}).get("image_done")) for i in range(1,11)); anim_count=sum(bool(states.get(str(i),{}).get("animation_done")) for i in range(1,11))
st.markdown(f'''<div class="mq-topgrid"><div class="mq-stat"><small>Story</small><b style="font-size:1rem">{html.escape(content_id(story))}</b></div><div class="mq-stat"><small>Stills ready</small><b>{image_count}/10</b></div><div class="mq-stat"><small>Animated</small><b>{anim_count}/10</b></div><div class="mq-stat"><small>Approved</small><b>{approved_count}/10</b></div></div>''',unsafe_allow_html=True)
st.markdown(f'<div class="mq-section"><h3>{html.escape(bp.final_title)}</h3><span>{approved_count*10}% COMPLETE</span></div><div class="mq-progress"><i style="width:{approved_count*10}%"></i></div>',unsafe_allow_html=True)
a,b,c=st.columns(3); a.link_button("↗ Flow",FLOW_URL,use_container_width=True); b.link_button("↗ Meta Vibes",VIBES_URL,use_container_width=True); c.link_button("↗ TikTok Symphony",SYMPHONY_URL,use_container_width=True)
all_flow="\n\n".join(f"SCENE {s.scene_number:02d}\n{s.flow_image_prompt}" for s in bp.scenes); all_vibes="\n\n".join(f"SCENE {s.scene_number:02d}\n{s.vibes_motion_prompt}" for s in bp.scenes); all_sym="\n\n".join(f"SCENE {s.scene_number:02d}\n{s.symphony_fallback_prompt}" for s in bp.scenes)
t1,t2,t3,t4=st.tabs(["◉ Scene board","Flow batch","Motion batch","CapCut sheet"])
with t1:
 changed=False
 for scene in bp.scenes:
  key=str(scene.scene_number); state=production.setdefault("scenes",{}).setdefault(key,{})
  done=bool(state.get("approved")); badge="READY" if done else "WORKING"
  with st.expander(f"{scene.scene_number:02d}  ·  {scene.duration_seconds:.1f}s  ·  {badge}  ·  {scene.english_caption}",expanded=scene.scene_number==1):
   st.markdown(f'<span class="mq-pill">SCENE {scene.scene_number:02d}</span><span class="mq-pill">{scene.duration_seconds:.1f}s</span>',unsafe_allow_html=True)
   st.caption("FLOW · STILL"); st.code(scene.flow_image_prompt,language="text"); st.caption("VIBES · MOTION"); st.code(scene.vibes_motion_prompt,language="text"); st.caption("SYMPHONY · FALLBACK"); st.code(scene.symphony_fallback_prompt,language="text")
   c1,c2,c3,c4=st.columns(4); ni=c1.checkbox("Still ready",bool(state.get("image_done")),key=f"img_{story['id']}_{key}"); na=c2.checkbox("Animated",bool(state.get("animation_done")),key=f"anim_{story['id']}_{key}"); opts=["Vibes","Symphony","Other"]; eng=c3.selectbox("Engine",opts,index=opts.index(state.get("animation_engine","Vibes")) if state.get("animation_engine","Vibes") in opts else 0,key=f"eng_{story['id']}_{key}"); ok=c4.checkbox("Approved",bool(state.get("approved")),key=f"ok_{story['id']}_{key}"); notes=st.text_input("Production note",state.get("notes",""),key=f"notes_{story['id']}_{key}"); ns={"image_done":ni,"animation_done":na,"animation_engine":eng,"approved":ok,"notes":notes}
   if ns!=state: production["scenes"][key]=ns; changed=True
 if changed: update_story(story["id"],{"production":production})
with t2: st.code(all_flow,language="text")
with t3: st.caption("VIBES · PRIMARY"); st.code(all_vibes,language="text"); st.caption("SYMPHONY · FALLBACK"); st.code(all_sym,language="text")
with t4: st.dataframe(capcut_dataframe(bp),use_container_width=True,hide_index=True); st.info(f"Caption: {bp.caption_direction}\n\nMusic: {bp.music_direction}")
if approved_count==10 and st.button("Send master to Quality Control →",type="primary",use_container_width=True): update_story(story["id"],{"status":"QC","production":production}); st.rerun()
