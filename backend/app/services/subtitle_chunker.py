import re


def chunk_words(
    words: list[dict],
    max_words: int = 5,
    max_duration: float = 2.5,
    max_gap: float = 0.45,
) -> list[list[dict]]:
    if not words:
        return []

    chunks = []
    current_chunk = []

    sentence_end_pattern = re.compile(
        r"[.!?]$"
    )

    for word in words:
        if not current_chunk:
            current_chunk.append(word)
            continue

        chunk_start = current_chunk[0]["start"]

        potential_duration = (
            word["end"]
            - chunk_start
        )

        previous_word = (
            current_chunk[-1]["word"]
        )

        previous_ends_sentence = bool(
            sentence_end_pattern.search(
                previous_word
            )
        )

        gap = (
            word["start"]
            - current_chunk[-1]["end"]
        )

        large_pause = (
            gap >= max_gap
        )

        should_split = (
            len(current_chunk) >= max_words
            or potential_duration > max_duration
            or previous_ends_sentence
            or large_pause
        )

        if should_split:
            chunks.append(
                current_chunk
            )

            current_chunk = []

        current_chunk.append(
            word
        )

    if current_chunk:
        chunks.append(
            current_chunk
        )

    return chunks

def merge_short_chunks(
    chunks: list[list[dict]],
    min_words: int = 2,
) -> list[list[dict]]:
    if not chunks:
        return []

    merged = []
    index = 0

    while index < len(chunks):
        chunk = chunks[index]

        if (
            len(chunk) < min_words
            and merged
        ):
            merged[-1].extend(chunk)
        else:
            merged.append(chunk)

        index += 1

    return merged