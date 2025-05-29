from pathlib import Path
import pandas as pd
from src.drucksachen import beschlussempfehlung, extract
from src.drucksachen.access import assert_drucksache_download
from src.drucksachen.parse import extract_title_from_drucksache
from src.utils import regex
from src.utils.llm import openai_client
from src.votes import config
from loguru import logger
from tqdm import tqdm
from src.votes.calculate_result import calculate_vote_result
from typing import TypedDict
from src.utils.download import download_file
from src.votes.get_entrypoint import get_entrypoint
from src.votes.parse import get_vote_title
from src.votes.pdf import get_vote, get_vote_path
from src.votes.summarize import summarize_texts

class VoteEntrypointDict(TypedDict):
    vote_id: str
    title: str
    type: str
    entrypoint_drucksache_title: str
    entrypoint_drucksache_id: str

def download_vote_documents(vote: pd.Series) -> pd.DataFrame:
    vote_text = get_vote(vote["vote_id"], opt="text", first_page_only=True)
    relevant_ids = regex.regex_drucksachen_ids(vote_text)

    success = []
    for relevant_id in relevant_ids:
        try:
            assert_drucksache_download(relevant_id)
            title = extract_title_from_drucksache(relevant_id)
            success.append(
                {
                    "drucksache": relevant_id,
                    "title": title,
                    "vote_id": vote["vote_id"],
                }
            )
        except Exception as e:
            logger.error(f"Error downloading {relevant_id}: {e}")
            continue
    return pd.DataFrame(success)

def build_vote(row: pd.Series) -> VoteEntrypointDict:
    # Calculate the voting result for each vote
    download_file(row['pdf_url'], get_vote_path(row['vote_id']))
    calculate_vote_result(row["vote_id"], row["xls_url"])

    vote_title = get_vote_title(row['vote_id'])
    vote_type = regex.regex_drucksachen_type(vote_title)
    drucksachen = download_vote_documents(row)
    if drucksachen.empty:
        logger.warning(f"No drucksachen found for vote {row['vote_id']}.")
        return {
            "vote_id": row["vote_id"],
            "title": vote_title,
            "type": vote_type,
            "entrypoint_drucksache_title": None,
            "entrypoint_drucksache_id": None,
        }
    entrypoint = get_entrypoint(
        vote_title,
        vote_type,
        drucksachen
    )

    return {
        "vote_id": row["vote_id"],
        "title": vote_title,
        "type": vote_type,
        "entrypoint_drucksache_title": entrypoint["entrypoint_drucksache_title"],
        "entrypoint_drucksache_id": entrypoint["entrypoint_drucksache_id"],
    }


def build_entrypoints(force_regenerate: bool = False) -> pd.DataFrame:
    if not force_regenerate and Path(config.ENTRYPOINTS_PARQUET_PATH).exists():
        logger.info("Loading existing entrypoints...")
        return pd.read_parquet(config.ENTRYPOINTS_PARQUET_PATH)
    
    urls = pd.read_parquet(config.URLS_PARQUET_PATH)

    logger.info("Calculating vote results...")
    entrypoints: VoteEntrypointDict = []
    with tqdm(
        total=len(urls),
        desc="Calculating vote results",
        unit="vote",
    ) as pbar:
        for _, row in urls.iterrows():
            try:
                entrypoint = build_vote(row)
                entrypoints.append(entrypoint)
            except Exception as e:
                logger.error(f"Error building vote {row['vote_id']}: {e}")
            pbar.update(1)
    entrypoints_df = pd.DataFrame(entrypoints)
    entrypoints_df.to_parquet(config.ENTRYPOINTS_PARQUET_PATH, index=False)
    return entrypoints_df

def process_beschlussempfehlungen(beschlussempfehlungen: pd.DataFrame) -> pd.DataFrame:
    underlying = beschlussempfehlungen.apply(
        lambda row: beschlussempfehlung.build(row["vote_id"], row["entrypoint_drucksache_id"]),
        axis=1
    )
    flattened_list = [
        item for sublist in underlying.tolist() for item in sublist
    ]
    beschlussempfehlung_drucksachen = pd.DataFrame(flattened_list).rename(columns={
        "entrypoint_drucksache_title": "drucksache_title",
        "entrypoint_drucksache_id": "drucksache_id"
    })
    return beschlussempfehlung_drucksachen

def clean_entrypoints(entrypoints: pd.DataFrame) -> pd.DataFrame:
    entrypoints = entrypoints[[
        "vote_id", "type", "entrypoint_drucksache_title", "entrypoint_drucksache_id"
    ]].rename(columns={
        "entrypoint_drucksache_title": "drucksache_title",
        "entrypoint_drucksache_id": "drucksache_id"
    })
    entrypoints["beschlussempfehlung"] = None
    return entrypoints

def combine_entrypoints_and_beschlussempfehlungen(entrypoints: pd.DataFrame) -> pd.DataFrame:
    entrypoints = entrypoints[entrypoints["entrypoint_drucksache_id"].notna()]
    beschlussempfehlungen = process_beschlussempfehlungen(entrypoints[entrypoints["type"] == "Beschlussempfehlung"])
    entrypoints = clean_entrypoints(entrypoints[entrypoints["type"] != "Beschlussempfehlung"])
    all_votes = pd.concat([
        entrypoints,
        beschlussempfehlungen
    ])
    all_votes = all_votes[all_votes["type"].isin(config.RELEVANT_TYPES)]
    return all_votes


def extract_content(row: pd.Series) -> str | None:
    druck_id = row["drucksache_id"]
    if row["type"] == "Gesetzentwurf":
        return extract.gesetzentwurf(druck_id)
    if row["type"] in {"Antrag", "Änderungsantrag", "Entschließungsantrag"}:
        return extract.antrag(druck_id)
    logger.error(f"Unknown type {row['type']} in {druck_id}")
    return None

def filter_votes_by_content(all_votes: pd.DataFrame) -> pd.DataFrame:
    before = len(all_votes)
    all_votes = all_votes[
        (all_votes["content"].notna()
        & all_votes["content"].str.len().lt(config.MAX_CONTENT_CHARS))
    ]
    after = len(all_votes)
    logger.info(f"Filtered {before - after} entries with too long content or no content")
    return all_votes


def build():
    tqdm.pandas()

    entrypoints = build_entrypoints()

    all_votes = combine_entrypoints_and_beschlussempfehlungen(entrypoints)
    logger.info("Extracting content from drucksachen...")
    all_votes["content"] = (
        all_votes.progress_apply(extract_content, axis=1)
        .str.replace(r"[\s\n]+", " ", regex=True)
        .str.strip()
    )
    all_votes = filter_votes_by_content(all_votes)
    logger.info("Summarizing texts...")
    all_votes["summary"] = summarize_texts(all_votes["content"])
    logger.info("Calculating embeddings for summaries...")
    all_votes["summary_embedding"] = all_votes["summary"].progress_apply(
        openai_client.get_embedding
    )
    all_votes["date"] = pd.to_datetime(
        all_votes["vote_id"].str.split("_").str[0], format="%Y%m%d"
    )
    logger.info("Saving data to parquet...")
    all_votes.to_parquet(config.OUTPUT_PARQUET_PATH, index=False)
