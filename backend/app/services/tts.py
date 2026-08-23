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
            "marin",
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
                "Speak in a cheerful, warm, and friendly tone. "
                "Sound like you're naturally smiling while speaking. "
                "Keep the delivery upbeat, welcoming, and genuinely enthusiastic. "
                "Use a natural conversational rhythm with lively intonation. "
                "Sound curious and happy to share something interesting. "
                "Keep the energy positive and engaging, but relaxed and effortless. "
                "Avoid sounding overly excited, theatrical, formal, "
                "or like a traditional news anchor."
            ),
            response_format="mp3",
        )

        response.write_to_file(output)

        return str(output)