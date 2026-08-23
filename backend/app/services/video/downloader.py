from pathlib import Path

import requests


def download_video(
    url: str,
    output_path: str,
) -> str:
    output = Path(output_path)
    output.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    response = requests.get(
        url,
        timeout=120,
    )

    response.raise_for_status()

    output.write_bytes(
        response.content
    )

    return str(output)