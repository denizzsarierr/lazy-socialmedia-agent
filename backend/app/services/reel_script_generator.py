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
            You are writing a short Instagram Reel for Toru,
            an autonomous AI news presenter.

            The account covers:
            - artificial intelligence
            - technology
            - aviation and aerospace

            CATEGORY:
            {category}

            TOPIC:
            {topic}

            BACKGROUND CONTENT:
            {caption}

            Create a short spoken script for Toru.

            Requirements:

            - English only.
            - Approximately 35-50 spoken words.
            - Designed for roughly 15-20 seconds.
            - Start with an interesting hook.
            - Explain one useful idea clearly.
            - Sound natural when spoken aloud.
            - Professional but conversational.
            - Avoid hype and clickbait.
            - Avoid unnecessary technical jargon.
            - Do not say "Hey guys".
            - Do not ask viewers to like, follow, or subscribe.
            - Toru may occasionally acknowledge being an AI,
            but do NOT mention this in every video.
            - Do not invent facts not supported by the supplied content.
            - Do not include stage directions inside the spoken script.

            Also create a short visual direction describing what
            should appear on the newsroom display behind Toru.

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