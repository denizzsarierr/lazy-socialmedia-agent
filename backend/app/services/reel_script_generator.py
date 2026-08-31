import json
import os

from openai import OpenAI


class ReelScriptGenerator:
    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

        self.model = os.getenv(
            "OPENAI_TEXT_MODEL",
            "gpt-5.6-luna",
        )

    def generate(
        self,
        category: str,
        topic: str,
        caption: str,
    ) -> dict:
        prompt = f"""
            You are writing a short Instagram Reel script for Toru,
            a humanoid AI technology presenter.

            CATEGORY:
            {category}

            TOPIC:
            {topic}

            SOURCE CONTENT / CAPTION:
            {caption}

            SCRIPT RULES:

            - English only.
            - Approximately 35-50 spoken words.
            - Aim for roughly 15-20 seconds of speech.
            - Start with a strong, natural hook.
            - Make the viewer curious within the first sentence.
            - Explain ONE interesting idea clearly.
            - Use short, conversational sentences.
            - Prefer everyday spoken English over academic language.
            - Use contractions naturally when appropriate.
            - Make the script sound good when spoken aloud.
            - Keep the energy upbeat and engaging.
            - A small playful or witty line is welcome when it fits naturally.
            - Accuracy is more important than humor.
            - Do not invent facts beyond the supplied content.
            - Avoid unnecessary technical jargon.
            - Avoid awkward invented-sounding adjectives such as "draggy".
            - Prefer natural spoken English even when simplifying technical concepts.
            - Avoid clickbait.
            - Avoid corporate language.
            - Avoid motivational language.
            - Do not say "Hey guys".
            - Do not ask viewers to like, follow, comment, or subscribe.
            - Do not include stage directions.
            - Do not use emojis.
            - Do not mention that Toru is an AI unless it is genuinely relevant
            to the topic.
            - Do not force a joke into every script.

            IMPORTANT:

            The script should sound like something a real charismatic presenter
            would naturally say to a camera.

            Do not simply summarize the background content.
            Rewrite the idea specifically for short-form spoken video.

            Also return a visual_direction field.

            The visual direction must NOT introduce topic-specific visuals.

            Toru already exists in a fixed technology newsroom.
            Keep the existing newsroom background unchanged and visually stable.

            Do not request new screens, interfaces, diagrams, icons, symbols,
            holograms, text, logos, charts, images, or additional objects.

            The visual_direction should simply describe maintaining the existing
            studio with subtle ambient movement only.

            Return ONLY valid JSON using exactly this structure:

            {{
                "hook": "...",
                "script": "...",
                "visual_direction": "..."
            }}
            """

        response = self.client.responses.create(
            model=self.model,
            input=prompt,
        )

        result = json.loads(
            response.output_text
        )

        return result