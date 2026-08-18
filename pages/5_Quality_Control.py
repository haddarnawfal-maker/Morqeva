import html
import streamlit as st
from data.store import load_stories,update_story,content_id
from models.story_blueprint import StoryBlueprint
from utils.helpers import cloud_guard,page_header
cloud_guard(); page_header("Quality Control","Final inspection gate before a MORQEVA master can publish.","MORQEVA · QC GATE")
stories=[s for s in load_stories() if s.get("status")=="QC"]
if not stories: st.markdown('<div class="mq-card"><span class="mq-pill mq-verified">QUEUE CLEAR</span><h3>No masters waiting for QC</h3><div class="mq-muted">Complete all 10 production scenes and send the master here.</div></div>',unsafe_allow_html=True); st.stop()
idx=st.selectbox("Master awaiting inspection",range(len(stories)),format_func=lambda i:f"{content_id(stories[i])} · {stories[i].get('title','')}"); story=stories[idx]; bp=StoryBlueprint.model_validate(story.get("blueprint") or {})
st.markdown(f'<div class="mq-card"><span class="mq-pill">{html.escape(content_id(story))}</span><span class="mq-pill mq-folklore">QC PENDING</span><h3>{html.escape(bp.final_title)}</h3><div class="mq-muted">10 scenes · target 60–65 sec · vertical 9:16 · no narration</div></div>',unsafe_allow_html=True)
checks=["Exactly 10 scenes, correctly ordered","Final runtime is 60–65 seconds","No narration / talking host","English primary caption + smaller Darija","Captions remain readable before cuts","Music supports mood without overpowering SFX","Scene-specific SFX present where useful","Visual style/location/characters remain coherent","No AI morphing, malformed anatomy, accidental text or watermarks","Claims respect VERIFIED / FOLKLORE / FICTION wording","Final export is 9:16, ideally 1080×1920"]
st.markdown('<div class="mq-section"><h3>Inspection checklist</h3><span>11 REQUIRED CHECKS</span></div>',unsafe_allow_html=True)
with st.form("qc"):
 results=[]
 for n,item in enumerate(checks,1): results.append(st.checkbox(f"{n:02d}  {item}",value=False))
 notes=st.text_area("Inspector notes",placeholder="Only note issues, corrections, or final observations...")
 passed=st.form_submit_button("✓ PASS QC · RELEASE MASTER",type="primary",use_container_width=True)
 if passed:
  if not all(results): st.error(f"QC blocked · {len(results)-sum(results)} required check(s) remain.")
  else: update_story(story["id"],{"status":"MASTER","production":{**(story.get("production") or {}),"qc_notes":notes}}); st.success("Master released to Distribution."); st.rerun()
