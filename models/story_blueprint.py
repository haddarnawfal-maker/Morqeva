from __future__ import annotations

from typing import List, Literal
from pydantic import BaseModel, Field, model_validator

FactLabel = Literal["VERIFIED", "FOLKLORE", "UNVERIFIED", "FICTION"]
StoryMode = Literal["VERIFIED_REAL", "FOLKLORE", "FICTIONAL_LEGEND"]


class Source(BaseModel):
    index: int
    title: str
    url: str
    domain: str = ""


class FactItem(BaseModel):
    claim: str
    label: FactLabel
    confidence: int = Field(ge=0, le=100)
    source_indices: List[int] = Field(default_factory=list)


class HookOption(BaseModel):
    text: str
    score: int = Field(ge=1, le=100)
    why_it_works: str


class SceneBlueprint(BaseModel):
    scene_number: int = Field(ge=1, le=10)
    duration_seconds: float = Field(ge=4.5, le=8.0)
    purpose: str
    english_caption: str
    darija_caption: str
    visual_summary: str
    flow_image_prompt: str
    vibes_motion_prompt: str
    symphony_fallback_prompt: str
    sfx: List[str] = Field(default_factory=list)
    music_cue: str = ""
    fact_label: FactLabel = "UNVERIFIED"
    source_indices: List[int] = Field(default_factory=list)


class StoryBlueprint(BaseModel):
    seed: str
    final_title: str
    story_mode: StoryMode
    category: str
    country: str
    location: str
    era: str
    topic: str
    premise: str
    original_angle: str
    verification_summary: str
    visual_bible: str
    facts: List[FactItem]
    hooks: List[HookOption] = Field(min_length=5, max_length=5)
    recommended_hook_index: int = Field(ge=0, le=4)
    selected_hook_index: int = Field(default=0, ge=0, le=4)
    scenes: List[SceneBlueprint] = Field(min_length=10, max_length=10)
    music_direction: str
    caption_direction: str
    total_duration_seconds: float = 62.0
    sources: List[Source] = Field(default_factory=list)

    @model_validator(mode="after")
    def normalize_master_format(self):
        if len(self.scenes) != 10:
            raise ValueError("MORQEVA master format requires exactly 10 scenes")

        # Always keep stable numbering and normalize timing to exactly 62s.
        for idx, scene in enumerate(self.scenes, start=1):
            scene.scene_number = idx

        raw_total = sum(max(scene.duration_seconds, 0.1) for scene in self.scenes)
        target = 62.0
        if raw_total <= 0:
            for scene in self.scenes:
                scene.duration_seconds = 6.2
        else:
            factor = target / raw_total
            running = 0.0
            for scene in self.scenes[:-1]:
                scene.duration_seconds = round(max(4.5, min(8.0, scene.duration_seconds * factor)), 1)
                running += scene.duration_seconds
            self.scenes[-1].duration_seconds = round(target - running, 1)
            if not 4.5 <= self.scenes[-1].duration_seconds <= 8.0:
                # Fallback: fixed master timing.
                for scene in self.scenes:
                    scene.duration_seconds = 6.2

        self.total_duration_seconds = round(sum(s.duration_seconds for s in self.scenes), 1)
        return self
