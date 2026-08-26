from pathlib import Path

from app.services.video.downloader import download_video
from app.services.video.runway import RunwayVideoGenerator


class VideoPipeline:
    def __init__(self) -> None:
        self.generator = RunwayVideoGenerator()

    def generate_clips(
        self,
        reference_image_url: str,
        scene_prompts: list[str],
        output_dir: str = "/app/generated/reel_clips",
        clip_duration: int = 5,
    ) -> list[str]:

        if not scene_prompts:
            raise ValueError(
                "At least one scene prompt is required."
            )

        output = Path(output_dir)
        output.mkdir(
            parents=True,
            exist_ok=True,
        )

        clip_paths = []

        for index, prompt in enumerate(
            scene_prompts,
            start=1,
        ):
            print(
                f"Generating clip "
                f"{index}/{len(scene_prompts)}..."
            )

            video_url = self.generator.generate(
                reference_image_url=reference_image_url,
                prompt=prompt,
                duration=clip_duration,
            )

            clip_path = output / (
                f"clip_{index:02d}.mp4"
            )

            download_video(
                video_url,
                str(clip_path),
            )

            clip_paths.append(
                str(clip_path)
            )

            print(
                f"Clip {index} downloaded: "
                f"{clip_path}"
            )

        return clip_paths