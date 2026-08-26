from pathlib import Path
import subprocess


def compose_reel(
    clip_paths: list[str],
    audio_path: str,
    output_path: str,
) -> str:
    if not clip_paths:
        raise ValueError(
            "At least one video clip is required."
        )

    output = Path(output_path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    concat_file = output.parent / "clips.txt"

    with concat_file.open("w") as file:
        for clip_path in clip_paths:
            absolute_path = Path(
                clip_path
            ).resolve()

            file.write(
                f"file '{absolute_path}'\n"
            )

    intermediate_path = (
        output.parent / "combined_video.mp4"
    )

    # Step 1: concatenate Runway clips.
    concat_command = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c",
        "copy",
        str(intermediate_path),
    ]

    subprocess.run(
        concat_command,
        check=True,
        capture_output=True,
        text=True,
    )

    # Step 2: attach Marin narration.
    # -shortest ensures the final Reel ends
    # when the narration ends.
    compose_command = [
        "ffmpeg",
        "-y",
        "-i",
        str(intermediate_path),
        "-i",
        audio_path,
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-shortest",
        "-movflags",
        "+faststart",
        str(output),
    ]

    subprocess.run(
        compose_command,
        check=True,
        capture_output=True,
        text=True,
    )

    return str(output)