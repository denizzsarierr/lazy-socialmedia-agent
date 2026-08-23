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