from pathlib import Path

import pandas as pd
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from loguru import logger

from src.config import EMBEDDING_MODEL, PARTIES
from src.manifestos import config

embeddings = OpenAIEmbeddings(model=EMBEDDING_MODEL)
splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)


def get_rag_embeddings(party: str) -> dict[str, Chroma]:
    if party not in PARTIES:
        raise ValueError(f"Party {party} is not supported. Choose from {PARTIES}.")
    logger.info(f"Creating RAG embeddings for party: {party}")
    Path("data/vectorstores/").mkdir(parents=True, exist_ok=True)
    manifesto_df = pd.read_parquet(config.CLEANED_PARQUET_PATH).query("party == @party")
    vectorstores = {}
    for _, row in manifesto_df.iterrows():
        store_path = Path(f"data/vectorstores/{row['party']}_{row['year']}")
        if store_path.exists():
            vectorstores[row["year"]] = Chroma(
                persist_directory=str(store_path), embedding_function=embeddings
            )
        else:
            docs = splitter.create_documents([row["summary"]])
            vs = Chroma.from_documents(
                docs, embeddings, persist_directory=str(store_path)
            )
            vectorstores[row["year"]] = vs
    return vectorstores
