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

def create_static_motion_clip(
    image_path: str,
    output_path: str,
    duration: int = 5,
) -> str:

    os.makedirs(
        os.path.dirname(output_path),
        exist_ok=True,
    )

    subprocess.run(
        [
            "ffmpeg",
            "-y",
            "-loop",
            "1",
            "-i",
            image_path,
            "-vf",
            (
                "scale=720:1280,"
                "zoompan="
                "z='min(zoom+0.00015,1.02)':"
                "x='iw/2-(iw/zoom/2)':"
                "y='ih/2-(ih/zoom/2)':"
                "d=125:"
                "s=720x1280:"
                "fps=25"
            ),
            "-t",
            str(duration),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-an",
            output_path,
        ],
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    return output_path