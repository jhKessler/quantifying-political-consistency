from src.utils.llm import openai_client

import pandas as pd
from typing import TypedDict
from loguru import logger
from src.utils.regex import regex_drucksachen_type

class EntrypointDict(TypedDict):
    entrypoint_drucksache_title: str
    entrypoint_drucksache_id: str


def get_entrypoint(vote_title: str, vote_type: str, drucksachen_for_this_vote: pd.DataFrame ) -> EntrypointDict:
    available_drucksachen = [
        {"index": index, "title": title}
        for index, title in enumerate(drucksachen_for_this_vote["title"].values)
    ]

    if len(available_drucksachen) == 1:
        matched_drucksache = drucksachen_for_this_vote.iloc[0]
    else:
        def catch_no_type_error(text: str):
            try:
                return regex_drucksachen_type(text)
            except ValueError:
                logger.warning(f"Type not found in {text}. Using 'Unbekannt'.")
                return "Unbekannt"
        drucksachen_for_this_vote["type"] = drucksachen_for_this_vote["title"].apply(catch_no_type_error)
        same_type = drucksachen_for_this_vote[
            (drucksachen_for_this_vote["type"] == vote_type)
        ]
        if same_type.empty:
            logger.warning(
                f"No drucksachen of type {vote_type} found for vote {vote_title}. Using all available drucksachen."
            )

        match = openai_client.match_drucksache_to_vote(
            vote_title, available_drucksachen if same_type.empty else same_type
        )
        matched_drucksache = drucksachen_for_this_vote.iloc[match.index]
    return {
        "entrypoint_drucksache_title": matched_drucksache["title"],
        "entrypoint_drucksache_id": matched_drucksache["drucksache"],
    }