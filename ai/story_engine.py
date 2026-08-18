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
- VERIFIED_REAL: every factual claim must be supported by grounded research. Never embellish facts simply to make the story darker.
- FOLKLORE: real geography/history may be used, but legendary claims must remain explicitly framed as legend, oral tradition, disputed belief or unverified account.
- FICTIONAL_LEGEND: create an atmospheric fictional legend that feels culturally and geographically believable, but NEVER attach invented tragedies, diseases, rituals, crimes, disasters or supernatural events to a real named village, real person or real community.
- In FICTIONAL_LEGEND mode, prefer an unnamed or clearly fictional settlement. Never invent a precise historical date merely to create false credibility.
- Fictional captions must preserve ambiguity with natural phrases such as "it is said", "according to the story", "some say", "the legend claims", or "maybe".
- Do NOT create pseudo-scientific explanations such as mysterious frequencies, neurological phenomena, toxins, experiments or impossible medical conditions unless the user's seed specifically asks for that angle.
- For fictional legends, prefer human customs, unexplained behaviour, strange traditions, missing explanations and atmospheric mysteries over monsters or fake science.
- A fictional legend should leave the viewer wondering whether an old story could have existed, not believing that fabricated evidence has been verified.
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
- Every claim must be labeled VERIFIED, FOLKLORE, UNVERIFIED, or FICTION.
- VERIFIED = supported by grounded sources.
- FOLKLORE = a real existing legend, oral tradition or belief found in grounded sources.
- UNVERIFIED = a real-world claim found in research but not sufficiently established.
- FICTION = anything invented by MORQEVA for a Fictional Legend.
- NEVER label an AI-invented legend, local tale, ritual or belief as FOLKLORE.
- In FICTIONAL_LEGEND mode, use VERIFIED facts only for useful real-world cultural, geographic or architectural context.
- Do not generate irrelevant factual background simply to make fictional stories appear credible.
- source_indices may ONLY reference numbers from the actual grounded source index.
- Never invent a URL.

SCENES:
- Exactly 10 scenes.
- Total finished duration is 62 seconds.
- Tell ONE coherent story with escalation; do not create 10 disconnected facts.
- Scene 1: immediate curiosity hook.
- Scene 2: establish the location/world.
- Scene 3: introduce the strange behaviour or mystery.
- Scene 4: deepen the pattern.
- Scene 5: show what inhabitants supposedly do or believe.
- Scene 6: introduce the rule/tradition/consequence.
- Scene 7: reveal the alleged origin or oldest version of the story.
- Scene 8: introduce uncertainty, contradiction or missing explanation.
- Scene 9: return to the present or show the mystery surviving.
- Scene 10: quiet, unsettling final thought with ambiguity. Never use a generic CTA.

CAPTIONS:
- English must sound cinematic, simple and immediately understandable.
- Usually 6–13 words per caption.
- Avoid academic wording and documentary jargon.
- Never write long explanatory sentences.
- For FICTIONAL_LEGEND, do not state invented claims as objective facts.
- Scene 1 or Scene 2 must clearly establish legendary ambiguity with wording such as "some say", "according to the story", "the legend says", or equivalent.
- After that framing is established, later captions may describe events more directly for cinematic flow.
- Do not repeat "it is said" mechanically in every scene.

DARIJA:
- Write genuinely natural Moroccan Darija using Latin/French letters and common numerals such as 3, 7 and 9 where natural.
- Never transliterate Modern Standard Arabic sentence structure.
- Never use formal Arabic vocabulary when an everyday Moroccan expression exists.
- The Darija should sound like something a Moroccan person would naturally say to a friend.
- Adapt the meaning rather than translating English word-for-word.
- Prefer forms such as: kaygolo, kayna, wa7ed, chi wa7ed, 7ed, b3d, nss lil, kayban, kayt7ka, ma 3arf 7ed.
- Keep every Darija caption short enough to read underneath the English caption.
- Do not use spellings like "moussafirin" or literary/formal Arabic phrasing.

VISUALS:
- Each Flow prompt must be directly paste-ready.
- 9:16 vertical, photorealistic cinematic documentary photography.
- Preserve one coherent location, architecture, weather, era, wardrobe and lighting language across all 10 scenes.
- Never place captions, logos or written text inside generated images.
- Do not make every scene another wide village shot. Alternate establishing shots, alleys, interiors, people, details, hands, windows, landscapes and close-ups.
- Vibes prompts must use subtle camera/environmental movement and preserve the original image.
- Symphony fallback prompts may use stronger controlled motion while explicitly preventing morphing and unwanted new objects.
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

HOOK REGENERATION RULES:
- Keep each hook short, cinematic and readable on a phone.
- Do not fabricate witnesses, traveler reports, dates, discoveries or evidence.
- If Mode is FICTIONAL_LEGEND, every hook must preserve ambiguity and clearly sound like a legend, rumor or story rather than a documented observation.
- Good FICTIONAL_LEGEND patterns include: "Some say...", "The story goes...", "According to an old tale...", "There is said to be...", or a clearly hypothetical question.
- Do not mechanically repeat the same opening phrase across all 5 hooks.
- Score honestly for scroll-stop strength.

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
Mode: {blueprint.story_mode}
Visual bible: {blueprint.visual_bible}
Selected hook: {blueprint.hooks[blueprint.selected_hook_index].text}
Existing scene: {existing.model_dump_json()}
Previous scene caption: {blueprint.scenes[scene_number-2].english_caption if scene_number > 1 else 'N/A'}
Next scene caption: {blueprint.scenes[scene_number].english_caption if scene_number < 10 else 'N/A'}

SCENE REGENERATION RULES:
- Strengthen the scene without changing the overall story arc.
- Do not invent unsupported factual claims, witnesses, traveler observations, dates or evidence.
- If Mode is FICTIONAL_LEGEND and this is Scene 1 or Scene 2, the English caption MUST explicitly preserve legendary ambiguity. Adapt the selected hook safely instead of copying it literally if the selected hook sounds too factual.
- For FICTIONAL_LEGEND, prefer wording such as "some say", "the story goes", "there is said to be", "according to the tale", or another natural ambiguity marker.
- English caption should normally be 6–13 words and easy to read quickly.

DARIJA REGENERATION RULES:
- Write natural everyday Moroccan Darija in Latin/French letters.
- Adapt meaning; never translate English word-for-word.
- Avoid formal Arabic/Moroccanized MSA words such as "moussafirin".
- Prefer natural forms such as: kaygolo, li kaydkhol, had l-wad, b3d nss lil, kayلاحظ, wa7ed l7aja, ghriba, 7ed ma kayna3s.
- Keep it short and conversational, as if a Moroccan person were telling the story to a friend.
- Use common numerals such as 3, 7 and 9 where natural.

VISUAL/MOTION RULES:
- Preserve the approved visual bible and image continuity.
- Flow prompt remains photorealistic, vertical 9:16, with no text/logo/watermark.
- Vibes motion should be subtle and preserve image structure.
- Symphony fallback may be stronger but must prevent morphing and unwanted new objects.

Return only one scene object.
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
