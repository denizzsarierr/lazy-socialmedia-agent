import os

import requests


class InstagramPublisher:
    def __init__(self) -> None:
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.instagram_account_id = os.getenv(
            "INSTAGRAM_ACCOUNT_ID"
        )

        self.graph_api_url = os.getenv(
            "META_GRAPH_API_URL",
            "https://graph.facebook.com/v23.0",
        )

    def publish_post(
        self,
        caption: str | None,
        media_urls: list[str],
    ) -> dict:

        print("=== INSTAGRAM PUBLISHER ===")
        print(f"Caption: {caption}")
        print(f"Media: {media_urls}")

        if not self.access_token:
            return {
                "success": False,
                "platform_post_id": None,
                "response": (
                    "INSTAGRAM_ACCESS_TOKEN is not configured."
                ),
            }

        if not self.instagram_account_id:
            return {
                "success": False,
                "platform_post_id": None,
                "response": (
                    "INSTAGRAM_ACCOUNT_ID is not configured."
                ),
            }

        return {
            "success": False,
            "platform_post_id": None,
            "response": (
                "Instagram API integration is not enabled yet."
            ),
        }