from pathlib import Path
import subprocess


def extract_last_frame(
    video_path: str,
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
        "-sseof",
        "-0.1",
        "-i",
        video_path,
        "-frames:v",
        "1",
        str(output),
    ]

    subprocess.run(
        command,
        check=True,
        capture_output=True,
        text=True,
    )

    return str(output)