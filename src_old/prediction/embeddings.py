import os

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_openai import OpenAIEmbeddings
from loguru import logger

from src.prediction import config

embeddings = OpenAIEmbeddings(model=config.EMBEDDING_MODEL)


def embed_manifestos(party: str) -> dict[str, Chroma]:
    """
    Embeds the manifestos for a given party, returns them and saves them in a vector store.
    """
    logger.info(f"Embedding manifestos for {party}")
    vs_root = "data/vectorstores"
    os.makedirs(vs_root, exist_ok=True)
    splitter = RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=100)

    manifesto_dir = "data/text/manifestos_cleaned"
    manifesto_paths = [
        os.path.join(manifesto_dir, p)
        for p in os.listdir(manifesto_dir)
        if p.startswith(party)
    ]

    docs_by_year = {}
    for path in manifesto_paths:
        year = os.path.basename(path).split("_")[-1].replace(".txt", "")
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
        docs_by_year[year] = splitter.create_documents([text])

    vectorstores = {}
    for year, docs in docs_by_year.items():
        store_path = os.path.join(vs_root, f"{party}_{year}")
        if os.path.exists(store_path):
            vectorstores[year] = Chroma(
                persist_directory=store_path, embedding_function=embeddings
            )
        else:
            vs = Chroma.from_documents(docs, embeddings, persist_directory=store_path)
            vectorstores[year] = vs
    return vectorstores
