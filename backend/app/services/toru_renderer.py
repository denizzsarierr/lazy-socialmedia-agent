from pathlib import Path
from PIL import Image
import math
import subprocess

from app.services.speech_timing import (
    is_speaking,
)

from app.services.animation_planner import (
    AnimationPlanner,
)


CANVAS_SIZE = (720, 1280)
FPS = 30

ASSET_DIR = Path("/app/app/assets/toru")
OUTPUT_DIR = Path("/app/generated/toru")

# Pose transitions
TRANSITION_DURATION = 0.15

# Small idle movement
BOB_AMPLITUDE = 5
BOB_SPEED = 0.8


POSE_FILES = {
    "idle": {
        "closed": "toru_idle.png",
        "talk": "toru_idle_talk.png",
    },
    "explain": {
        "closed": "toru_explain.png",
        "talk": "toru_explain_talk.png",
    },
    "wave": {
        "closed": "toru_wave.png",
    },
    "wink": {
        "closed": "toru_wink.png",
    },
}


def load_and_normalize_pose(
    name: str,
) -> Image.Image:

    path = ASSET_DIR / name

    if not path.exists():
        raise FileNotFoundError(
            f"Pose not found: {path}"
        )

    image = Image.open(
        path
    ).convert("RGBA")

    target_height = 1000

    scale = (
        target_height
        / image.height
    )

    new_width = round(
        image.width * scale
    )

    new_height = round(
        image.height * scale
    )

    image = image.resize(
        (new_width, new_height),
        Image.Resampling.LANCZOS,
    )

    canvas = Image.new(
        "RGBA",
        CANVAS_SIZE,
        (0, 0, 0, 0),
    )

    x = (
        CANVAS_SIZE[0]
        - new_width
    ) // 2

    bottom_margin = 80

    y = (
        CANVAS_SIZE[1]
        - new_height
        - bottom_margin
    )

    canvas.alpha_composite(
        image,
        (x, y),
    )

    return canvas


def ease_in_out(
    value: float,
) -> float:
    """
    Smoothstep easing.
    Converts 0..1 into a smoother 0..1 transition.
    """

    value = max(
        0.0,
        min(1.0, value),
    )

    return (
        value
        * value
        * (3 - 2 * value)
    )


def get_timeline_pose(
    time_sec: float,
    pose_timeline: list[dict],
):
    for index, scene in enumerate(
        pose_timeline
    ):
        start = scene["start"]
        end = scene["end"]
        pose_name = scene["pose"]

        if start <= time_sec < end:
            return (
                index,
                start,
                end,
                pose_name,
            )

    # If we are exactly at / after the end,
    # keep the final pose.
    last_scene = pose_timeline[-1]

    return (
        len(pose_timeline) - 1,
        last_scene["start"],
        last_scene["end"],
        last_scene["pose"],
    )


def get_pose_variant(
    pose_name: str,
    speaking: bool,
    time_sec: float,
    poses: dict,
) -> Image.Image:

    variants = poses[pose_name]

    if not speaking:
        return variants["closed"]

    if "talk" not in variants:
        return variants["closed"]

    mouth_open = (
        int(time_sec * 7) % 2 == 0
    )

    if mouth_open:
        return variants["talk"]

    return variants["closed"]


def get_pose_image(
    time_sec: float,
    poses: dict,
    speaking: bool,
    pose_timeline: list[dict],
) -> Image.Image:

    (
        index,
        start,
        _,
        pose_name,
    ) = get_timeline_pose(
        time_sec,
        pose_timeline,
    )

    current_pose = get_pose_variant(
        pose_name,
        speaking,
        time_sec,
        poses,
    )

    if index == 0:
        return current_pose.copy()

    time_since_transition = (
        time_sec - start
    )

    if (
        time_since_transition
        >= TRANSITION_DURATION
    ):
        return current_pose.copy()

    previous_pose_name = (
        pose_timeline[
            index - 1
        ]["pose"]
    )

    previous_pose = get_pose_variant(
        previous_pose_name,
        speaking,
        time_sec,
        poses,
    )

    progress = (
        time_since_transition
        / TRANSITION_DURATION
    )

    progress = ease_in_out(
        progress
    )

    return Image.blend(
        previous_pose,
        current_pose,
        progress,
    )


def should_wink(
    time_sec: float,
) -> bool:
    """
    Temporary facial animation.

    Later this can be replaced
    by dynamic animation events.
    """

    wink_intervals = [
        (2.90, 3.05),
        (4.55, 4.70),
    ]

    for start, end in wink_intervals:
        if start <= time_sec < end:
            return True

    return False


def apply_idle_motion(
    image: Image.Image,
    time_sec: float,
) -> Image.Image:

    offset_y = int(
        math.sin(
            time_sec
            * math.tau
            * BOB_SPEED
        )
        * BOB_AMPLITUDE
    )

    canvas = Image.new(
        "RGBA",
        CANVAS_SIZE,
        (0, 0, 0, 0),
    )

    canvas.alpha_composite(
        image,
        (0, offset_y),
    )

    return canvas


def get_audio_duration(
    audio_path: str | Path,
) -> float:

    audio_path = Path(
        audio_path
    )

    if not audio_path.exists():
        raise FileNotFoundError(
            f"Audio file not found: "
            f"{audio_path}"
        )

    command = [
        "ffprobe",
        "-v",
        "error",
        "-show_entries",
        "format=duration",
        "-of",
        (
            "default="
            "noprint_wrappers=1:"
            "nokey=1"
        ),
        str(audio_path),
    ]

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=True,
    )

    return float(
        result.stdout.strip()
    )


def render_toru_video(
    audio_path: str | Path,
    script: str,
    words: list[dict],
    output_path: str | Path,
    ) -> str:

    duration = get_audio_duration(
        audio_path
    )

    planner = AnimationPlanner()

    pose_timeline = planner.generate(
        script=script,
        duration=duration,
        words=words,
    )   

    print(
        f"Audio duration: "
        f"{duration:.2f}s"
    )

    print(
        f"Detected "
        f"{len(words)} "
        f"spoken words"
    )

    print(
        "Animation plan:"
    )

    for scene in pose_timeline:
        print(
            f"{scene['start']:.2f} - "
            f"{scene['end']:.2f}: "
            f"{scene['pose']}"
        )

    output_path = Path(output_path)

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    poses = {}

    for (
        pose_name,
        variants,
    ) in POSE_FILES.items():

        poses[pose_name] = {}

        for (
            variant_name,
            filename,
        ) in variants.items():

            poses[
                pose_name
            ][
                variant_name
            ] = (
                load_and_normalize_pose(
                    filename
                )
            )

    command = [
        "ffmpeg",
        "-y",

        "-f",
        "rawvideo",

        "-pix_fmt",
        "rgb24",

        "-s",
        (
            f"{CANVAS_SIZE[0]}"
            f"x"
            f"{CANVAS_SIZE[1]}"
        ),

        "-r",
        str(FPS),

        "-i",
        "-",

        "-i",
        str(audio_path),

        # Video
        "-c:v",
        "libx264",

        "-preset",
        "medium",

        "-crf",
        "18",

        "-pix_fmt",
        "yuv420p",

        # Audio
        "-c:a",
        "aac",

        "-b:a",
        "128k",

        "-shortest",

        "-movflags",
        "+faststart",

        str(output_path),
    ]

    process = subprocess.Popen(
        command,
        stdin=subprocess.PIPE,
    )

    total_frames = math.ceil(
        FPS * duration
    )

    try:
        for frame_number in range(
            total_frames
        ):
            time_sec = (
                frame_number
                / FPS
            )

            speaking = is_speaking(
                time_sec,
                words,
            )

            character = get_pose_image(
                time_sec,
                poses,
                speaking,
                pose_timeline,
            )

            (
                _,
                _,
                _,
                current_pose_name,
            ) = get_timeline_pose(
                time_sec,
                pose_timeline,
            )

            # Temporary wink.
            # Do not wink while speaking.
            if (
                current_pose_name
                == "idle"
                and not speaking
                and should_wink(
                    time_sec
                )
            ):
                character = (
                    poses[
                        "wink"
                    ][
                        "closed"
                    ].copy()
                )

            character = (
                apply_idle_motion(
                    character,
                    time_sec,
                )
            )

            frame = Image.new(
                "RGB",
                CANVAS_SIZE,
                (220, 235, 255),
            )

            frame.paste(
                character,
                (0, 0),
                character,
            )

            if process.stdin is None:
                raise RuntimeError(
                    "FFmpeg stdin "
                    "is not available"
                )

            process.stdin.write(
                frame.tobytes()
            )

    finally:
        if (
            process.stdin
            is not None
        ):
            process.stdin.close()

    return_code = (
        process.wait()
    )

    if return_code != 0:
        raise RuntimeError(
            "FFmpeg failed "
            f"with exit code "
            f"{return_code}"
        )

    print(
        f"Rendered "
        f"{total_frames} "
        f"frames directly "
        f"to FFmpeg"
    )

    print(
        f"Video created: "
        f"{output_path}"
    )

    return str(
        output_path
    )

