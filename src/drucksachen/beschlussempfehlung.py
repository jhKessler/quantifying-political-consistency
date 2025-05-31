import re
from typing import TypedDict

from loguru import logger

from src.drucksachen.access import get_drucksache
from src.drucksachen.parse import extract_title_from_drucksache
from src.enums import VoteResultEnum
from src.utils import regex


def get_content(drucksache_id: str) -> str | None:
    blocks = get_drucksache(drucksache_id, opt="blocks")
    started, buf = False, []
    for block in blocks:
        text = block[4].strip()
        if "Der Bundestag wolle beschließen" in text:
            started = True
        if started:
            buf.append(text)
        if "Berlin, den" in text:
            break
    if not started:
        logger.error(f"Beschlussempfehlung start not found in {drucksache_id}")
        return None
    return " ".join(buf)


class VoteEntry(TypedDict):
    vote: str
    drucksache_id: str
    beschlussempfehlung: str | None


def parse(vote_id: str, drucksache_id: str) -> list[VoteEntry]:
    beschluss_pattern = re.compile(
        r"Drucksache\s+(\d+/\d+)"
        r"(?:\s+(?!anzunehmen|abzulehnen)[A-Za-zÄÖÜäöüß]+)*"
        r"\s+(anzunehmen|abzulehnen)"
    )
    text = get_content(drucksache_id)
    if not text:
        return []
    results = []
    for druck_id, action in beschluss_pattern.findall(text):
        results.append(
            {
                "vote_id": vote_id,
                "drucksache_id": druck_id,
                "beschlussempfehlung": VoteResultEnum.ANNAHME.value
                if action == "anzunehmen"
                else VoteResultEnum.ABLEHNUNG.value,
            }
        )
    if not results:
        logger.warning(f"No votes found in Beschlussempfehlung {drucksache_id}")
    return results


class ParsedBeschlussempfehlung(TypedDict):
    vote_id: str
    type: str
    entrypoint_drucksache_title: str
    entrypoint_drucksache_id: str


def build(vote_id: str, vote_num: str, drucksache_id: str) -> list[dict]:
    underyling_votes = parse(vote_id, drucksache_id)
    result = []
    for vote in underyling_votes:
        title = extract_title_from_drucksache(vote["drucksache_id"])
        type_ = regex.regex_drucksachen_type(title)
        result.append(
            {
                "vote_id": vote_id,
                "vote_num": vote_num,
                "type": type_,
                "entrypoint_drucksache_title": title,
                "entrypoint_drucksache_id": vote["drucksache_id"],
                "beschlussempfehlung": vote["beschlussempfehlung"],
            }
        )
    if not result:
        logger.warning(
            f"No underlying votes found for {vote_id} with drucksache {drucksache_id}."
        )

    return result
