import pandas as pd
import streamlit as st

from ai.story_engine import generate_blueprint, regenerate_hooks, regenerate_scene
from components.story_ui import render_hook_picker, render_research, render_scene, render_sources
from config.settings import STORY_MODES, ORIGIN_OPTIONS, TARGET_PLATFORMS
from data.store import create_story, update_story, content_id, get_story, record_ai_usage, summarize_ai_usage
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


def render_ai_usage(performance):
    usage = (performance or {}).get("ai_usage") or {}
    if not usage:
        st.caption("Gemini usage tracking starts with the next AI generation for this story.")
        return
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Gemini calls", int(usage.get("calls", 0) or 0))
    c2.metric("Input tokens", f"{int(usage.get('input_tokens', 0) or 0):,}")
    c3.metric("Cached tokens", f"{int(usage.get('cached_tokens', 0) or 0):,}")
    c4.metric("Billed output", f"{int(usage.get('billed_output_tokens', 0) or 0):,}")
    c5.metric("Est. API cost", f"${float(usage.get('estimated_cost_usd', 0) or 0):.4f}")
    st.caption(
        f"Total tokens: {int(usage.get('total_tokens', 0) or 0):,} · "
        f"Thinking: {int(usage.get('thought_tokens', 0) or 0):,} · "
        f"Cached: {int(usage.get('cached_tokens', 0) or 0):,} · "
        f"Grounded Search calls: {int(usage.get('search_requests', 0) or 0)}"
    )
    events = usage.get("events") or []
    if events:
        with st.expander("API usage details", expanded=False):
            frame = pd.DataFrame(events)
            cols = [c for c in ["operation", "model", "input_tokens", "cached_tokens", "output_tokens", "thought_tokens", "search_requests", "estimated_cost_usd"] if c in frame.columns]
            st.dataframe(frame[cols], use_container_width=True, hide_index=True)
    st.caption("Cached tokens are reported by Gemini when a cache hit is exposed in usage metadata. Cost is an estimate; your Google billing dashboard remains the source of truth.")


def show_generation_error(exc: Exception) -> None:
    message = str(exc)
    lowered = message.lower()
    if "429" in lowered or "quota" in lowered or "too_many_requests" in lowered or "resource_exhausted" in lowered:
        st.warning(
            "Gemini quota is temporarily exhausted. MORQEVA is OK — no story was created and nothing was lost. "
            "Wait for the quota window to reset or enable Gemini API billing, then press Generate once. Repeated clicks will not help."
        )
        st.caption("Quota protection: generation stopped immediately instead of continuing with more AI work.")
    elif "503" in lowered or "unavailable" in lowered or "overloaded" in lowered:
        st.warning("Gemini is temporarily unavailable/overloaded. MORQEVA is OK. Try again later.")
    else:
        st.error(f"Generation could not complete: {message}")


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
            usage_events = []
            try:
                bp = generate_blueprint(
                    api_key=api_key,
                    model=model,
                    seed=seed.strip(),
                    story_mode=STORY_MODES[mode_label],
                    origin_preference=origin,
                    country_hint=country_hint.strip(),
                    use_grounding=grounding_enabled,
                    usage_sink=usage_events,
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
                    "performance": {"ai_usage": summarize_ai_usage(usage_events)},
                })
                st.session_state["active_story_id"] = row["id"]
                st.session_state["active_blueprint"] = bp.model_dump(mode="json")
                status.update(label=f"{content_id(row)} blueprint ready", state="complete")
            except Exception as exc:
                status.update(label="Generation paused", state="error")
                show_generation_error(exc)

if "active_blueprint" in st.session_state and "active_story_id" in st.session_state:
    bp = StoryBlueprint.model_validate(st.session_state["active_blueprint"])
    story_id = st.session_state["active_story_id"]

    st.divider()
    st.markdown(f"## {content_id(story_id)} · {bp.final_title}")
    tabs = st.tabs(["Story & facts", "Hooks", "10 scenes", "Sources", "API usage"])

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
                usage_events = []
                try:
                    bp.hooks = regenerate_hooks(api_key, model, bp, usage_sink=usage_events)
                    bp.recommended_hook_index = max(range(5), key=lambda i: bp.hooks[i].score)
                    bp.selected_hook_index = bp.recommended_hook_index
                    st.session_state["active_blueprint"] = bp.model_dump(mode="json")
                    update_story(story_id, {"blueprint": bp.model_dump(mode="json")})
                    record_ai_usage(story_id, usage_events)
                    st.rerun()
                except Exception as exc:
                    show_generation_error(exc)

    with tabs[2]:
        st.caption(f"Master timing: {bp.total_duration_seconds:.1f}s across exactly 10 scenes")
        for scene in bp.scenes:
            render_scene(scene, expanded=scene.scene_number == 1)
            if st.button(f"↻ Regenerate Scene {scene.scene_number}", key=f"regen_{story_id}_{scene.scene_number}"):
                with st.spinner(f"Regenerating Scene {scene.scene_number}…"):
                    usage_events = []
                    try:
                        bp.scenes[scene.scene_number - 1] = regenerate_scene(api_key, model, bp, scene.scene_number, usage_sink=usage_events)
                        bp = StoryBlueprint.model_validate(bp.model_dump())
                        st.session_state["active_blueprint"] = bp.model_dump(mode="json")
                        update_story(story_id, {"blueprint": bp.model_dump(mode="json")})
                        record_ai_usage(story_id, usage_events)
                        st.rerun()
                    except Exception as exc:
                        show_generation_error(exc)

    with tabs[3]:
        render_sources(bp)

    with tabs[4]:
        live_story = get_story(story_id) or {}
        render_ai_usage(live_story.get("performance") or {})

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