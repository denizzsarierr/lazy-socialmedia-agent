from pathlib import Path

import requests


def download_file(
    url: str,
    output_path: str,
    timeout: int = 120,
    ) -> str:
    output = Path(output_path)

    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    response = requests.get(
        url,
        timeout=timeout,
    )

    response.raise_for_status()

    output.write_bytes(
        response.content
    )

    return str(output)


def download_video(
    url: str,
    output_path: str,
    ) -> str:
    return download_file(
        url=url,
        output_path=output_path,
        timeout=120,
    )


def download_image(
    url: str,
    output_path: str,
    ) -> str:
    return download_file(
        url=url,
        output_path=output_path,
        timeout=60,
    )