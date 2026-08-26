from pathlib import Path


def _ass_time(seconds: float) -> str:
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    return (
        f"{hours}:"
        f"{minutes:02d}:"
        f"{secs:05.2f}"
    )


def generate_karaoke_ass(
    chunks: list[list[dict]],
    output_path: str,
) -> str:
    output = Path(output_path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    header = """[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 2
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Toru,Arial,48,&H00FFFFFF,&H0000D7FF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,3,1,2,60,60,110,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""

    dialogue_lines = []

    for chunk in chunks:
        start = chunk[0]["start"]
        end = chunk[-1]["end"]

        karaoke_parts = []

        for word in chunk:
            duration = max(
                word["end"] - word["start"],
                0.01,
            )

            centiseconds = max(
                1,
                round(duration * 100),
            )

            karaoke_parts.append(
                f"{{\\k{centiseconds}}}{word['word']}"
            )

        text = " ".join(
            karaoke_parts
        )

        dialogue_lines.append(
            "Dialogue: 0,"
            f"{_ass_time(start)},"
            f"{_ass_time(end)},"
            "Toru,,0,0,0,,"
            f"{text}"
        )

    output.write_text(
        header
        + "\n".join(dialogue_lines),
        encoding="utf-8",
    )

    return str(output)