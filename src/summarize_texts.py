from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm
from loguru import logger
import pandas as pd
from src.utils import deepseek_utils


SYSTEM_PROMPT = """
    Fasse den Folgenden Text über den im Bundestag abgestimmt wird zusammen.
    Das Ergebnis sollte eine kurze Zusammenfassung sein, die genau beschreibt, für was abgestimmt wird.
    Versuche dich kurz zu halten, aber nenne die Wichtigsten Aspekte.
    Falls im Text enthalten ist, von wem der Antrag kommt, nenne AUF KEINEN FALL den Namen oder die Fraktion, lass unbedingt aus von wem der Antrag ist.
    Fange direkt mit der Zusammenfassung an, ohne Einleitung oder Erklärung.
"""


def process(idx: int, text: str) -> tuple[int, str | None]:
    try:
        return idx, deepseek_utils.prompt_deepseek(
            system_prompt=SYSTEM_PROMPT,
            text=text,
        )
    except Exception:
        logger.error(f"Error processing row: {text}")
        return idx, None


def summarize_texts():
    content = pd.read_parquet("data/parquet/votes_content.parquet")
    summarizations = [None] * len(content)

    with ThreadPoolExecutor(max_workers=4) as pool, tqdm(total=len(content)) as pbar:
        futures = [
            pool.submit(process, i, row["content"])
            for i, (_, row) in enumerate(content.iterrows())
        ]
        for future in as_completed(futures):
            i, summary = future.result()
            summarizations[i] = summary
            pbar.update(1)
    content["summary"] = summarizations
    content.to_parquet("data/parquet/votes_content_summarized.parquet", index=False)
