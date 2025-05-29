import time
from pathlib import Path

import pandas as pd
import requests
from loguru import logger

from src.utils.pdf import extract_first_page


def download_file(fileurl: str, save_to_path: str, delay: int = 0.5) -> None:
    """
    Downloads a file from a given URL and saves it to disk.

    Args:
        fileurl (str): The URL to download the file from.
        save_to_path (str): The file path to save the downloaded file to.
    """
    if Path(save_to_path).exists():
        return

    r = requests.get(
        fileurl,
        stream=True,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3"
        },
    )
    r.raise_for_status()
    with open(save_to_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)

    time.sleep(delay)  # Delay to avoid overwhelming the server

    if save_to_path.endswith(".pdf"):
        # try to open the file to ensure it was downloaded correctly
        try:
            extract_first_page(save_to_path)
        except Exception as e:
            logger.error(
                f"Error extracting first page from {save_to_path}: {e}. Deleting file."
            )
            Path(save_to_path).unlink(missing_ok=True)
            raise RuntimeError(f"Downloaded file {save_to_path} is not a valid PDF.")
    elif save_to_path.endswith(".xls") or save_to_path.endswith(".xlsx"):
        try:
            pd.read_excel(save_to_path)
        except Exception as e:
            logger.error(
                f"Error reading Excel file {save_to_path}: {e}. Deleting file."
            )
            Path(save_to_path).unlink(missing_ok=True)
            raise RuntimeError(
                f"Downloaded file {save_to_path} is not a valid Excel file."
            )
