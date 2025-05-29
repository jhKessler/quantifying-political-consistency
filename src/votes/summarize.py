from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback
from typing import Iterable
from tqdm import tqdm
from loguru import logger
import pandas as pd

from src.utils.llm import deepseek_client, openai_client
from src.utils.llm.prompts import SUMMARIZE_DRUCKSACHE





def process(idx: int, text: str) -> tuple[int, str | None]:
    try:
        return idx, openai_client.prompt_openai(
            system_prompt=SUMMARIZE_DRUCKSACHE,
            text=text,
        )
    except Exception as e:
        traceback.print_exc()
        return idx, None


def summarize_texts(content: pd.Series) -> list[str | None]:
    summarizations = [None] * len(content)

    with ThreadPoolExecutor(max_workers=2) as pool, tqdm(total=len(content)) as pbar:
        futures = [
            pool.submit(process, i, content)
            for i, content in enumerate(content)
        ]
        for future in as_completed(futures):
            i, summary = future.result()
            summarizations[i] = summary
            pbar.update(1)
    
    return summarizations