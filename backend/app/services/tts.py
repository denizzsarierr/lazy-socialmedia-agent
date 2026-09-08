import os
from pathlib import Path

from openai import OpenAI


class TTSService:
    def __init__(self) -> None:
        self.client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY")
        )

        self.model = os.getenv(
            "OPENAI_TTS_MODEL",
            "gpt-4o-mini-tts",
        )

        self.voice = os.getenv(
            "OPENAI_TTS_VOICE",
            "fable",
        )

    def generate(
        self,
        text: str,
        output_path: str,
    ) -> str:
        output = Path(output_path)
        output.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        response = self.client.audio.speech.create(
            model=self.model,
            voice=self.voice,
            input=text,
            instructions=(
            "Speak as Toru, a cheerful young animated technology character. "
            "Use a youthful, bright, friendly voice with a playful cartoon-like energy. "
            "Sound upbeat, curious, and naturally excited about what you're talking about. "
            "Keep the delivery casual and conversational, like talking enthusiastically to a friend. "
            "Use expressive pitch changes and lively intonation, especially on surprising or interesting ideas. "
            "Keep the voice light and energetic rather than deep, serious, or polished. "
            "Speak at a moderately quick pace suitable for short animated social media videos. "
            "Add subtle moments of amusement and wonder when appropriate. "
            "Let questions and surprising facts feel genuinely exciting. "
            "Keep the performance spontaneous and slightly quirky, while still speaking clearly. "
            "Avoid sounding like a narrator, news anchor, teacher, corporate presenter, or advertisement. "
            "Do not sound overly polished or dramatic. "
            "Toru should feel like a fun, clever animated friend who happens to love technology."
        ),
            response_format="mp3",
        )

        response.write_to_file(output)

        return str(output)