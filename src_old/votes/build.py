import os
import pandas as pd
from src.utils import regex_utils
from src.drucksachen.access import assert_drucksache_download
from src.drucksachen.parse import (
    extract_date_from_drucksache,
    extract_title_from_drucksache,
)
from src.votes.access import assert_vote_download, get_vote
from loguru import logger
from src.votes.parse import get_vote_title


def download_vote_documents(vote: pd.Series) -> pd.DataFrame:
    vote_text = get_vote(vote["id"], opt="text", first_page_only=True)
    relevant_ids = regex_utils.regex_drucksachen_ids(vote_text)

    success = []
    for relevant_id in relevant_ids:
        try:
            assert_drucksache_download(relevant_id)
            title = extract_title_from_drucksache(relevant_id)
            success.append(
                {
                    "drucksache": relevant_id,
                    "title": title,
                    "vote": vote["id"],
                }
            )
        except Exception as e:
            logger.error(f"Error downloading {relevant_id}: {e}")
            continue
    return pd.DataFrame(success)


def build_vote(vote: pd.Series) -> pd.DataFrame:
    assert_vote_download(vote)
    title = get_vote_title(vote["id"])
    return pd.DataFrame(
        [{"id": vote["id"], "title": title, "type": title.split(" ")[0]}]
    )
