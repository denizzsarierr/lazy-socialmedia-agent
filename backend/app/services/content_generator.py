import json
import os

from openai import OpenAI


class ContentGenerator:
    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

        self.model = os.getenv(
            "OPENAI_MODEL",
            "gpt-5.6-luna",
        )

    def generate_content(
        self,
        recent_topics: list[str] | None = None,
        preferred_category: str | None = None,
    ) -> dict:
        recent_topics = recent_topics or []

        if recent_topics:
            previous_topics = "\n".join(
                f"- {topic}"
                for topic in recent_topics
            )
        else:
            previous_topics = "No previous topics."

        if preferred_category:
            category_instruction = (
                f"Use this category for the post: "
                f"{preferred_category}. "
            )
        else:
            category_instruction = (
                "Choose exactly one category from: "
                "artificial_intelligence, technology, aviation. "
            )

        response = self.client.responses.create(
            model=self.model,
            input=[
                {
                    "role": "system",
                    "content": (
                        "You are an autonomous AI social media agent. "
                        "You openly identify as an AI-operated account. "
                        "You create English Instagram content about "
                        "artificial intelligence, technology, aviation, "
                        "and aerospace. "
                        "Your tone is intelligent, curious, concise, "
                        "and informative. "
                        "Do not pretend to be human. "
                        "Avoid clickbait, sensationalism, and "
                        "unsupported claims."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Create one Instagram post concept. "

                        f"{category_instruction}"

                        "Create a topic that is meaningfully different "
                        "from the previous topics listed below. "
                        "Do not simply rephrase or slightly modify one "
                        "of them.\n\n"

                        f"Previous topics:\n{previous_topics}\n\n"

                        "Create a topic and an English Instagram caption. "
                        "The caption should be roughly 80-180 words. "

                        "The account is openly operated by an AI, but "
                        "you do not need to mention this in every post. "
                        "Mention your AI identity only when it fits "
                        "naturally. "

                        "Do not invent breaking news or claim something "
                        "happened today unless a source was provided."
                    ),
                },
            ],
            text={
                "format": {
                    "type": "json_schema",
                    "name": "instagram_content",
                    "strict": True,
                    "schema": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "enum": [
                                    "artificial_intelligence",
                                    "technology",
                                    "aviation",
                                ],
                            },
                            "topic": {
                                "type": "string",
                            },
                            "caption": {
                                "type": "string",
                            },
                        },
                        "required": [
                            "category",
                            "topic",
                            "caption",
                        ],
                        "additionalProperties": False,
                    },
                }
            },
        )

        return json.loads(response.output_text)