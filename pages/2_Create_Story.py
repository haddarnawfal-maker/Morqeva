import html
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st
from sqlalchemy import text
from ai.story_engine import generate_blueprint,regenerate_hooks,regenerate_scene
from components.story_ui import render_hook_picker,render_research,render_scene,render_sources
from config.settings import STORY_MODES,ORIGIN_OPTIONS
from data.store import create_story,update_story,content_id,get_story,record_ai_usage,summarize_ai_usage,get_connection
from models.story_blueprint import StoryBlueprint
from utils.helpers import cloud_guard,page_header,production_defaults

cloud_guard(); page_header("Create Story Studio","One seed becomes a researched 10-scene production blueprint.","MORQEVA · INTELLIGENCE LAB")
try:
 api_key=str(st.secrets["GEMINI_API_KEY"]); model=str(st.secrets.get("GEMINI_MODEL","gemini-3.6-flash")); grounding_enabled=bool(st.secrets.get("ENABLE_GROUNDING",True))
except Exception:
 st.error("Gemini API is not configured in Streamlit Secrets."); st.stop()

def delete_story_local(story_id:int):
 conn=get_connection()
 with conn.session as session:
  session.execute(text("delete from public.stories where id=:id"),{"id":story_id}); session.commit()

def render_ai_usage(performance):
 usage=(performance or {}).get("ai_usage") or {}
 if not usage: st.caption("Usage tracking starts with the next AI generation for this story."); return
 c1,c2,c3,c4=st.columns(4); c1.metric("Calls",int(usage.get("calls",0) or 0)); c2.metric("Input",f"{int(usage.get('input_tokens',0) or 0):,}"); c3.metric("Output",f"{int(usage.get('billed_output_tokens',0) or 0):,}"); c4.metric("Cached",f"{int(usage.get('cached_tokens',0) or 0):,}")
 st.caption(f"Thinking {int(usage.get('thought_tokens',0) or 0):,} · Grounded search {int(usage.get('search_requests',0) or 0)} · Est. cost ${float(usage.get('estimated_cost_usd',0) or 0):.4f}")

def _quota_reset_context():
 """Return the next Gemini RPD reset in Morocco time.

 Google documents RPD resets at midnight Pacific time. This calculation uses real
 timezone rules instead of hard-coding 08:00, so DST changes stay correct.
 """
 pacific=ZoneInfo("America/Los_Angeles")
 morocco=ZoneInfo("Africa/Casablanca")
 now_pt=datetime.now(pacific)
 next_reset_pt=(now_pt+timedelta(days=1)).replace(hour=0,minute=0,second=0,microsecond=0)
 next_reset_ma=next_reset_pt.astimezone(morocco)
 return next_reset_ma

def _quota_kind(message:str):
 l=(message or "").lower().replace("_","").replace("-","").replace(" ","")
 daily_markers=("requestsperday","perday","rpd","dailyquota","generatedrequestsperday")
 minute_markers=("requestsperminute","perminute","rpm","tokensperminute","tpm")
 if any(marker in l for marker in daily_markers): return "daily"
 if any(marker in l for marker in minute_markers): return "minute"
 return "unknown"

def show_generation_error(exc):
 m=str(exc); l=m.lower()
 if "429" in l or "quota" in l or "resource_exhausted" in l:
  kind=_quota_kind(m)
  if kind=="daily":
   reset=_quota_reset_context()
   st.error(f"Gemini daily request quota is exhausted for this Google Cloud project. Daily quota resets at midnight Pacific time — next reset is about {reset.strftime('%H:%M')} Morocco time on {reset.strftime('%d %b')}.")
   st.info("This quota is shared by the whole Google Cloud project, not just this API key. If you have not used MORQEVA since the last reset, the project/model quota may be stuck or another key/app in the same project may have consumed it.")
  elif kind=="minute":
   st.warning("Gemini's per-minute rate limit was reached. Wait about 60 seconds, then retry — this is not the daily quota.")
  else:
   reset=_quota_reset_context()
   st.error("Gemini returned a quota/rate-limit error, but did not clearly identify whether it is the minute or daily limit.")
   st.info(f"If it is the daily RPD limit, Google's next Pacific-midnight reset is about {reset.strftime('%H:%M')} Morocco time on {reset.strftime('%d %b')}.")
  with st.expander("Gemini error details"):
   st.code(m)
 elif "503" in l or "overloaded" in l: st.warning("Gemini is temporarily overloaded. Try again later.")
 else: st.error(f"Generation failed: {m}")

st.markdown('<div class="mq-section"><h3>Story brief</h3><span>STEP 01 · INPUT</span></div>',unsafe_allow_html=True)
with st.form("story_seed"):
 seed=st.text_input("Seed / working title",placeholder="e.g. The village that never sleeps")
 c1,c2=st.columns(2); mode_label=c1.selectbox("Story mode",list(STORY_MODES.keys()),index=0); origin=c2.selectbox("Origin",ORIGIN_OPTIONS,index=1)
 country_hint=st.text_input("Country / region hint",placeholder="Optional — leave blank for discovery")
 st.markdown('<div class="mq-card"><span class="mq-pill">LOCKED FORMAT</span><div class="mq-muted" style="margin-top:8px">Dark Vault · exactly 10 scenes · 60–65 sec · 9:16 · no narration · English + smaller Darija</div></div>',unsafe_allow_html=True)
 generate=st.form_submit_button("⚡ BUILD FULL BLUEPRINT",type="primary",use_container_width=True)

if generate:
 if not seed.strip(): st.error("Enter a seed/title first.")
 else:
  with st.status("MORQEVA is building the blueprint…",expanded=True) as status:
   usage_events=[]
   try:
    st.write("01 · Researching subject and verification boundaries")
    bp=generate_blueprint(api_key=api_key,model=model,seed=seed.strip(),story_mode=STORY_MODES[mode_label],origin_preference=origin,country_hint=country_hint.strip(),use_grounding=grounding_enabled,usage_sink=usage_events)
    st.write("02 · Building hooks, narrative arc and 10 production scenes")
    row=create_story({"seed":seed.strip(),"title":bp.final_title,"story_mode":bp.story_mode,"country":bp.country,"status":"BLUEPRINT_REVIEW","blueprint":bp.model_dump(mode="json"),"production":production_defaults(bp.model_dump(mode="json")),"performance":{"ai_usage":summarize_ai_usage(usage_events)}})
    st.session_state["active_story_id"]=row["id"]; st.session_state["active_blueprint"]=bp.model_dump(mode="json"); status.update(label=f"{content_id(row)} · blueprint ready",state="complete")
   except Exception as exc: status.update(label="Generation stopped",state="error"); show_generation_error(exc)

if "active_blueprint" in st.session_state and "active_story_id" in st.session_state:
 bp=StoryBlueprint.model_validate(st.session_state["active_blueprint"]); story_id=st.session_state["active_story_id"]
 st.markdown('<div class="mq-section"><h3>Blueprint workspace</h3><span>STEP 02 · REVIEW</span></div>',unsafe_allow_html=True)
 st.markdown(f'<div class="mq-card"><span class="mq-pill">{html.escape(content_id(story_id))}</span><span class="mq-pill">{html.escape(bp.story_mode.replace("_"," ").title())}</span><h2 style="margin:.7rem 0 .3rem">{html.escape(bp.final_title)}</h2><div class="mq-muted">{html.escape(bp.country or "")}</div></div>',unsafe_allow_html=True)
 tabs=st.tabs(["Overview","Hooks","10 Scenes","Sources","API"])
 with tabs[0]:
  render_research(bp); st.markdown('<div class="mq-section"><h3>Creative direction</h3><span>VISUAL SYSTEM</span></div>',unsafe_allow_html=True); st.info(f"Visual bible: {bp.visual_bible}\n\nMusic: {bp.music_direction}\n\nCaptions: {bp.caption_direction}")
 with tabs[1]:
  chosen=render_hook_picker(bp,f"story_{story_id}")
  if chosen!=bp.selected_hook_index: bp.selected_hook_index=chosen; st.session_state["active_blueprint"]=bp.model_dump(mode="json"); update_story(story_id,{"blueprint":bp.model_dump(mode="json")})
  if st.button("↻ Regenerate 5 hooks",key=f"rehooks_{story_id}",use_container_width=True):
   usage_events=[]
   try:
    bp.hooks=regenerate_hooks(api_key,model,bp,usage_sink=usage_events); bp.recommended_hook_index=max(range(5),key=lambda i:bp.hooks[i].score); bp.selected_hook_index=bp.recommended_hook_index; st.session_state["active_blueprint"]=bp.model_dump(mode="json"); update_story(story_id,{"blueprint":bp.model_dump(mode="json")}); record_ai_usage(story_id,usage_events); st.rerun()
   except Exception as exc: show_generation_error(exc)
 with tabs[2]:
  st.caption(f"Master timing · {bp.total_duration_seconds:.1f}s · exactly 10 scenes")
  for scene in bp.scenes:
   render_scene(scene,expanded=scene.scene_number==1)
   if st.button(f"↻ Regenerate Scene {scene.scene_number}",key=f"regen_{story_id}_{scene.scene_number}"):
    usage_events=[]
    try:
     bp.scenes[scene.scene_number-1]=regenerate_scene(api_key,model,bp,scene.scene_number,usage_sink=usage_events); bp=StoryBlueprint.model_validate(bp.model_dump()); st.session_state["active_blueprint"]=bp.model_dump(mode="json"); update_story(story_id,{"blueprint":bp.model_dump(mode="json")}); record_ai_usage(story_id,usage_events); st.rerun()
    except Exception as exc: show_generation_error(exc)
 with tabs[3]: render_sources(bp)
 with tabs[4]: render_ai_usage((get_story(story_id) or {}).get("performance") or {})
 st.markdown('<div class="mq-section"><h3>Approval gate</h3><span>STEP 03 · RELEASE</span></div>',unsafe_allow_html=True)
 c1,c2=st.columns([3,1])
 if c1.button("✓ APPROVE BLUEPRINT → PRODUCTION",type="primary",use_container_width=True):
  update_story(story_id,{"title":bp.final_title,"country":bp.country,"blueprint":bp.model_dump(mode="json"),"production":production_defaults(bp.model_dump(mode="json")),"status":"PRODUCTION"}); st.success(f"{content_id(story_id)} moved to Production.")
 with c2.popover("Delete story",use_container_width=True):
  st.warning(f"Delete {content_id(story_id)} permanently?")
  confirm=st.checkbox("Yes, permanently delete it",key=f"confirm_delete_create_{story_id}")
  if st.button("Delete permanently",type="secondary",disabled=not confirm,key=f"delete_create_{story_id}",use_container_width=True):
   delete_story_local(story_id); st.session_state.pop("active_story_id",None); st.session_state.pop("active_blueprint",None); st.rerun()
