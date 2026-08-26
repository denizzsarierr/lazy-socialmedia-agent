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
You are planning video scenes for Toru, a humanoid AI
technology presenter.

Toru is seated in a modern technology newsroom and presents
short Instagram Reels about AI, technology, aviation,
and aerospace.

TOPIC:
{topic}

FULL SPOKEN SCRIPT:
{script}

GENERAL BACKGROUND VISUAL:
{visual_direction}

NUMBER OF VIDEO CLIPS:
{clip_count}

Create exactly {clip_count} sequential scenes.

Each scene will later become an approximately 5-second
image-to-video generation.

SCENE RULES:

- Toru must remain the main presenter.
- Keep the same newsroom environment.
- Keep camera changes subtle.
- Toru should use natural presenter gestures.
- Do not make Toru perform exaggerated movements.
- Do not introduce extra people.
- Do not add readable text or logos.
- Avoid repeating exactly the same movement in consecutive scenes.
- Background visuals should help explain the topic.
- Scenes must feel like parts of one continuous technology show.
- Keep directions concise because they will be used in video prompts.

Use this general progression when appropriate:

1. Hook:
   Toru engages the viewer.

2. Explanation:
   Toru naturally explains the concept.

3. Visual insight:
   Background visualization becomes more useful.

4. Conclusion:
   Toru returns focus toward the viewer with a warm,
   confident finish.

Adapt this progression if the number of clips is different.

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