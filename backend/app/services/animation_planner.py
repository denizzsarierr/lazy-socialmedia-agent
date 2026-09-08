import json
import os

from openai import OpenAI


ALLOWED_POSES = {
    "idle",
    "explain",
    "wave",
}


class AnimationPlanner:
    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=os.getenv(
                "OPENAI_API_KEY"
            )
        )

        self.model = os.getenv(
            "OPENAI_TEXT_MODEL",
            "gpt-5.6-luna",
        )

    def generate(
        self,
        script: str,
        duration: float,
        words: list[dict],
    ) -> list[dict]:

        word_timing_text = "\n".join(
            (
                f"{word['start']:.2f}-"
                f"{word['end']:.2f}: "
                f"{word['word']}"
            )
            for word in words
        )

        prompt = f"""
            You are directing Toru, a 2D animated presenter
            for a short Instagram Reel.

            SCRIPT:
            {script}

            TOTAL AUDIO DURATION:
            {duration:.2f} seconds

            WORD TIMESTAMPS:
            {word_timing_text}

            AVAILABLE POSES:

            idle
            - Neutral presenter pose.
            - Best for hooks, normal speaking and calm statements.

            explain
            - One hand extended in a presenting gesture.
            - Use when Toru is explaining an important idea,
            contrast, fact, mechanism or key point.

            wave
            - Friendly raised-hand gesture.
            - Primarily intended for the ending.
            - Use sparingly.

            TASK:

            Create a natural animation timeline for the presenter.

            RULES:

            - Cover the COMPLETE audio from 0.00 to {duration:.2f}.
            - Every scene must start exactly when the previous one ends.
            - Never leave gaps.
            - Never overlap scenes.
            - Use ONLY: idle, explain, wave.
            - Do not create rapid pose changes.
            - Most poses should last at least 3 seconds.
            - Prefer 3 to 6 total scenes for a 15-25 second Reel.
            - Do not alternate poses unnecessarily.
            - The animation should feel calm and intentional.
            - Use the meaning of the spoken script to decide
            when an explain gesture is appropriate.
            - idle should be the default pose.
            - Avoid using wave in the middle of an explanation.
            - wave may be used near the ending if natural.
            - Do not create facial expressions.
            - Mouth movement and blinking are handled elsewhere.
            - Times must be based on the supplied word timestamps.
            - Round timestamps to two decimal places.

            Return ONLY valid JSON with exactly this structure:

            {{
                "scenes": [
                    {{
                        "start": 0.0,
                        "end": 4.2,
                        "pose": "idle"
                    }}
                ]
            }}
            """

        response = self.client.responses.create(
            model=self.model,
            input=prompt,
        )

        result = json.loads(
            response.output_text
        )

        scenes = result["scenes"]

        return self._validate_plan(
            scenes,
            duration,
        )

    def _validate_plan(
        self,
        scenes: list[dict],
        duration: float,
    ) -> list[dict]:

        if not scenes:
            raise ValueError(
                "Animation plan contains no scenes"
            )

        cleaned = []

        for scene in scenes:
            pose = scene["pose"]

            if pose not in ALLOWED_POSES:
                raise ValueError(
                    f"Invalid pose: {pose}"
                )

            cleaned.append(
                {
                    "start": float(
                        scene["start"]
                    ),
                    "end": float(
                        scene["end"]
                    ),
                    "pose": pose,
                }
            )

        # Force exact video boundaries.
        cleaned[0]["start"] = 0.0
        cleaned[-1]["end"] = duration

        # Remove tiny floating-point gaps between scenes.
        for index in range(
            1,
            len(cleaned),
        ):
            cleaned[index]["start"] = (
                cleaned[
                    index - 1
                ]["end"]
            )

        return cleaned