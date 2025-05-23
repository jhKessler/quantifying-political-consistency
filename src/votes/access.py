import os

from src.utils.download import download_file
from src.utils import pdf_utils
from loguru import logger
import pandas as pd


def assert_vote_download(vote: pd.Series):
    os.makedirs("data/tmp/votes/", exist_ok=True)
    filename = f"data/tmp/votes/{vote['id']}.pdf"
    if os.path.exists(filename):
        return
    download_file(vote["pdf_url"], filename)
    try:
        pdf_utils.extract_content(filename)
    except Exception as e:
        logger.error(f"File {filename} corrupted: {e}")
        os.remove(filename)
        raise e

def get_vote(vote_id: str, opt="text", first_page_only=False) -> str:
    filename = f"data/tmp/votes/{vote_id}.pdf"
    
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Vote {vote_id} not found. Please download it first.")

    if first_page_only:
        return pdf_utils.extract_first_page(filename, opt)
    return pdf_utils.extract_content(filename, opt)