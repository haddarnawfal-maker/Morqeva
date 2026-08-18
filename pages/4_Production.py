import pandas as pd
import streamlit as st

from components.story_ui import capcut_dataframe
from config.settings import FLOW_URL, VIBES_URL, SYMPHONY_URL
from data.store import load_stories, update_story, content_id
from models.story_blueprint import StoryBlueprint
from utils.helpers import cloud_guard, page_header, production_defaults

cloud_guard()
page_header("Production", "Flow stills → Vibes first → Symphony fallback → CapCut master.", "MORQEVA STUDIO")
stories = [s for s in load_stories() if s.get("status") in {"PRODUCTION", "QC", "MASTER"}]
if not stories:
    st.info("No approved blueprints are waiting for production.")
    st.stop()

idx = st.selectbox("Story", range(len(stories)), format_func=lambda i: f"{content_id(stories[i])} · {stories[i].get('title','')}")
story = stories[idx]
bp = StoryBlueprint.model_validate(story.get("blueprint") or {})
production = story.get("production") or production_defaults(bp.model_dump(mode="json"))

st.markdown(f"## {content_id(story)} · {bp.final_title}")
a,b,c = st.columns(3)
a.link_button("Open Flow", FLOW_URL, use_container_width=True)
b.link_button("Open Meta Vibes", VIBES_URL, use_container_width=True)
c.link_button("Open TikTok Symphony", SYMPHONY_URL, use_container_width=True)

all_flow = "\n\n".join(f"SCENE {s.scene_number:02d}\n{s.flow_image_prompt}" for s in bp.scenes)
all_vibes = "\n\n".join(f"SCENE {s.scene_number:02d}\n{s.vibes_motion_prompt}" for s in bp.scenes)
all_sym = "\n\n".join(f"SCENE {s.scene_number:02d}\n{s.symphony_fallback_prompt}" for s in bp.scenes)

tab1, tab2, tab3, tab4 = st.tabs(["Scene tracker", "All Flow prompts", "All motion prompts", "CapCut sheet"])

with tab1:
    changed = False
    for scene in bp.scenes:
        key = str(scene.scene_number)
        state = production.setdefault("scenes", {}).setdefault(key, {})
        with st.expander(f"Scene {scene.scene_number:02d} · {scene.duration_seconds:.1f}s · {scene.english_caption}", expanded=scene.scene_number == 1):
            st.markdown("**FLOW prompt**")
            st.code(scene.flow_image_prompt, language="text")
            st.markdown("**Vibes motion**")
            st.code(scene.vibes_motion_prompt, language="text")
            st.markdown("**Symphony fallback**")
            st.code(scene.symphony_fallback_prompt, language="text")
            c1,c2,c3,c4 = st.columns(4)
            new_image = c1.checkbox("Flow image ✓", value=bool(state.get("image_done")), key=f"img_{story['id']}_{key}")
            new_anim = c2.checkbox("Animation ✓", value=bool(state.get("animation_done")), key=f"anim_{story['id']}_{key}")
            engine = c3.selectbox("Engine", ["Vibes", "Symphony", "Other"], index=["Vibes","Symphony","Other"].index(state.get("animation_engine","Vibes")) if state.get("animation_engine","Vibes") in ["Vibes","Symphony","Other"] else 0, key=f"eng_{story['id']}_{key}")
            approved = c4.checkbox("Scene approved ✓", value=bool(state.get("approved")), key=f"ok_{story['id']}_{key}")
            notes = st.text_input("Notes", value=state.get("notes", ""), key=f"notes_{story['id']}_{key}")
            new_state = {"image_done":new_image,"animation_done":new_anim,"animation_engine":engine,"approved":approved,"notes":notes}
            if new_state != state:
                production["scenes"][key] = new_state
                changed = True
    if changed:
        update_story(story["id"], {"production": production})

with tab2:
    st.code(all_flow, language="text")

with tab3:
    st.markdown("#### Vibes — primary")
    st.code(all_vibes, language="text")
    st.markdown("#### Symphony — fallback")
    st.code(all_sym, language="text")

with tab4:
    st.dataframe(capcut_dataframe(bp), use_container_width=True, hide_index=True)
    st.markdown("**Caption style:** " + bp.caption_direction)
    st.markdown("**Music:** " + bp.music_direction)

approved_count = sum(bool((production.get("scenes") or {}).get(str(i), {}).get("approved")) for i in range(1,11))
st.progress(approved_count/10, text=f"{approved_count}/10 scenes approved")
if approved_count == 10:
    if st.button("Send to Quality Control", type="primary", use_container_width=True):
        update_story(story["id"], {"status": "QC", "production": production})
        st.success("Sent to QC.")
        st.rerun()
