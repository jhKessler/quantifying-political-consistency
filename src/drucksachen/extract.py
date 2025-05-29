from loguru import logger

from src.drucksachen.access import get_drucksache


def _scan_for_intro(
    blocks, start_mark: str, end_mark: str | None, start_at_index: int | None = None
) -> str | None:
    start = start_at_index
    end = None
    for idx, block in enumerate(blocks):
        text = block[4].strip()
        if start is None and text.startswith(start_mark):
            start = idx
        if start is not None and end_mark and text.startswith(end_mark):
            end = idx
            break
    if start is None or (end_mark and end is None):
        return None
    slice_ = blocks[start:end] if end else blocks[start:]
    return " ".join(b[4] for b in slice_)


def gesetzentwurf(drucksache_id: str) -> str | None:
    blocks = get_drucksache(drucksache_id, opt="blocks")
    res = _scan_for_intro(blocks, "A.", "C.")
    if res is None:
        logger.error(f"Gesetzentwurf intro not found in {drucksache_id}")
    return res


def antrag(drucksache_id: str) -> str | None:
    blocks = get_drucksache(drucksache_id, opt="blocks")
    res = _scan_for_intro(blocks, "Begründung", None, start_at_index=0)
    if res is None:
        logger.error(f"Antrag intro not found in {drucksache_id}")
    return res
