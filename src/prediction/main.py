import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import pandas as pd
from langchain_chroma import Chroma
from loguru import logger
from tqdm import tqdm

from src.prediction import config, embeddings
from src.utils.deepseek_utils import prompt_deepseek


def get_correct_manifesto_year(
    date: datetime, party: str, manifestos_metadata: pd.DataFrame
) -> str | None:
    only_party = manifestos_metadata.query("party == @party").sort_values(
        "valid_starting", ascending=True
    )
    after_date = only_party.query("valid_starting < @date")
    try:
        correct_row = after_date.iloc[-1]
        return str(correct_row["year"])
    except IndexError:
        logger.warning(
            f"No manifesto found for {party} before {date.strftime('%Y-%m-%d')}"
        )
        return None


def predict_vote(
    vote: pd.Series,
    chroma_store: dict[str, Chroma],
    party: str,
    manifestos_metadata: pd.DataFrame,
):
    relevant_year = get_correct_manifesto_year(vote["date"], party, manifestos_metadata)
    if relevant_year is None:
        return None
    vs = chroma_store[relevant_year]
    results = vs.similarity_search_by_vector(
        embedding=vote["embedding"], k=config.SIMILARITY_K
    )

    llm_context = "\n".join([doc.page_content for doc in results])
    decision_text = prompt_deepseek(
        system_prompt=config.DEEPSEEK_SYSTEM_PROMPT,
        text=f"""
            Wahlprogramm: {llm_context} 
            Antrag: {vote["summary"]}
        """,
        model=config.DEEPSEEK_MODEL,
    )
    cleaned = re.sub(r"[^a-zA-Zä ]", "", decision_text).strip()
    if cleaned.startswith("stimmt nicht zu"):
        decision = "ablehnung"
    elif cleaned.startswith("stimmt zu"):
        decision = "zustimmung"
    elif cleaned.startswith("enthält sich"):
        decision = "enthaltung"
    else:
        logger.warning(f"Unexpected decision text: {decision_text}")
        decision = None
    return {"context": llm_context, "reasoning": decision_text, "decision": decision}


def process(
    idx: int, row: pd.Series, chroma_store: dict[str, Chroma], party: str, manifestos_metadata: pd.DataFrame
) -> tuple[int, str | None]:
    try:
        return idx, predict_vote(row, chroma_store, party, manifestos_metadata)
    except Exception as e:
        logger.error(f"Error processing row: {row['vote']}")
        logger.exception(e)
        return idx, None


def predict_partyline(party: str, vote_embeddings: pd.DataFrame, manifesto_metadata: pd.DataFrame) -> list[dict]:
    decisions = [None] * len(vote_embeddings)
    manifesto_embeddings = embeddings.embed_manifestos(party)
    with (
        ThreadPoolExecutor(max_workers=config.THREADS) as pool,
        tqdm(total=len(vote_embeddings)) as pbar,
    ):
        futures = [
            pool.submit(process, i, row, manifesto_embeddings, party, manifesto_metadata)
            for i, (_, row) in enumerate(vote_embeddings.iterrows())
        ]
        for future in as_completed(futures):
            i, decision = future.result()
            decisions[i] = decision
            pbar.update(1)
    return decisions


def predict_party_votes():
    if not os.path.exists("data/parquet/votes_summarized_embeddings.parquet"):
        logger.error(
            "Vote embeddings file not found. Please run the embedding generation first."
        )
        raise FileNotFoundError("Vote embeddings file not found.")

    vote_embeddings = pd.read_parquet(
        "data/parquet/votes_summarized_embeddings.parquet"
    )
    vote_embeddings["date"] = pd.to_datetime(
        vote_embeddings["vote"].str.split("_").str[0], format="%Y%m%d"
    )

    manifestos_metadata = pd.read_csv("data/csv/manifestos.csv")
    manifestos_metadata["valid_starting"] = pd.to_datetime(
        manifestos_metadata["valid_starting"], format="%d.%m.%Y"
    )

    for party in config.PARTIES:
        logger.info(f"Processing party: {party}")
        party_lines = predict_partyline(party, vote_embeddings, manifestos_metadata)
        vote_embeddings[f"{party}_decision"] = party_lines

    vote_embeddings.to_parquet(
        "data/parquet/predicted_votes.parquet",
        index=False,
    )
