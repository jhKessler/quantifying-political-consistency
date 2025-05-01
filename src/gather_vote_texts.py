import os
import pandas as pd
import re
from loguru import logger
from src.utils.download import download_file
from src.utils import pdf_utils
from tqdm import tqdm


def regex_relevant_ids(vote_name: str) -> list[str]:
    """
    Extracts relevant IDs from the vote name using regex.

    Args:
        vote_name (str): The name of the vote.

    Returns:
        list[str]: A list of extracted IDs.
    """
    pattern = re.compile(r"\b\d{2}/\d*\b")
    matches = pattern.findall(vote_name)
    return list(set(matches))


def extract_relevant_ids(vote_pdf_path: str) -> list[str]:
    first_page_text = pdf_utils.extract_first_page_text(vote_pdf_path)
    if first_page_text is None:
        logger.error(f"Failed to extract text from {vote_pdf_path}")
        return []
    relevant_ids = regex_relevant_ids(first_page_text)
    if not relevant_ids:
        logger.warning(f"No relevant IDs found in the first page of {vote_pdf_path}")
        return []
    return relevant_ids


def download_vote_text(vote: pd.Series):
    """
    Downloads the vote text from the given URL and saves it to the specified directory.

    Args:
        vote (pd.Series): A row from the DataFrame containing vote information.
        download_dir (str): The directory to save the downloaded file.
    """
    required_columns = ["name", "id", "pdf_url"]
    for col in required_columns:
        if col not in vote:
            raise ValueError(f"Missing required column: {col}")

    os.makedirs("data/tmp/vote_pdf", exist_ok=True)
    local_path = f"data/tmp/vote_pdf/{vote['id']}.pdf"
    download_file(vote["pdf_url"], local_path)

    relevant_ids = extract_relevant_ids(local_path)

    for index, relevant_id in enumerate(relevant_ids):
        bundestag_number, vote_number = relevant_id.split("/")
        url = f"https://dserver.bundestag.de/btd/{bundestag_number}/{vote_number[:3]}/{bundestag_number}{vote_number}.pdf"
        logger.info(
            f"Downloading {url} to data/tmp/texts/{vote['id']}/{vote['id']}_{index}.pdf"
        )
        os.makedirs(f"data/tmp/texts/{vote['id']}", exist_ok=True)
        filename = f"data/tmp/texts/{vote['id']}/{vote['id']}_{index}.pdf"
        if os.path.exists(filename):
            logger.info(f"File already exists: {filename}")
            continue
        download_file(url, filename)


def gather_vote_texts():
    """
    Orchestrates the process of gathering vote texts from the Bundestag website.

    - Downloads the vote text PDFs
    - Extracts relevant IDs from the first page of each PDF
    - Saves the extracted IDs to a local directory
    """
    logger.info("Gathering vote texts from Bundestag website...")

    df = pd.read_parquet("data/parquet/votes.parquet")

    pbar = tqdm(total=len(df), desc="Downloading vote texts", unit="vote")

    for _, vote in df.iterrows():
        pbar.update(1)
        try:
            download_vote_text(vote)
        except Exception as e:
            logger.error(f"Failed to download or process {vote['name']}: {e}")
