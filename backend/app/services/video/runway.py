import os

from runwayml import RunwayML, TaskFailedError

from app.services.video.base import VideoGenerator


class RunwayVideoGenerator(VideoGenerator):
    def __init__(self) -> None:
        self.client = RunwayML(
            api_key=os.getenv("RUNWAYML_API_SECRET")
        )

        self.model = os.getenv(
            "RUNWAY_VIDEO_MODEL",
            "gen4_turbo",
        )

    def generate(
        self,
        reference_image_url: str,
        prompt: str,
        duration: int = 5,
    ) -> str:

        # Runway allows a maximum of 1000 characters.
        if len(prompt) > 1000:
            raise ValueError(
                f"Runway prompt is too long: "
                f"{len(prompt)} characters."
            )

        try:
            task = self.client.image_to_video.create(
                model=self.model,
                prompt_image=reference_image_url,
                prompt_text=prompt,
                ratio="720:1280",
                duration=duration,
            ).wait_for_task_output()

        except TaskFailedError as exc:
            raise RuntimeError(
                f"Runway video generation failed: "
                f"{exc.task_details}"
            ) from exc

        if not task.output:
            raise RuntimeError(
                "Runway returned no video output."
            )

        return task.output[0]
        