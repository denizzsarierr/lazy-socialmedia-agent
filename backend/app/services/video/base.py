from abc import ABC, abstractmethod


class VideoGenerator(ABC):

    @abstractmethod
    def generate(
        self,
        reference_image_url: str,
        prompt: str,
        duration: int,
    ) -> str:
        """
        Generate a video and return either a provider URL
        or a local path to the generated MP4.
        """
        raise NotImplementedError