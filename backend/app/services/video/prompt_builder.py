from app.services.video.character_config import ROBOT_ANCHOR


def build_presenter_video_prompt(
    topic: str,
    visual_direction: str,
    ) -> str:
    return f"""
        Toru, the humanoid AI presenter from the reference image, sits behind
        the newsroom desk and looks naturally at the camera.

        Use subtle natural motion: blinking, small head movements,
        gentle hand gestures, and relaxed upper-body movement.

        Toru appears cheerful, warm, curious, and confident.
        Preserve Toru's identity, face, navy suit, studio, lighting,
        framing, and colors from the reference image.

        Topic: {topic}

        Background display:
        {visual_direction}

        Keep Toru as the main subject.
        Use smooth, realistic motion.
        No text, logos, extra people, or appearance changes.
        """.strip()

def build_scene_video_prompt(
    topic: str,
    scene: dict,
    ) -> str:
    presenter_action = scene["presenter_action"]
    background_action = scene["background_action"]
    camera_action = scene["camera_action"]

    prompt = f"""
    Toru, the humanoid AI presenter from the reference image,
    remains in the same technology newsroom.

    Presenter:
    {presenter_action}

    Background:
    {background_action}

    Camera:
    {camera_action}

    Preserve Toru's identity, face, navy suit, studio, lighting,
    framing style, and colors from the reference image.

    Topic: {topic}

    Use smooth, realistic motion.
    Toru should move naturally like a charismatic technology presenter.
    Keep gestures subtle and believable.

    No readable text, logos, extra people, or appearance changes.
    """.strip()

    if len(prompt) > 1000:
        raise ValueError(
            f"Scene prompt is too long: "
            f"{len(prompt)} characters."
        )

    return prompt