import os
import re
import time
import dateparser
import pandas as pd
import requests
from bs4 import BeautifulSoup, ResultSet, Tag
from tqdm import tqdm
from loguru import logger
import uuid


def get_votes_html(start_offset: int, limit: int = 30) -> ResultSet:
    """Fetches a block of vote listings from the Bundestag website.

    Args:
        start_offset (int): The current offset on the Bundestag website's paginated results.
        limit (int, optional): How many items the endpoint returns at once. Defaults to 30.

    Returns:
        ResultSet: A BeautifulSoup ResultSet containing <tr> elements for the table rows (excluding header).
    """
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
    """Parses the HTML <tr> element for a single vote into a dictionary of fields.

    Args:
        vote_element (Tag): A BeautifulSoup Tag representing the <tr> element for one vote row.

    Returns:
        dict: A dictionary with parsed fields: 'name', 'date', 'topic', 'xls_url', 'pdf_url', 'doctype'.
    """
    date_cell, topic_cell, data_cell, doctype_cell = vote_element.find_all("td")
    name_tag = data_cell.find(class_="bt-documents-description").find("p")
    name = name_tag.text.strip() if name_tag else ""

    data_links = data_cell.find_all("a")
    pdf_link = None
    xls_link = None

    for link in data_links:
        if link.get("title", "").startswith("PDF"):
            pdf_link = link["href"]
        elif link.get("title", "").startswith("XLS"):
            xls_link = link["href"]

    pattern = r"(\d{8})(?:_(\d+))?"
    try:
        only_filename = os.path.basename(xls_link)
        match = re.search(pattern, only_filename)
        day, number = match.groups()
        abstimmungs_id = "_".join(match.groups()) if number else day
    except Exception as e:
        logger.error(f"Failed to extract ID from {xls_link}")
        abstimmungs_id = None

    return {
        "id": abstimmungs_id,  # Generate a unique ID for each vote
        "name": name,
        "date": date_cell.text.strip(),
        "topic": topic_cell.text.strip(),
        "xls_url": xls_link or None,
        "pdf_url": pdf_link or None,
        "doctype": doctype_cell.text.strip(),
    }


def scrape_votes(limit: int = 30, sleep_duration: float = 0.5) -> list[dict]:
    """Main scraper function that iterates through all vote listings until no more full pages are found.

    Args:
        limit (int, optional): How many items per page. Defaults to 30 (the page size the Bundestag site uses).
        sleep_duration (float, optional): Delay in seconds between requests to avoid overwhelming the server.

    Returns:
        list[dict]: A list of dictionaries representing all parsed vote entries.
    """
    data = []
    start_offset = 0
    pbar = tqdm(desc="Scraping", unit="vote")

    while True:
        votes = get_votes_html(start_offset, limit=limit)

        if not votes or len(votes) < limit:
            break

        start_offset += limit
        pbar.update(limit)

        time.sleep(sleep_duration)

        for idx, vote in enumerate(votes):
            try:
                vote_data = parse_vote_row(vote)
                data.append(vote_data)
            except Exception as e:
                logger.warning(
                    f"Unable to parse vote at offset {start_offset + idx} due to {e}"
                )

    pbar.close()
    return data


def clean_vote_data(data: list[dict]) -> pd.DataFrame:
    """Cleans and transforms the scraped vote data.

    Args:
        data (list[dict]): The raw list of vote dictionaries from scrape_votes().

    Returns:
        pd.DataFrame: A cleaned Pandas DataFrame with valid dates, xls links, and a tidied 'name' field.
    """
    df = pd.DataFrame(data)
    df["date"] = df["date"].apply(dateparser.parse)
    df = df[(df["date"].notna()) & (df["xls_url"].notna())]
    df["name"] = df["name"].str.split(":", n=1).str[-1].str.strip()
    df.drop(columns=["doctype", "topic"], inplace=True)
    return df


def gather_vote_urls():
    """Orchestrates the full ETL (Extract, Transform, Load) workflow.

    - Scrapes vote URLs from the Bundestag website
    - Cleans the data and produces a final Excel file
    """
    logger.info("Scraping vote URLs from Bundestag website...")
    os.makedirs("data/parquet", exist_ok=True)
    raw_data = scrape_votes()
    clean_df = clean_vote_data(raw_data)
    clean_df.to_parquet("data/parquet/votes.parquet", index=False)
