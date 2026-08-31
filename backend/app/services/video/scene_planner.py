import json
import os

from openai import OpenAI


class ScenePlanner:
    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

        self.model = os.getenv(
            "OPENAI_TEXT_MODEL",
            "gpt-5.6-luna",
        )

    def plan(
        self,
        topic: str,
        script: str,
        visual_direction: str,
        clip_count: int,
    ) -> list[dict]:

        prompt = f"""
            You are planning subtle continuous video scenes for Toru,
            a humanoid AI technology presenter.

            Toru is seated in a modern technology newsroom and presents
            short Instagram Reels about AI, technology, aviation,
            and aerospace.

            TOPIC:
            {topic}

            FULL SPOKEN SCRIPT:
            {script}

            NUMBER OF VIDEO CLIPS:
            {clip_count}

            Create exactly {clip_count} sequential scenes.

            IMPORTANT STYLE:

            The newsroom already exists in the reference image.
            Do NOT visually explain the topic using the background.

            The goal is not dramatic animation.
            The goal is to make Toru look naturally alive while
            preserving strong visual continuity.

            PRESENTER RULES:

            - Toru remains seated.
            - Use only small, natural presenter movements.
            - Small hand gestures are allowed.
            - Slight head turns or nods are allowed.
            - Slight upper-body movement is allowed.
            - Avoid large arm movements.
            - Avoid crossing hands or complicated hand interactions.
            - Avoid sudden pose changes.
            - Avoid exaggerated facial expressions.
            - Movement should continue naturally from the previous clip.

            CAMERA RULES:

            - Camera movement must be extremely subtle.
            - Prefer a very slow push-in, tiny horizontal drift,
            or almost static camera.
            - Never reset the camera angle.
            - Never make dramatic zooms.
            - Never orbit around Toru.
            - Never change to another shot or viewpoint.

            BACKGROUND RULES:

            - Keep the existing newsroom unchanged.
            - Background should remain almost static.
            - Do not introduce new objects.
            - Do not introduce screens.
            - Do not introduce UI.
            - Do not introduce diagrams.
            - Do not introduce icons or symbols.
            - Do not introduce text or logos.
            - Do not introduce holograms.
            - Do not introduce topic-specific graphics.
            - Do not introduce extra people.

            CONTINUITY:

            Every clip begins from the final frame of the previous clip.

            Therefore movements must be compatible with the pose and
            camera position already present in the reference frame.

            Avoid describing a specific starting pose that could conflict
            with the reference image.

            Use different but very subtle presenter movements between
            clips.

            Example progression:

            Clip 1:
            small open-hand presenter gesture,
            very slow camera push-in.

            Clip 2:
            small gesture with the other hand,
            tiny horizontal camera drift.

            Clip 3:
            subtle head nod and relaxed hand movement,
            camera nearly static.

            Clip 4:
            small concluding gesture and natural eye contact,
            very slow subtle push-in.

            Return ONLY valid JSON with exactly this structure:

            {{
                "scenes": [
                    {{
                        "clip_number": 1,
                        "presenter_action": "...",
                        "background_action": "...",
                        "camera_action": "..."
                    }}
                ]
            }}

            For background_action always describe keeping the existing
            background unchanged with only minimal ambient movement.
            """

        response = self.client.responses.create(
            model=self.model,
            input=prompt,
        )

        data = json.loads(
            response.output_text
        )

        scenes = data["scenes"]

        if len(scenes) != clip_count:
            raise ValueError(
                f"Expected {clip_count} scenes, "
                f"received {len(scenes)}."
            )

        return scenes