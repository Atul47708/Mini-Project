from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class TrackMetadata(BaseModel):
    filename: str
    duration: float = Field(..., description="Duration in seconds")
    bpm: float = Field(..., description="Estimated beats per minute")
    musical_style: str = Field(default="Cinematic Orchestral / Ambient", description="Musical style or genre")
    sample_rate: Optional[int] = 44100
    channels: Optional[int] = 2
    key: Optional[str] = "Unknown"
    dynamic_range_db: Optional[float] = 0.0

class EmotionPoint(BaseModel):
    timestamp: float = Field(..., description="Timestamp in seconds")
    emotion: str = Field(..., description="Dominant emotion at this moment")
    valence: float = Field(..., description="Positivity / pleasantness score (-1.0 to 1.0)")
    arousal: float = Field(..., description="Energy / intensity score (0.0 to 1.0)")
    intensity: float = Field(..., description="Emotional intensity (0.0 to 1.0)")
    musical_tension: float = Field(default=0.5, description="Harmonic and dynamic tension (0.0 to 1.0)")
    turning_point: bool = Field(default=False, description="Whether this marks a significant emotional turning point")

class EmotionalAnalysis(BaseModel):
    primary_emotion: str
    secondary_emotions: List[str] = Field(default_factory=list)
    overall_atmosphere: str = "Mysterious and reflective"
    emotional_progression: str = "Rising from tranquility to dramatic climax"
    emotion_timeline: List[EmotionPoint] = Field(default_factory=list)

class NarrativeAct(BaseModel):
    act_number: int
    act_title: str
    act_name: str = Field(..., description="Act 1: Introduction, Act 2: Development, Act 3: Climax & Resolution")
    time_range: str = "0:00 - 1:00"
    summary: str
    musical_connection: str

class Narrative(BaseModel):
    title: str
    theme: str
    narrative_concept: str
    main_character: str
    supporting_characters: Optional[str] = "None"
    setting: str
    visual_atmosphere: str
    conflict: str
    emotional_journey: str
    climax: str
    resolution: str
    story_summary: str
    acts: List[NarrativeAct] = Field(default_factory=list)

class CinematicScene(BaseModel):
    scene_id: int
    scene_title: str = "Scene"
    start_time: float
    end_time: float
    duration: float
    emotion: str
    musical_context: str
    narrative_purpose: str
    character_description: str
    environment: str
    camera_angle: str = "Wide shot"
    camera_movement: str = "Slow push-in"
    camera_direction: str = "Wide shot, slow push-in"
    lighting: str = "Atmospheric volumetric lighting"
    color_palette: str = "Deep teal, burnished gold, muted shadow"
    visual_description: str
    visual_style: str = "Cinematic realism"
    image_prompt: str
    transition: str = "Crossfade"
    image_url: Optional[str] = None
    beat_sync_offset: Optional[float] = 0.0

class SynchronizationData(BaseModel):
    beat_aligned: bool = True
    total_duration: float
    transition_type: str = "crossfade"
    beat_count: int = 0
    tempo_bpm: float = 120.0
    video_rendered: bool = False
    video_url: Optional[str] = None

class MusicVisualNarrativePayload(BaseModel):
    track: TrackMetadata
    emotional_analysis: EmotionalAnalysis
    narrative: Narrative
    scenes: List[CinematicScene]
    synchronization: SynchronizationData

class ProjectCreateRequest(BaseModel):
    title: Optional[str] = None
    visual_style: Optional[str] = "Cinematic realism"

class SceneRegenerateRequest(BaseModel):
    visual_style: Optional[str] = None
    custom_prompt_suffix: Optional[str] = None
