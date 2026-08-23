import os

import cloudinary
import cloudinary.uploader


cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET"),
    secure=True,
)


class MediaStorage:
    def upload_image(self, file_path: str) -> str:
        result = cloudinary.uploader.upload(
            file_path,
            resource_type="image",
            folder="lazy-socialmedia-agent",
        )

        secure_url = result.get("secure_url")

        if not secure_url:
            raise RuntimeError(
                "Cloudinary upload did not return a secure_url."
            )

        return secure_url

    def upload_video(self, file_path: str) -> str:
        result = cloudinary.uploader.upload(
            file_path,
            resource_type="video",
            folder="lazy-socialmedia-agent",
        )

        secure_url = result.get("secure_url")

        if not secure_url:
            raise RuntimeError(
                "Cloudinary upload did not return a secure_url."
            )

        return secure_url