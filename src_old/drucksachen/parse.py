import re
from src.drucksachen.access import get_drucksache
from src.utils import regex
import re
from typing import Iterable, TypedDict
from loguru import logger
from . import extractors


def extract_title_from_drucksache(drucksachen_id: str) -> str:
    blocks = get_drucksache(drucksachen_id, opt="blocks", first_page_only=True)
    for index, paragraph in enumerate(blocks):
        if regex_utils.is_title_start(paragraph[4]):
            return re.sub(
                "\s+",
                " ",
                " ".join(el[4] for el in blocks[index : (index + 3)]),
            ).strip()
    raise ValueError("Title not found in the document.")


class VoteEntry(TypedDict):
    vote: str
    drucksache_id: str
    beschlussempfehlung: str | None


_BESCHLUSS_REGEX = re.compile(
    r"Drucksache\s+(\d+/\d+)"
    r"(?:\s+(?!anzunehmen|abzulehnen)[A-Za-zÄÖÜäöüß]+)*"
    r"\s+(anzunehmen|abzulehnen)"
)


def parse_beschlussempfehlung(vote: str, drucksache_id: str) -> list[VoteEntry]:
    text = extractors.beschlussempfehlung(drucksache_id)
    if not text:
        return []
    results = []
    for druck_id, action in _BESCHLUSS_REGEX.findall(text):
        results.append(
            {
                "vote": vote,
                "drucksache_id": druck_id,
                "beschlussempfehlung": "annehmen"
                if action == "anzunehmen"
                else "ablehnen",
            }
        )
    if not results:
        logger.warning(f"No votes found in Beschlussempfehlung {drucksache_id}")
    return results


def clean_content(text: str) -> str:
    header = re.compile(
        r"Deutscher Bundestag\s+–\s+\d+\.\s+Wahlperiode\s*\n–\s*\d+\s*–\s*\nDrucksache\s+\d+/\d+",
        flags=re.MULTILINE,
    )
    return header.sub("", text).replace("\xa0", " ").strip().replace("  ", " ")
