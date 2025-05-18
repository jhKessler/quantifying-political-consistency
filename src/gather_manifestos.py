import os
import pandas as pd
from tqdm import tqdm
from src.utils.download import download_file
from src.utils import pdf_utils


def download_manifestos():
    urls = pd.read_csv("data/csv/manifestos.csv")

    os.makedirs("data/tmp/manifestos", exist_ok=True)
    os.makedirs("data/text/manifestos", exist_ok=True)

    pbar = tqdm(total=len(urls), desc="Downloading manifestos", unit="manifesto")
    for _, row in urls.iterrows():
        pbar.update(1)
        local_path = f"data/tmp/manifestos/{row['party']}_{row['year']}.pdf"
        download_file(row["url"], local_path)

        text_path = f"data/text/manifestos/{row['party']}_{row['year']}.txt"
        manifesto_text = pdf_utils.extract_pdf_text(local_path)

        with open(text_path, "w", encoding="utf-8") as f:
            f.write(manifesto_text)
