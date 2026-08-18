import pandas as pd
import streamlit as st

from ai.story_engine import regenerate_hooks, regenerate_scene
from components.story_ui import render_hook_picker, render_research, render_scene, render_sources
from data.store import load_stories, content_id, update_story
from models.story_blueprint import StoryBlueprint
from utils.helpers import cloud_guard, page_header, status_label, production_defaults

cloud_guard()
page_header("Story Library", "Every MORQEVA story and its complete intelligence blueprint in one cloud workspace.")
stories = load_stories()

if not stories:
    st.info("No stories yet. Create the first one from Create Story.")
    st.stop()

labels = [f"{content_id(s)} · {s.get('title','Untitled')} · {status_label(s.get('status',''))}" for s in stories]
selected = st.selectbox("Story", range(len(stories)), format_func=lambda i: labels[i])
story = stories[selected]
bp_raw = story.get("blueprint") or {}

if not bp_raw:
    st.warning("This record has no blueprint yet.")
    st.stop()

bp = StoryBlueprint.model_validate(bp_raw)
st.markdown(f"## {content_id(story)} · {bp.final_title}")
t1, t2, t3, t4 = st.tabs(["Research", "Hooks", "10 scenes", "Sources"])

with t1:
    render_research(bp)

with t2:
    recommended = bp.recommended_hook_index

    st.success(
        f"⭐ Recommended hook #{recommended + 1}: "
        f"{bp.hooks[recommended].text}"
    )

    chosen = render_hook_picker(
        bp,
        key_prefix=f"library_{story['id']}",
    )

    c1, c2 = st.columns(2)

    if c1.button(
        "✓ Use selected hook",
        key=f"use_hook_{story['id']}",
        type="primary",
        use_container_width=True,
    ):
        try:
            api_key = str(st.secrets["GEMINI_API_KEY"])
            model = str(st.secrets.get("GEMINI_MODEL", "gemini-3.6-flash"))

            bp.selected_hook_index = chosen

            with st.spinner("Applying the hook and rewriting Scene 1…"):
                bp.scenes[0] = regenerate_scene(
                    api_key,
                    model,
                    bp,
                    1,
                )

                bp = StoryBlueprint.model_validate(bp.model_dump())

                update_story(
                    story["id"],
                    {"blueprint": bp.model_dump(mode="json")},
                )

            st.success(
                f"Hook #{chosen + 1} selected and Scene 1 updated."
            )
            st.rerun()

        except Exception as exc:
            st.error(f"Could not apply hook: {exc}")

    if c2.button(
        "↻ Regenerate 5 hooks",
        key=f"regen_hooks_{story['id']}",
        use_container_width=True,
    ):
        try:
            api_key = str(st.secrets["GEMINI_API_KEY"])
            model = str(st.secrets.get("GEMINI_MODEL", "gemini-3.6-flash"))

            with st.spinner("Generating 5 stronger hooks…"):
                bp.hooks = regenerate_hooks(
                    api_key,
                    model,
                    bp,
                )

                bp.recommended_hook_index = max(
                    range(5),
                    key=lambda i: bp.hooks[i].score,
                )

                bp.selected_hook_index = bp.recommended_hook_index

                update_story(
                    story["id"],
                    {"blueprint": bp.model_dump(mode="json")},
                )

            st.rerun()

        except Exception as exc:
            st.error(f"Hook regeneration failed: {exc}")

with t3:
    for s in bp.scenes:
        render_scene(s)

with t4:
    render_sources(bp)

st.divider()
current_status = story.get("status", "")
if current_status == "BLUEPRINT_REVIEW":
    st.caption("Blueprint review complete? Send this story into the production tracker when the hook, scenes and prompts are ready.")
    if st.button("✓ Approve Blueprint → Production", type="primary", use_container_width=True, key=f"approve_{story['id']}"):
        update_story(
            story["id"],
            {
                "title": bp.final_title,
                "country": bp.country,
                "blueprint": bp.model_dump(mode="json"),
                "production": production_defaults(bp.model_dump(mode="json")),
                "status": "PRODUCTION",
            },
        )
        st.success(f"{content_id(story)} is now ready in Production.")
        st.rerun()
elif current_status in {"PRODUCTION", "QC", "MASTER"}:
    st.success(f"Current stage: {status_label(current_status)}")
