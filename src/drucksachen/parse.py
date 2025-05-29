import re

from src.drucksachen.access import get_drucksache
from src.utils import regex


def extract_title_from_drucksache(drucksachen_id: str) -> str:
    blocks = get_drucksache(drucksachen_id, opt="blocks", first_page_only=True)
    for index, paragraph in enumerate(blocks):
        if regex.is_title_start(paragraph[4].strip()):
            return re.sub(
                "\s+",
                " ",
                " ".join(el[4] for el in blocks[index : (index + 3)]),
            ).strip()
    raise ValueError("Title not found in the document.")
