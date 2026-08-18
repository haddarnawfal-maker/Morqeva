import streamlit as st

from ai.story_engine import generate_blueprint, regenerate_hooks, regenerate_scene
from components.story_ui import render_hook_picker, render_research, render_scene, render_sources
from config.settings import STORY_MODES, ORIGIN_OPTIONS, TARGET_PLATFORMS
from data.store import create_story, update_story, content_id
from models.story_blueprint import StoryBlueprint
from utils.helpers import cloud_guard, page_header, production_defaults

cloud_guard()
page_header("Create Story", "One seed in. Research, facts, 5 hooks, exactly 10 scenes, English/Darija captions, Flow prompts, motion prompts and SFX out.", "MORQEVA INTELLIGENCE")

try:
    api_key = str(st.secrets["GEMINI_API_KEY"])
    model = str(st.secrets.get("GEMINI_MODEL", "gemini-3.6-flash"))
    grounding_enabled = bool(st.secrets.get("ENABLE_GROUNDING", True))
except Exception:
    st.error("Add GEMINI_API_KEY to Streamlit Cloud Secrets before generating blueprints.")
    st.stop()

with st.form("story_seed"):
    seed = st.text_input("Story seed / title", placeholder="e.g. The graves Marrakech forgot for 250 years")
    c1, c2 = st.columns(2)
    mode_label = c1.selectbox("Story mode", list(STORY_MODES.keys()), index=0)
    origin = c2.selectbox("Origin", ORIGIN_OPTIONS, index=1)
    country_hint = st.text_input("Country / region hint (optional)", placeholder="Leave blank for MORQEVA to discover the strongest match")
    st.caption("Locked: Dark Vault · exactly 10 scenes · 60–65 sec · 9:16 · no narration · English + smaller Darija")
    generate = st.form_submit_button("⚡ Generate Full Blueprint", type="primary", use_container_width=True)

if generate:
    if not seed.strip():
        st.error("Enter a story seed/title first.")
    else:
        with st.status("MORQEVA is researching and building the production blueprint…", expanded=True) as status:
            st.write("Researching the subject and verification boundaries…")
            try:
                bp = generate_blueprint(
                    api_key=api_key,
                    model=model,
                    seed=seed.strip(),
                    story_mode=STORY_MODES[mode_label],
                    origin_preference=origin,
                    country_hint=country_hint.strip(),
                    use_grounding=grounding_enabled,
                )
                st.write("Generating 5 hooks and 10 production-ready scenes…")
                row = create_story({
                    "seed": seed.strip(),
                    "title": bp.final_title,
                    "story_mode": bp.story_mode,
                    "country": bp.country,
                    "status": "BLUEPRINT_REVIEW",
                    "blueprint": bp.model_dump(mode="json"),
                    "production": production_defaults(bp.model_dump(mode="json")),
                })
                st.session_state["active_story_id"] = row["id"]
                st.session_state["active_blueprint"] = bp.model_dump(mode="json")
                status.update(label=f"{content_id(row)} blueprint ready", state="complete")
            except Exception as exc:
                status.update(label="Generation failed", state="error")
                st.error(str(exc))

if "active_blueprint" in st.session_state and "active_story_id" in st.session_state:
    bp = StoryBlueprint.model_validate(st.session_state["active_blueprint"])
    story_id = st.session_state["active_story_id"]

    st.divider()
    st.markdown(f"## {content_id(story_id)} · {bp.final_title}")
    tabs = st.tabs(["Story & facts", "Hooks", "10 scenes", "Sources"])

    with tabs[0]:
        render_research(bp)
        st.markdown("**Visual bible**")
        st.write(bp.visual_bible)
        st.markdown("**Music direction**")
        st.write(bp.music_direction)
        st.markdown("**Caption direction**")
        st.write(bp.caption_direction)

    with tabs[1]:
        chosen = render_hook_picker(bp, f"story_{story_id}")
        if chosen != bp.selected_hook_index:
            bp.selected_hook_index = chosen
            st.session_state["active_blueprint"] = bp.model_dump(mode="json")
            update_story(story_id, {"blueprint": bp.model_dump(mode="json")})
        if st.button("↻ Regenerate 5 hooks", key=f"rehooks_{story_id}"):
            with st.spinner("Generating stronger hooks…"):
                bp.hooks = regenerate_hooks(api_key, model, bp)
                bp.recommended_hook_index = max(range(5), key=lambda i: bp.hooks[i].score)
                bp.selected_hook_index = bp.recommended_hook_index
                st.session_state["active_blueprint"] = bp.model_dump(mode="json")
                update_story(story_id, {"blueprint": bp.model_dump(mode="json")})
                st.rerun()

    with tabs[2]:
        st.caption(f"Master timing: {bp.total_duration_seconds:.1f}s across exactly 10 scenes")
        for scene in bp.scenes:
            render_scene(scene, expanded=scene.scene_number == 1)
            if st.button(f"↻ Regenerate Scene {scene.scene_number}", key=f"regen_{story_id}_{scene.scene_number}"):
                with st.spinner(f"Regenerating Scene {scene.scene_number}…"):
                    bp.scenes[scene.scene_number - 1] = regenerate_scene(api_key, model, bp, scene.scene_number)
                    bp = StoryBlueprint.model_validate(bp.model_dump())
                    st.session_state["active_blueprint"] = bp.model_dump(mode="json")
                    update_story(story_id, {"blueprint": bp.model_dump(mode="json")})
                    st.rerun()

    with tabs[3]:
        render_sources(bp)

    st.divider()
    if st.button("✓ Approve Blueprint → Production", type="primary", use_container_width=True):
        update_story(story_id, {
            "title": bp.final_title,
            "country": bp.country,
            "blueprint": bp.model_dump(mode="json"),
            "production": production_defaults(bp.model_dump(mode="json")),
            "status": "PRODUCTION",
        })
        st.success(f"{content_id(story_id)} is ready in Production.")
