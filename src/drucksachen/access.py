from pathlib import Path
from src.utils.download import download_file
from src.utils import pdf
from loguru import logger

def get_drucksache_path(drucksachen_id: str) -> str:
    return f"data/drucksachen/{drucksachen_id.replace('/', '_')}.pdf"

def assert_drucksache_download(drucksachen_id: str):
    Path("data/drucksachen").mkdir(parents=True, exist_ok=True)
    filename = get_drucksache_path(drucksachen_id)
    if Path(filename).exists():
        return
    bundestag_number, vote_number = drucksachen_id.split("/")
    zeroes_to_add = max(0, 5 - len(vote_number))
    vote_number = f"{'0' * zeroes_to_add}{vote_number}"
    url = f"https://dserver.bundestag.de/btd/{bundestag_number}/{vote_number[:3]}/{bundestag_number}{vote_number}.pdf"
    download_file(url, filename)
    try:
        pdf.extract_content(filename)
    except Exception as e:
        logger.error(f"File {filename} corrupted: {e}")
        Path(filename).unlink(missing_ok=True)
        raise e


def get_drucksache(drucksachen_id: str, opt="text", first_page_only=False) -> str:
    """
    Downloads the drucksache with the given ID and returns the path to the downloaded file.

    Args:
        drucksachen_id (str): The ID of the drucksache to download.

    Returns:
        str: The path to the downloaded file.
    """
    path = get_drucksache_path(drucksachen_id)
    assert_drucksache_download(drucksachen_id)

    if first_page_only:
        return pdf.extract_first_page(path, opt)
    return pdf.extract_content(path, opt)
