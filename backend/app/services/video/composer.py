from pathlib import Path
import subprocess


def burn_subtitles(
    video_path: str,
    ass_path: str,
    output_path: str,
) -> str:
    output = Path(output_path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    command = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vf",
        f"ass={ass_path}",
        "-c:a",
        "copy",
        "-movflags",
        "+faststart",
        str(output),
    ]

    subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )

    return str(output)