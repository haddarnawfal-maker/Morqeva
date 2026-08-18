from __future__ import annotations

import pandas as pd
import streamlit as st

from models.story_blueprint import StoryBlueprint
from utils.helpers import fact_badge


def render_sources(bp: StoryBlueprint):
    if not bp.sources:
        st.warning("No grounded source URLs were returned.")
        return
    for source in bp.sources:
        st.markdown(f"**[{source.index}] {source.title}**  \n{source.url}")


def render_research(bp: StoryBlueprint):
    c1, c2, c3 = st.columns(3)
    c1.metric("Country", bp.country or "—")
    c2.metric("Era", bp.era or "—")
    c3.metric("Mode", bp.story_mode.replace("_", " ").title())
    st.markdown(f"**Topic:** {bp.topic}")
    st.markdown(f"**Premise:** {bp.premise}")
    st.markdown(f"**Original angle:** {bp.original_angle}")
    st.info(bp.verification_summary)

    with st.expander("Facts & verification", expanded=False):
        for fact in bp.facts:
            st.markdown(f"{fact_badge(fact.label)} {fact.claim}", unsafe_allow_html=True)
            if fact.source_indices:
                st.caption("Sources: " + ", ".join(f"[{i}]" for i in fact.source_indices))


def render_ai_usage(performance):
    usage = (performance or {}).get("ai_usage") or {}
    if not usage:
        st.caption("Gemini usage tracking starts with the next AI generation for this story.")
        return

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Gemini calls", int(usage.get("calls", 0) or 0))
    c2.metric("Input tokens", f"{int(usage.get('input_tokens', 0) or 0):,}")
    c3.metric("Billed output", f"{int(usage.get('billed_output_tokens', 0) or 0):,}")
    c4.metric("Est. API cost", f"${float(usage.get('estimated_cost_usd', 0) or 0):.4f}")

    st.caption(
        f"Total tokens: {int(usage.get('total_tokens', 0) or 0):,} · "
        f"Thinking: {int(usage.get('thought_tokens', 0) or 0):,} · "
        f"Grounded Search calls: {int(usage.get('search_requests', 0) or 0)}"
    )

    events = usage.get("events") or []
    if events:
        with st.expander("API usage details", expanded=False):
            st.dataframe(
                pd.DataFrame(events)[[
                    "operation", "model", "input_tokens", "output_tokens",
                    "thought_tokens", "search_requests", "estimated_cost_usd"
                ]],
                use_container_width=True,
                hide_index=True,
            )
    st.caption("Cost is an estimate from MORQEVA's configured Gemini model pricing; your Google billing dashboard remains the source of truth.")


def render_hook_picker(bp: StoryBlueprint, key_prefix: str = "hook") -> int:
    options = [f"{idx+1}. {h.text}  ·  {h.score}/100" for idx, h in enumerate(bp.hooks)]
    idx = st.radio(
        "Choose the hook used by the blueprint",
        range(len(options)),
        format_func=lambda i: options[i],
        index=bp.selected_hook_index,
        key=f"{key_prefix}_picker",
    )
    st.caption(bp.hooks[idx].why_it_works)
    return idx


def render_scene(scene, expanded: bool = False):
    title = f"Scene {scene.scene_number:02d} · {scene.duration_seconds:.1f}s · {scene.purpose}"
    with st.expander(title, expanded=expanded):
        st.markdown("**English caption**")
        st.write(scene.english_caption)
        st.markdown("**Darija**")
        st.caption(scene.darija_caption)
        st.markdown("**Visual direction**")
        st.write(scene.visual_summary)
        st.markdown("**FLOW — image prompt**")
        st.code(scene.flow_image_prompt, language="text")
        st.markdown("**VIBES — motion prompt**")
        st.code(scene.vibes_motion_prompt, language="text")
        st.markdown("**SYMPHONY — fallback motion prompt**")
        st.code(scene.symphony_fallback_prompt, language="text")
        if scene.sfx:
            st.markdown("**SFX:** " + " · ".join(scene.sfx))
        if scene.music_cue:
            st.caption("Music: " + scene.music_cue)
        st.markdown(f"{fact_badge(scene.fact_label)}", unsafe_allow_html=True)
        if scene.source_indices:
            st.caption("Sources: " + ", ".join(f"[{i}]" for i in scene.source_indices))


def capcut_dataframe(bp: StoryBlueprint):
    return pd.DataFrame([
        {
            "Scene": s.scene_number,
            "Time (s)": s.duration_seconds,
            "English": s.english_caption,
            "Darija": s.darija_caption,
            "SFX": ", ".join(s.sfx),
            "Music cue": s.music_cue,
        }
        for s in bp.scenes
    ])
