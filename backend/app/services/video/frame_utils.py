import os
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


import os
import subprocess


def extract_frame_before_end(
        video_path: str,
        output_path: str,
        seconds_before_end: float = 0.5,
    ) -> str:
    """
    Extract a frame shortly before the end of a video.

    Example:
        seconds_before_end=0.5
        -> extracts a frame roughly 0.5 seconds
           before the final frame.
    """

    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True,
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-sseof",
            f"-{seconds_before_end}",
            "-i",
            video_path,
            "-frames:v",
            "1",
            "-q:v",
            "2",
            output_path,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return output_path