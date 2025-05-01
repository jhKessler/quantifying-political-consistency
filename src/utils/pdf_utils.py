import pandas as pd
import requests
from tqdm import tqdm
from time import sleep
import pymupdf
from loguru import logger

def extract_first_page_text(pdf_path: str):
    """
    Extracts the text content from the first page of a PDF file.

    Args:
        pdf_path: The path to the PDF file.

    Returns:
        The text content of the first page as a string, or None if an error occurs.
    """
    doc = pymupdf.open(pdf_path)

    if doc.page_count < 1:
        logger.error(f"PDF file {pdf_path} has no pages.")
        doc.close()
        return None
    
    text = doc[0].get_text()
    doc.close()
    return text
