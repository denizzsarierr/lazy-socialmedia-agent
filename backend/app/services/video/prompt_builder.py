from app.services.video.character_config import ROBOT_ANCHOR


def build_presenter_video_prompt(
        topic: str,
        visual_direction: str,
    ) -> str:
    return f"""
        Toru, the humanoid AI presenter from the reference image,
        remains in the exact same technology newsroom.

        Toru stays seated behind the desk and looks naturally toward
        the camera.

        Use only subtle realistic motion:
        small head movements, natural blinking, slight upper-body
        movement, and one gentle presenter hand gesture.

        Keep the camera almost static with only a very slow,
        subtle cinematic movement.

        Keep the existing background unchanged and nearly static.

        Preserve Toru's identity, face, navy suit, studio, lighting,
        composition, camera perspective, and colors.

        Topic: {topic}

        Do not add or change objects.
        Do not add screens, interfaces, diagrams, icons, symbols,
        text, logos, holograms, graphics, or extra people.

        Use subtle natural motion only.
        """.strip()


def build_scene_video_prompt(
        topic: str,
        scene: dict,
    ) -> str:

    presenter_action = scene["presenter_action"]
    camera_action = scene["camera_action"]

    prompt = f"""
        Toru continues naturally from the reference frame in the
        same technology newsroom.

        Presenter:
        {presenter_action}

        Camera:
        {camera_action}

        Keep the existing background unchanged and nearly static.

        Preserve Toru's identity, face, navy suit, studio, lighting,
        composition, camera perspective, and colors from the
        reference frame.

        Topic: {topic}

        Use only subtle realistic motion.
        Keep gestures small and natural.
        Maintain continuity with the reference frame.

        Do not add or change objects.
        Do not add screens, interfaces, diagrams, icons, symbols,
        text, logos, holograms, graphics, or extra people.
        Do not reset the camera or Toru's pose.
        """.strip()

    if len(prompt) > 1000:
        raise ValueError(
            f"Scene prompt is too long: "
            f"{len(prompt)} characters."
        )

    return prompt