from __future__ import annotations

import json
from urllib.parse import urlparse
from typing import Dict, List, Tuple

from google import genai
from pydantic import TypeAdapter

from models.story_blueprint import StoryBlueprint, SceneBlueprint, HookOption, Source


MASTER_CONTEXT = """
You are MORQEVA, a Dark Vault content intelligence engine.
The output will become a faceless 9:16 short for TikTok, Instagram Reels and YouTube Shorts.

LOCKED MASTER RULES:
- Exactly 10 scenes.
- Total finished duration must be 60–65 seconds; target 62 seconds.
- No narration or talking host.
- Story is communicated with large English on-screen captions and a smaller natural Darija translation underneath.
- Darija must use Latin/French letters, not Arabic script.
- Captions must be short enough to read comfortably on a phone.
- Images are generated in Google Flow / Nano Banana 2 Lite.
- Every scene needs a highly detailed vertical 9:16 Flow prompt with NO text/logo/watermark inside the image.
- Every scene needs a concise Meta Vibes motion prompt that preserves the still image.
- Every scene needs a stronger TikTok Symphony fallback animation prompt.
- Sound is dark atmospheric music + scene-specific SFX. No voiceover.
- Visuals must feel cinematic, photorealistic and documentary-like, not generic AI horror.
- Maintain a single coherent visual world across all 10 scenes. Build a visual_bible and repeat its key continuity cues in prompts.
- The first scene must be a scroll-stopping hook. Scene 10 must leave a lingering final thought rather than a generic CTA.
- Do not hardcode horror clichés, monsters, glowing eyes or supernatural effects unless the source material truly calls for them.
- Do not invent factual claims in VERIFIED_REAL mode.
- In FOLKLORE mode, clearly distinguish documented history from oral legend or disputed claims.
- In FICTIONAL_LEGEND mode, the story may feel plausible, but wording must signal ambiguity ("it is said", "the story goes", "maybe") and must not impersonate documented historical evidence.
"""


def _client(api_key: str):
    return genai.Client(api_key=api_key)


def _extract_citations(interaction) -> List[Source]:
    found: Dict[str, Source] = {}
    try:
        for step in interaction.steps:
            if getattr(step, "type", None) != "model_output":
                continue
            for block in getattr(step, "content", []) or []:
                for ann in getattr(block, "annotations", []) or []:
                    if getattr(ann, "type", None) != "url_citation":
                        continue
                    url = getattr(ann, "url", "") or ""
                    if not url or url in found:
                        continue
                    title = getattr(ann, "title", "") or urlparse(url).netloc
                    domain = urlparse(url).netloc.replace("www.", "")
                    found[url] = Source(index=0, title=title, url=url, domain=domain)
    except Exception:
        return []

    sources = list(found.values())
    for idx, source in enumerate(sources, start=1):
        source.index = idx
    return sources


def _research_prompt(seed: str, story_mode: str, origin_preference: str, country_hint: str) -> str:
    return f"""
Research a candidate Dark Vault story for MORQEVA.

USER SEED / TITLE: {seed}
MODE: {story_mode}
ORIGIN PREFERENCE: {origin_preference}
COUNTRY / REGION HINT: {country_hint or 'None'}

Find the strongest, obscure, visually compelling subject that genuinely fits the seed. Avoid overused listicle topics.
For VERIFIED_REAL: prefer primary sources, government/cultural institutions, museums, academic sources, or strong reputable reporting. Clearly identify uncertain claims.
For FOLKLORE: research the real location/history and separate the legend from documented facts.

Return a concise research dossier containing:
- best matching subject/location
- dates/era
- 8–12 useful claims
- what is verified vs disputed/folklore
- details that must NOT be overstated
- why this story is visually strong for a 60–65 second 10-scene short
- an original angle that avoids generic "haunted place" framing
Do not write the final 10 scenes yet.
"""


def research_story(api_key: str, model: str, seed: str, story_mode: str, origin_preference: str, country_hint: str = "") -> Tuple[str, List[Source]]:
    client = _client(api_key)
    interaction = client.interactions.create(
        model=model,
        input=_research_prompt(seed, story_mode, origin_preference, country_hint),
        tools=[{"type": "google_search"}],
    )
    return interaction.output_text, _extract_citations(interaction)


def _source_index_text(sources: List[Source]) -> str:
    if not sources:
        return "No grounded URLs were returned. Do not invent source URLs."
    return "\n".join(f"[{s.index}] {s.title} — {s.url}" for s in sources)


def generate_blueprint(
    api_key: str,
    model: str,
    seed: str,
    story_mode: str,
    origin_preference: str,
    country_hint: str = "",
    use_grounding: bool = True,
) -> StoryBlueprint:
    research_text = ""
    sources: List[Source] = []

    if story_mode in {"VERIFIED_REAL", "FOLKLORE"}:
        if not use_grounding:
            raise RuntimeError("Verified/Folklore generation requires Google Search grounding to avoid unverified factual output.")
        research_text, sources = research_story(
            api_key=api_key,
            model=model,
            seed=seed,
            story_mode=story_mode,
            origin_preference=origin_preference,
            country_hint=country_hint,
        )
    else:
        research_text = (
            "This is an intentionally fictional legend. Do not invent citations or claim that invented details are documented. "
            "Use ambiguity and folklore-style wording throughout."
        )

    prompt = f"""
{MASTER_CONTEXT}

USER SEED: {seed}
MODE: {story_mode}
ORIGIN PREFERENCE: {origin_preference}
COUNTRY / REGION HINT: {country_hint or 'None'}

RESEARCH DOSSIER:
{research_text}

ACTUAL GROUNDED SOURCE INDEX:
{_source_index_text(sources)}

Create the complete MORQEVA production blueprint now.

HOOKS:
- Generate exactly 5 materially different hooks.
- Score each 1–100 for scroll-stop strength.
- Recommend the strongest one.

FACTS:
- Every factual claim must be labeled VERIFIED, FOLKLORE, UNVERIFIED, or FICTION.
- source_indices may ONLY reference numbers from the source index above.
- Never invent a URL.

SCENES:
- Exactly 10 scenes.
- Aim roughly 6.2 seconds each; total will be normalized to 62 seconds.
- Each English caption should usually be 5–14 words; split ideas across scenes rather than creating paragraphs.
- Darija must be natural Moroccan Darija in Latin/French letters and concise enough to sit underneath English.
- scene 1 must use the recommended hook or a condensed version of it.
- Each Flow image prompt must be detailed enough to paste directly into Flow, vertical 9:16, photorealistic, no text, and repeat continuity details from visual_bible.
- Vibes prompts should prioritize subtle realistic motion and image preservation.
- Symphony fallback prompts can request stronger controlled motion, but must preserve architecture/people/objects.
- Include 1–3 useful SFX per scene.

Return ONLY schema-valid structured output.
"""

    client = _client(api_key)
    interaction = client.interactions.create(
        model=model,
        input=prompt,
        response_format={
            "type": "text",
            "mime_type": "application/json",
            "schema": StoryBlueprint.model_json_schema(),
        },
    )
    blueprint = StoryBlueprint.model_validate_json(interaction.output_text)
    blueprint.sources = sources
    blueprint.seed = seed
    blueprint.story_mode = story_mode
    return blueprint


def regenerate_hooks(api_key: str, model: str, blueprint: StoryBlueprint) -> List[HookOption]:
    adapter = TypeAdapter(List[HookOption])
    prompt = f"""
{MASTER_CONTEXT}
Regenerate exactly 5 stronger, materially different hooks for this approved research summary.
Story title: {blueprint.final_title}
Premise: {blueprint.premise}
Original angle: {blueprint.original_angle}
Verification: {blueprint.verification_summary}
Mode: {blueprint.story_mode}
Return only 5 hook objects. Keep factual wording compatible with the story mode.
"""
    client = _client(api_key)
    interaction = client.interactions.create(
        model=model,
        input=prompt,
        response_format={"type": "text", "mime_type": "application/json", "schema": adapter.json_schema()},
    )
    return adapter.validate_json(interaction.output_text)


def regenerate_scene(api_key: str, model: str, blueprint: StoryBlueprint, scene_number: int) -> SceneBlueprint:
    existing = blueprint.scenes[scene_number - 1]
    prompt = f"""
{MASTER_CONTEXT}
Regenerate ONLY scene {scene_number} for this MORQEVA blueprint while preserving the rest of the story and visual continuity.
Title: {blueprint.final_title}
Premise: {blueprint.premise}
Visual bible: {blueprint.visual_bible}
Selected hook: {blueprint.hooks[blueprint.selected_hook_index].text}
Existing scene: {existing.model_dump_json()}
Previous scene caption: {blueprint.scenes[scene_number-2].english_caption if scene_number > 1 else 'N/A'}
Next scene caption: {blueprint.scenes[scene_number].english_caption if scene_number < 10 else 'N/A'}
Make it stronger without inventing unsupported factual claims. Return only one scene object.
"""
    client = _client(api_key)
    interaction = client.interactions.create(
        model=model,
        input=prompt,
        response_format={"type": "text", "mime_type": "application/json", "schema": SceneBlueprint.model_json_schema()},
    )
    scene = SceneBlueprint.model_validate_json(interaction.output_text)
    scene.scene_number = scene_number
    return scene
