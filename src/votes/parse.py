import re
from src.utils import pdf_utils, regex_utils
from src.votes.access import get_vote


def get_vote_title(vote_id: str) -> str:
    blocks = get_vote(vote_id, opt="blocks", first_page_only=True)
    for index, paragraph in enumerate(blocks):
        if regex_utils.is_title_start(paragraph[4]):
            return re.sub(
                "\s+", " ", " ".join(el[4] for el in blocks[index : (index + 3)])
            ).strip()
    raise ValueError(f"Title not found in {vote_id}")
