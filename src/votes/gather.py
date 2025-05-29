import re
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup, ResultSet, Tag
from loguru import logger
from tqdm import tqdm

from src.votes import config


def get_votes_tablerows(start_offset: int, limit: int = 30) -> ResultSet:
    url = (
        "https://www.bundestag.de/ajax/filterlist/de/parlament/plenum/abstimmung/"
        f"liste/462112-462112?limit={limit}&noFilterSet=false&offset={start_offset}"
    )
    response = requests.get(url)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    # first row is the table header, so skip it
    return soup.find_all("tr")[1:]


def parse_vote_row(vote_element: Tag) -> dict:
    _, _, data_cell, _ = vote_element.find_all("td")
    data_links = data_cell.find_all("a")
    pdf_link = None
    xls_link = None

    for link in data_links:
        if link.get("title", "").startswith("PDF"):
            pdf_link = link["href"]
        elif link.get("title", "").startswith("XLS"):
            xls_link = link["href"]

    if not xls_link or not pdf_link:
        raise ValueError("Vote row does not contain all necessary document urls.")

    id_pattern = r"(\d{8})(?:_(\d+))?"
    only_filename = Path(xls_link).name
    match = re.search(id_pattern, only_filename)
    day, number = match.groups()
    abstimmungs_id = "_".join(match.groups()) if number else day

    return {
        "vote_id": abstimmungs_id,
        "xls_url": xls_link or None,
        "pdf_url": pdf_link or None,
    }


def scrape_urls(limit: int = 30, sleep_duration: float = 0.5) -> list[dict]:
    if Path(config.URLS_PARQUET_PATH).exists():
        logger.info("Vote metadata already exists. Skipping scraping.")
        return
    Path("data/votes/").mkdir(parents=True, exist_ok=True)
    logger.info("Gathering vote metadata from Bundestag website...")
    data = []
    current_offset = 0

    with tqdm(desc="Scraping vote metadata", unit="vote") as pbar:
        while True:
            votes = get_votes_tablerows(current_offset, limit=limit)

            if not votes or len(votes) < limit:
                break

            current_offset += limit
            pbar.update(limit)

            time.sleep(sleep_duration)

            for idx, vote in enumerate(votes):
                try:
                    vote_data = parse_vote_row(vote)
                    data.append(vote_data)
                except Exception as e:
                    logger.error(
                        f"Unable to parse vote at offset {current_offset + idx} due to {e}"
                    )

    logger.info(f"Gathered {len(data)} votes.")
    pd.DataFrame(data).to_parquet(config.URLS_PARQUET_PATH, index=False)
