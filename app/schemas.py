from enum import Enum

from pydantic import BaseModel, Field


class StoryLength(str, Enum):
    short = "short"
    medium = "medium"
    long = "long"


class GenerateRequest(BaseModel):
    topic: str = Field(min_length=3, max_length=5000)
    length: StoryLength = StoryLength.medium
    voice: str = "alloy"
    style: str = "campfire"


class GenerateResponse(BaseModel):
    title: str
    story: str
    audio_url: str
    filename: str
