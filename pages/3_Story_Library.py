import html
import pandas as pd
import streamlit as st
from ai.story_engine import regenerate_hooks,regenerate_scene
from components.story_ui import render_hook_picker,render_research,render_scene,render_sources
from data.store import load_stories,content_id,update_story,record_ai_usage,delete_story,delete_all_stories
from models.story_blueprint import StoryBlueprint
from utils.helpers import cloud_guard,page_header,status_label,production_defaults

cloud_guard(); page_header("Story Library","Browse every MORQEVA story, status and production blueprint from one vault.","MORQEVA · STORY VAULT")
stories=load_stories()
if not stories: st.info("No stories yet. Create the first one from Create Story."); st.stop()

st.markdown('<div class="mq-section"><h3>Vault overview</h3><span>ALL STORIES</span></div>',unsafe_allow_html=True)
cols=st.columns(3)
for n,story in enumerate(stories[:6]):
 bp=story.get("blueprint") or {}; prod=story.get("production") or {}; scenes=prod.get("scenes") or {}; approved=sum(bool(v.get("approved")) for v in scenes.values()) if scenes else 0; progress=approved*10 if scenes else (15 if story.get("status")=="BLUEPRINT_REVIEW" else 0)
 with cols[n%3]: st.markdown(f'''<div class="mq-story"><span class="mq-pill">{html.escape(content_id(story))}</span><span class="mq-pill">{html.escape(status_label(story.get('status','')))}</span><h4>{html.escape(story.get('title','Untitled'))}</h4><div class="mq-muted">{html.escape(bp.get('country',story.get('country','')) or 'Dark Vault')} · {progress}%</div><div class="mq-progress"><i style="width:{progress}%"></i></div></div>''',unsafe_allow_html=True)

with st.popover("Vault actions"):
 st.caption("Permanent actions")
 confirm_all=st.checkbox("I want to permanently delete every story",key="confirm_delete_all")
 if st.button("Delete ALL stories",disabled=not confirm_all,use_container_width=True):
  delete_all_stories(); st.session_state.pop("active_story_id",None); st.session_state.pop("active_blueprint",None); st.success("Vault cleared."); st.rerun()

st.markdown('<div class="mq-section"><h3>Open story</h3><span>DETAILED WORKSPACE</span></div>',unsafe_allow_html=True)
labels=[f"{content_id(s)} · {s.get('title','Untitled')} · {status_label(s.get('status',''))}" for s in stories]
selected=st.selectbox("Select story",range(len(stories)),format_func=lambda i:labels[i]); story=stories[selected]; bp_raw=story.get("blueprint") or {}
if not bp_raw: st.warning("This record has no blueprint yet."); st.stop()
bp=StoryBlueprint.model_validate(bp_raw); prod=story.get("production") or {}; approved=sum(bool(v.get("approved")) for v in (prod.get("scenes") or {}).values()) if prod else 0
st.markdown(f'''<div class="mq-card"><span class="mq-pill">{html.escape(content_id(story))}</span><span class="mq-pill">{html.escape(status_label(story.get('status','')))}</span><h2 style="margin:.7rem 0 .3rem">{html.escape(bp.final_title)}</h2><div class="mq-muted">{html.escape(bp.country or '')} · {approved}/10 scenes approved</div></div>''',unsafe_allow_html=True)

def render_ai_usage(performance):
 usage=(performance or {}).get("ai_usage") or {}
 if not usage: st.caption("Usage tracking starts with the next AI generation for this story."); return
 c1,c2,c3,c4=st.columns(4); c1.metric("Calls",int(usage.get("calls",0) or 0)); c2.metric("Input",f"{int(usage.get('input_tokens',0) or 0):,}"); c3.metric("Output",f"{int(usage.get('billed_output_tokens',0) or 0):,}"); c4.metric("Cached",f"{int(usage.get('cached_tokens',0) or 0):,}")
 st.caption(f"Thinking {int(usage.get('thought_tokens',0) or 0):,} · Search {int(usage.get('search_requests',0) or 0)} · Est. cost ${float(usage.get('estimated_cost_usd',0) or 0):.4f}")

t1,t2,t3,t4,t5=st.tabs(["Overview","Hooks","10 Scenes","Sources","API"])
with t1: render_research(bp)
with t2:
 recommended=bp.recommended_hook_index; st.success(f"Recommended hook #{recommended+1}: {bp.hooks[recommended].text}"); chosen=render_hook_picker(bp,key_prefix=f"library_{story['id']}"); c1,c2=st.columns(2)
 if c1.button("✓ Use selected hook",key=f"use_hook_{story['id']}",type="primary",use_container_width=True):
  try:
   api_key=str(st.secrets["GEMINI_API_KEY"]); model=str(st.secrets.get("GEMINI_MODEL","gemini-3.6-flash")); bp.selected_hook_index=chosen; usage_events=[]; bp.scenes[0]=regenerate_scene(api_key,model,bp,1,usage_sink=usage_events); bp=StoryBlueprint.model_validate(bp.model_dump()); update_story(story["id"],{"blueprint":bp.model_dump(mode="json")}); record_ai_usage(story["id"],usage_events); st.rerun()
  except Exception as exc: st.error(f"Could not apply hook: {exc}")
 if c2.button("↻ Regenerate hooks",key=f"regen_hooks_{story['id']}",use_container_width=True):
  try:
   api_key=str(st.secrets["GEMINI_API_KEY"]); model=str(st.secrets.get("GEMINI_MODEL","gemini-3.6-flash")); usage_events=[]; bp.hooks=regenerate_hooks(api_key,model,bp,usage_sink=usage_events); bp.recommended_hook_index=max(range(5),key=lambda i:bp.hooks[i].score); bp.selected_hook_index=bp.recommended_hook_index; update_story(story["id"],{"blueprint":bp.model_dump(mode="json")}); record_ai_usage(story["id"],usage_events); st.rerun()
  except Exception as exc: st.error(f"Hook regeneration failed: {exc}")
with t3:
 for s in bp.scenes: render_scene(s)
with t4: render_sources(bp)
with t5: render_ai_usage(story.get("performance") or {})

current_status=story.get("status","")
st.markdown('<div class="mq-section"><h3>Workflow action</h3><span>CURRENT STAGE</span></div>',unsafe_allow_html=True)
c1,c2=st.columns([3,1])
with c1:
 if current_status=="BLUEPRINT_REVIEW":
  if st.button("✓ APPROVE BLUEPRINT → PRODUCTION",type="primary",use_container_width=True,key=f"approve_{story['id']}"):
   update_story(story["id"],{"title":bp.final_title,"country":bp.country,"blueprint":bp.model_dump(mode="json"),"production":production_defaults(bp.model_dump(mode="json")),"status":"PRODUCTION"}); st.rerun()
 else: st.success(f"Current stage: {status_label(current_status)}")
with c2:
 with st.popover("Delete story",use_container_width=True):
  st.warning(f"Delete {content_id(story)} permanently?")
  confirm=st.checkbox("Yes, permanently delete it",key=f"confirm_delete_library_{story['id']}")
  if st.button("Delete permanently",disabled=not confirm,key=f"delete_library_{story['id']}",use_container_width=True):
   delete_story(story["id"]); st.session_state.pop("active_story_id",None); st.session_state.pop("active_blueprint",None); st.success("Story deleted."); st.rerun()
