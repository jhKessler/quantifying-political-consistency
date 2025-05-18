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
    pattern = re.compile(r"\b\d{2}/\d+\b")

    matches = pattern.findall(vote_name)
    return list(set(matches))


def regex_drucksache(first_page_text: str) -> list[str]:
    """
    Extracts Drucksache IDs from the first page text using regex.

    Args:
        first_page_text (str): The text of the first page of the PDF.

    Returns:
        list[str]: A list of extracted Drucksache IDs.
    """
    # example "Drucksache 20/15096" only extract first occurrence
    pattern = re.compile(r"Drucksache\s+(\d{1,2}/\d+)")
    matches = pattern.findall(first_page_text)
    if matches:
        return matches[0].replace("/", "_")
    return None


def regex_date(first_page_text: str) -> str:
    """
    Extracts the date from the first page text using regex.

    Args:
        first_page_text (str): The text of the first page of the PDF.

    Returns:
        str: The extracted date.
    """
    pattern = re.compile(r"(\d{1,2}\.\s*\d{1,2}\.\s*\d{4})")
    matches = pattern.findall(first_page_text)
    if matches:
        return re.sub("\s+", "", matches[0])
    return None


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

def extract_document_type(first_page_text: str) -> str:
    lines = [line for line in first_page_text.splitlines() if line.strip()]
    return lines[4].strip()


def download_vote_texts(vote: pd.Series) -> list[dict]:
    """
    Downloads the vote texts from the given URL and saves it to the specified directory.

    Args:
        vote (pd.Series): A row from the DataFrame containing vote information.
        download_dir (str): The directory to save the downloaded file.
    """
    required_columns = ["name", "id", "pdf_url"]
    for col in required_columns:
        if col not in vote:
            raise ValueError(f"Missing required column: {col}")

    os.makedirs(f"data/tmp/vote_pdf/{vote['id']}/drucksachen", exist_ok=True)

    # extract all relevant drucksachen for this vote
    local_path = f"data/tmp/vote_pdf/{vote['id']}/vote.pdf"
    download_file(vote["pdf_url"], local_path)
    relevant_ids = extract_relevant_ids(local_path)

    documents = []

    for index, relevant_id in enumerate(relevant_ids):
        bundestag_number, vote_number = relevant_id.split("/")
        zeroes_to_add = max(0, 5 - len(vote_number))
        vote_number = f"{'0' * zeroes_to_add}{vote_number}"
        url = f"https://dserver.bundestag.de/btd/{bundestag_number}/{vote_number[:3]}/{bundestag_number}{vote_number}.pdf"
        filename = f"data/tmp/vote_pdf/{vote['id']}/drucksachen/{index}.pdf"
        download_file(url, filename)

        first_page_text = pdf_utils.extract_first_page_text(filename)
        if not first_page_text:
            logger.error(f"Failed to extract text from {filename}")
            continue

        drucksache_id = regex_drucksache(first_page_text)
        date = regex_date(first_page_text)
        document_type = extract_document_type(first_page_text)

        if not drucksache_id or not date:
            logger.error(f"Failed to extract drucksache or date from {filename} drucksache: {drucksache_id} date: {date}")
            continue
        
        documents.append({
            "vote_id": vote["id"],
            "filename": filename,
            "drucksache": drucksache_id,
            "date": date,
            "document_type": document_type
        })
    return documents

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
    all_documents = []
    for _, vote in df.iterrows():
        pbar.update(1)
        try:
            all_documents.extend(download_vote_texts(vote))
        except Exception as e:
            logger.error(f"Failed to download or process {vote['name']}: {e}")
            logger.error(f"Vote data: {vote}")
    
    pbar.close()
    logger.info("Vote texts gathered successfully.")
    logger.info("Building dataframe of vote texts...")
    all_texts = pd.DataFrame(all_documents).drop_duplicates(subset=["vote_id", "drucksache"]).to_parquet("data/parquet/vote_texts.parquet", index=False)
    logger.info("Dataframe of vote texts built successfully. Saved to data/parquet/vote_texts.parquet")
    logger.info("Gathering vote texts completed.")
    return all_texts
