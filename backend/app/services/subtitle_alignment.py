from pathlib import Path

from openai import OpenAI


class SubtitleAligner:
    def __init__(self) -> None:
        self.client = OpenAI()

    def align_words(
        self,
        audio_path: str,
    ) -> list[dict]:
        path = Path(audio_path)

        if not path.exists():
            raise FileNotFoundError(
                f"Audio file not found: {audio_path}"
            )

        with path.open("rb") as audio_file:
            transcript = self.client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="verbose_json",
                timestamp_granularities=["word"],
                language="en",
            )

        words = []

        for word in transcript.words or []:
            words.append(
                {
                    "word": word.word.strip(),
                    "start": float(word.start),
                    "end": float(word.end),
                }
            )

        if not words:
            raise RuntimeError(
                "No word timestamps were returned."
            )

        return words