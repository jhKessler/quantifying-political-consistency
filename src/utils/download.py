import requests
from loguru import logger
import os


def download_file(fileurl: str, save_to_path: str):
    """
    Downloads a file from a given URL and saves it to disk.

    Args:
        fileurl (str): The URL to download the file from.
        save_to_path (str): The file path to save the downloaded file to.
    """
    if os.path.exists(save_to_path):
        return

    r = requests.get(fileurl, stream=True)
    r.raise_for_status()
    with open(save_to_path, "wb") as f:
        for chunk in r.iter_content(chunk_size=1024):
            if chunk:
                f.write(chunk)
    return save_to_path
