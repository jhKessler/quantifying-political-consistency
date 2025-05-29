from pathlib import Path

from src.utils.download import download_file
from src.utils import pdf
from loguru import logger
import pandas as pd

def get_vote_path(vote_id: str) -> str:
    return f"data/votes/all/{vote_id}/result.pdf"


def assert_vote_download(vote: pd.Series):
    Path(f"data/votes/pdf/{vote['id']}/result.pdf").mkdir(parents=True, exist_ok=True)
    filename = f"data/tmp/votes/{vote['id']}.pdf"
    if Path(filename).exists():
        return
    download_file(vote["pdf_url"], filename)
    try:
        pdf.extract_content(filename)
    except Exception as e:
        logger.error(f"File {filename} corrupted: {e}")
        Path(filename).unlink(missing_ok=True)
        raise e


def get_vote(vote_id: str, opt="text", first_page_only=False) -> str:
    filename = get_vote_path(vote_id)
    if not Path(filename).exists():
        raise FileNotFoundError(f"Vote {vote_id} not found. Please download it first.")

    if first_page_only:
        return pdf.extract_first_page(filename, opt)
    return pdf.extract_content(filename, opt)
