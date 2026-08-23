from app.services.video.character_config import ROBOT_ANCHOR


def build_presenter_video_prompt(
    topic: str,
    visual_direction: str,
) -> str:
    character = ROBOT_ANCHOR

    return f"""
        Create a vertical short-form technology news video.

        PRESENTER:
        {character.appearance}

        FACE:
        {character.face}

        BODY:
        {character.body}

        PRESENTATION STYLE:
        {character.personality}

        STUDIO:
        {character.studio}

        CAMERA:
        {character.camera}

        LIGHTING:
        {character.lighting}

        VISUAL STYLE:
        {character.visual_style}

        CURRENT TOPIC:
        {topic}

        SCENE DIRECTION:
        The presenter is seated behind the newsroom desk.
        The presenter looks directly into the camera and makes subtle,
        natural robotic gestures while presenting the topic.

        The display behind the presenter should visually relate to:
        {visual_direction}

        Keep the presenter as the main subject.
        Background visuals should support the topic without becoming distracting.

        CONSISTENCY RULES:
        {character.negative_rules}
        """.strip()