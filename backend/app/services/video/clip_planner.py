import math
from dataclasses import dataclass


@dataclass(frozen=True)
class ClipPlan:
    clip_count: int
    clip_duration: int
    total_video_duration: int
    audio_duration: float


def plan_video_clips(
    audio_duration: float,
    clip_duration: int = 5,
) -> ClipPlan:
    if audio_duration <= 0:
        raise ValueError(
            "Audio duration must be greater than zero."
        )

    if clip_duration <= 0:
        raise ValueError(
            "Clip duration must be greater than zero."
        )

    clip_count = math.ceil(
        audio_duration / clip_duration
    )

    return ClipPlan(
        clip_count=clip_count,
        clip_duration=clip_duration,
        total_video_duration=clip_count * clip_duration,
        audio_duration=audio_duration,
    )