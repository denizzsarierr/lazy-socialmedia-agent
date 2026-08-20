class InstagramPublisher:
    def publish_post(
        self,
        caption: str | None,
        media_paths: list[str],
    ) -> dict:
        print("=== INSTAGRAM PUBLISHER ===")
        print(f"Caption: {caption}")
        print(f"Media: {media_paths}")

        return {
            "success": True,
            "platform_post_id": "fake_instagram_post_123",
            "response": "Fake Instagram post published successfully.",
        }