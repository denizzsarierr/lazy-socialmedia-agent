import os
import time

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
    
    def publish_reel(
        self,
        caption: str | None,
        video_url: str,
        share_to_feed: bool = True,
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

        if not video_url:
            return {
                "success": False,
                "platform_post_id": None,
                "response": "No Reel video URL provided.",
            }

        try:
            # 1. Create Reel container
            container_url = (
                f"{self.base_url}/"
                f"{self.instagram_account_id}/media"
            )

            container_response = requests.post(
                container_url,
                data={
                    "media_type": "REELS",
                    "video_url": video_url,
                    "caption": caption or "",
                    "share_to_feed": (
                        "true"
                        if share_to_feed
                        else "false"
                    ),
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
                        "Instagram did not return "
                        f"a Reel container ID: {container_data}"
                    ),
                }

            print(
                f"Instagram Reel container created: "
                f"{container_id}"
            )

            # 2. Wait until Instagram finishes
            # processing the uploaded video.
            status_url = (
                f"{self.base_url}/{container_id}"
            )

            max_checks = 5

            for check_number in range(1, max_checks + 1):
                status_response = requests.get(
                    status_url,
                    params={
                        "fields": "status_code,status",
                        "access_token": self.access_token,
                    },
                    timeout=30,
                )

                status_response.raise_for_status()

                status_data = status_response.json()

                status_code = status_data.get(
                    "status_code"
                )

                print(
                    f"Reel processing status "
                    f"({check_number}/{max_checks}): "
                    f"{status_code}"
                )

                if status_code == "FINISHED":
                    break

                if status_code == "ERROR":
                    return {
                        "success": False,
                        "platform_post_id": None,
                        "response": (
                            "Instagram Reel processing failed: "
                            f"{status_data}"
                        ),
                    }

                if status_code == "EXPIRED":
                    return {
                        "success": False,
                        "platform_post_id": None,
                        "response": (
                            "Instagram Reel container expired: "
                            f"{status_data}"
                        ),
                    }

                if check_number < max_checks:
                    time.sleep(60)

            else:
                return {
                    "success": False,
                    "platform_post_id": None,
                    "response": (
                        "Instagram Reel processing did not "
                        "finish within the allowed checks."
                    ),
                }

            # 3. Publish Reel
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
                        "Instagram did not return "
                        f"a Reel media ID: {publish_data}"
                    ),
                }

            return {
                "success": True,
                "platform_post_id": media_id,
                "response": str(publish_data),
            }

        except requests.RequestException as exc:
            if exc.response is not None:
                error_message = exc.response.text
            else:
                error_message = str(exc)

            return {
                "success": False,
                "platform_post_id": None,
                "response": error_message,
            }