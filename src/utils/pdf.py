import re
from time import sleep

import pandas as pd
import pymupdf
import requests
from loguru import logger
from tqdm import tqdm


def extract_first_page(pdf_path: str, opt="text"):
    """
    Extracts the text content from the first page of a PDF file.

    Args:
        pdf_path: The path to the PDF file.

    Returns:
        The text content of the first page as a string, or None if an error occurs.
    """

    with pymupdf.open(pdf_path) as doc:
        if doc.page_count < 1:
            logger.error(f"PDF file {pdf_path} has no pages.")
            return None

        content = doc[0].get_text(opt)
        if opt == "blocks":
            content = list(sorted(content, key=lambda x: x[1]))
        return content


def extract_content(path: str, opt="text") -> str | list[tuple]:
    with pymupdf.open(path) as doc:
        if opt == "text":
            all_pages = "\n".join(page.get_text() for page in doc)
            clean = re.sub(r"\s+", " ", all_pages)
            return clean.strip()
        elif opt == "blocks":
            all_blocks = []
            for page in doc:
                blocks = sorted(page.get_text("blocks"), key=lambda x: x[1])
                all_blocks.extend(blocks)
            return all_blocks
