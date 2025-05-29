from pathlib import Path

import numpy as np
import pandas as pd
from loguru import logger

from src.feature_engineering import config
from src.utils.llm.openai_client import get_embedding


def get_embeddings() -> pd.DataFrame:
    if Path(config.CATEGORY_EMBEDDINGS_PATH).exists():
        logger.info("Loading existing categories embeddings...")
        categories = pd.read_parquet(config.CATEGORY_EMBEDDINGS_PATH)
    else:
        logger.info("Creating categories embeddings...")
        categories = pd.DataFrame(
            {
                "category": config.CATEGORIES,
            }
        )
        categories["embedding"] = categories["category"].apply(get_embedding)
        categories.to_parquet(config.CATEGORY_EMBEDDINGS_PATH, index=False)
    return categories


def get_closest_category(summary_embedding: np.array, categories: pd.DataFrame) -> str:
    distances = categories["embedding"].apply(
        lambda x: np.linalg.norm(np.array(x) - summary_embedding)
    )
    closest_index = distances.idxmin()
    return categories.iloc[closest_index]["category"]


def get_category_column(embeddings: pd.Series) -> pd.Series:
    logger.info("Calculating closest categories through embeddings")
    categories = get_embeddings()
    return embeddings.apply(lambda x: get_closest_category(np.array(x), categories))
