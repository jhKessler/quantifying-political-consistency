import os

from src.utils.download import download_file
from src.utils import pdf_utils
from loguru import logger

def assert_drucksache_download(drucksachen_id: str):
    os.makedirs("data/tmp/drucksachen", exist_ok=True)
    filename = f"data/tmp/drucksachen/{drucksachen_id.replace('/', '_')}.pdf"
    if os.path.exists(filename):
        return
    bundestag_number, vote_number = drucksachen_id.split("/")
    zeroes_to_add = max(0, 5 - len(vote_number))
    vote_number = f"{'0' * zeroes_to_add}{vote_number}"
    url = f"https://dserver.bundestag.de/btd/{bundestag_number}/{vote_number[:3]}/{bundestag_number}{vote_number}.pdf"
    download_file(url, filename)
    try:
        pdf_utils.extract_content(filename)
    except Exception as e:
        logger.error(f"File {filename} corrupted: {e}")
        os.remove(filename)
        raise e

def get_drucksache(drucksachen_id: str, opt="text", first_page_only=False) -> str:
    """
    Downloads the drucksache with the given ID and returns the path to the downloaded file.
    
    Args:
        drucksachen_id (str): The ID of the drucksache to download.
    
    Returns:
        str: The path to the downloaded file.
    """
    path = f"data/tmp/drucksachen/{drucksachen_id.replace('/', '_')}.pdf"
    assert_drucksache_download(drucksachen_id)
    
    if first_page_only:
        return pdf_utils.extract_first_page(path, opt)
    return pdf_utils.extract_content(path, opt)