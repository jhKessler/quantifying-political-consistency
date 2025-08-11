import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import TypedDict

import pandas as pd
from langchain_chroma import Chroma
from loguru import logger
from tqdm import tqdm

from src.enums import VoteResultEnum
from src.manifestos.embed import get_rag_embeddings
from src.prediction import config
from src.utils.llm import deepseek_client, openai_client
from src.votes.config import RESULT_CSV_FOLDER


def get_correct_manifesto_year(
    date: datetime, party: str, manifestos_metadata: pd.DataFrame
) -> str | None:
    only_party = manifestos_metadata.query("party == @party").sort_values(
        "valid_starting", ascending=True
    )
    after_date = only_party.query("valid_starting < @date")
    try:
        correct_row = after_date.iloc[-1]
        return correct_row["year"]
    except IndexError:
        logger.warning(
            f"No manifesto found for {party} before {date.strftime('%Y-%m-%d')}"
        )
        return None


class VotePredictionResult(TypedDict):
    context: str
    reasoning: str
    decision: str | None


def predict_vote(
    vote: pd.Series,
    chroma_store: dict[str, Chroma],
    party: str,
    manifestos: pd.DataFrame,
) -> VotePredictionResult | None:
    relevant_year = get_correct_manifesto_year(vote["date"], party, manifestos)
    if relevant_year is None:
        return None
    vs = chroma_store[relevant_year]
    results = vs.similarity_search_by_vector(
        embedding=vote["summary_embedding"], k=config.SIMILARITY_K
    )

    llm_context = "\n".join([doc.page_content for doc in results])
    decision_text = openai_client.prompt_openai(
        system_prompt=config.PREDICTION_PROMPT,
        text=f"""
            Wahlprogramm: {llm_context} 
            Antrag: {vote["summary"]}
        """,
        model="gpt-5",
    )
    cleaned = re.sub(r"[^a-zA-Zä ]", "", decision_text).strip()
    if cleaned.startswith("stimmt nicht zu"):
        decision = VoteResultEnum.ABLEHNUNG.value
    elif cleaned.startswith("stimmt zu"):
        decision = VoteResultEnum.ANNAHME.value
    elif cleaned.startswith("enthält sich"):
        decision = VoteResultEnum.ENTHALTUNG.value
    else:
        logger.warning(f"Unexpected decision text: {decision_text}")
        decision = None
    return {"context": llm_context, "reasoning": decision_text, "decision": decision}


def process(
    idx: int,
    row: pd.Series,
    chroma_store: dict[str, Chroma],
    party: str,
    manifestos: pd.DataFrame,
) -> tuple[int, VotePredictionResult | None]:
    try:
        return idx, predict_vote(row, chroma_store, party, manifestos)
    except Exception as e:
        logger.error(f"Error processing row: {row['vote_id']}")
        logger.exception(e)
        return idx, None


def predict_partyline(
    party: str, votes: pd.DataFrame, manifestos: pd.DataFrame
) -> list[VotePredictionResult]:
    if not Path(f"{RESULT_CSV_FOLDER}/{party}.csv").exists():
        raise FileNotFoundError(
            f"Results file for party {party} not found. Please run the preprocessing step first."
        )

    manifestos = manifestos[manifestos["party"] == party]
    manifesto_chroma_db = get_rag_embeddings(party)

    decisions = [None] * len(votes)
    with (
        ThreadPoolExecutor(max_workers=config.THREADS) as pool,
        tqdm(total=len(votes)) as pbar,
    ):
        futures = [
            pool.submit(process, i, row, manifesto_chroma_db, party, manifestos)
            for i, (_, row) in enumerate(votes.iterrows())
        ]

        for future in as_completed(futures):
            i, decision = future.result()
            decisions[i] = decision
            pbar.update(1)

    return decisions
