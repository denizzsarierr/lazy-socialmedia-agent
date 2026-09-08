from pathlib import Path
from openai import OpenAI


client = OpenAI()


def get_word_timestamps(audio_path: str | Path):
    audio_path = Path(audio_path)

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Audio file not found: {audio_path}"
        )

    with audio_path.open("rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            response_format="verbose_json",
            timestamp_granularities=["word"],
        )

    words = []

    for word in transcription.words or []:
        words.append(
            {
                "word": word.word,
                "start": float(word.start),
                "end": float(word.end),
            }
        )

    return words

def is_speaking(
    time_sec: float,
    words: list[dict],
    padding: float = 0.04,
    ) -> bool:
    for word in words:
        start = word["start"] - padding
        end = word["end"] + padding

        if start <= time_sec <= end:
            return True

    return False

if __name__ == "__main__":
    timestamps = get_word_timestamps(
        "/app/generated/toru_reel_voice.mp3"
    )

    for word in timestamps:
        print(
            f"{word['start']:.2f} - "
            f"{word['end']:.2f} : "
            f"{word['word']}"
        )