import os

import requests


class InstagramPublisher:
    def __init__(self) -> None:
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.instagram_account_id = os.getenv(
            "INSTAGRAM_ACCOUNT_ID"
        )

        self.api_version = os.getenv(
            "META_API_VERSION",
            "v23.0",
        )

        self.base_url = (
            f"https://graph.instagram.com/{self.api_version}"
        )

    def publish_post(
        self,
        caption: str | None,
        media_urls: list[str],
    ) -> dict:

        if not self.access_token:
            return {
                "success": False,
                "platform_post_id": None,
                "response": "INSTAGRAM_ACCESS_TOKEN is not configured.",
            }

        if not self.instagram_account_id:
            return {
                "success": False,
                "platform_post_id": None,
                "response": "INSTAGRAM_ACCOUNT_ID is not configured.",
            }

        if not media_urls:
            return {
                "success": False,
                "platform_post_id": None,
                "response": "No media URL provided.",
            }

        if len(media_urls) != 1:
            return {
                "success": False,
                "platform_post_id": None,
                "response": (
                    "Only single-image posts are supported for now."
                ),
            }

        try:
            # Step 1: Create media container
            container_url = (
                f"{self.base_url}/"
                f"{self.instagram_account_id}/media"
            )

            container_response = requests.post(
                container_url,
                data={
                    "image_url": media_urls[0],
                    "caption": caption or "",
                    "access_token": self.access_token,
                },
                timeout=30,
            )

            container_response.raise_for_status()

            container_data = container_response.json()

            container_id = container_data.get("id")

            if not container_id:
                return {
                    "success": False,
                    "platform_post_id": None,
                    "response": (
                        f"Instagram did not return a container ID: "
                        f"{container_data}"
                    ),
                }

            # Step 2: Publish container
            publish_url = (
                f"{self.base_url}/"
                f"{self.instagram_account_id}/media_publish"
            )

            publish_response = requests.post(
                publish_url,
                data={
                    "creation_id": container_id,
                    "access_token": self.access_token,
                },
                timeout=30,
            )

            publish_response.raise_for_status()

            publish_data = publish_response.json()

            media_id = publish_data.get("id")

            if not media_id:
                return {
                    "success": False,
                    "platform_post_id": None,
                    "response": (
                        f"Instagram did not return a media ID: "
                        f"{publish_data}"
                    ),
                }

            return {
                "success": True,
                "platform_post_id": media_id,
                "response": str(publish_data),
            }

        except requests.RequestException as exc:
            response_text = None

            if exc.response is not None:
                response_text = exc.response.text

            return {
                "success": False,
                "platform_post_id": None,
                "response": response_text or str(exc),
            }