import os
import pandas as pd
from tqdm import tqdm
from src.utils.download import download_file
from src.utils import pdf_utils
from src.utils import openai_utils

SUMMARIZATION_PROMPT = """
    Filtere aus dem folgenden Text jegliche Informationen heraus, aus denen erischtlich ist, von welcher Partei das Wahlprogramm stammt.
    Das Ergebnis soll eine Liste von Punkten sein, welche die wichtigsten Punkte des Wahlprogramms zusammenfassen, ohne Namen einzelner Personen oder Parteien zu nennen.
    Gehe gerne ins Detail für jeden Punkt um keine wichtigen Informationen auszulassen. 
    Fange direkt mit dem Text an, ohne Einleitung oder Erklärung.
"""


def download_manifestos():
    urls = pd.read_csv("data/csv/manifestos.csv")

    os.makedirs("data/tmp/manifestos", exist_ok=True)
    os.makedirs("data/text/manifestos_raw", exist_ok=True)
    os.makedirs("data/text/manifestos_cleaned", exist_ok=True)

    with tqdm(total=len(urls), desc="Downloading manifestos", unit="manifesto") as pbar:
        for _, row in urls.iterrows():
            pbar.update(1)
            local_path = f"data/tmp/manifestos/{row['party']}_{row['year']}.pdf"
            download_file(row["url"], local_path)

            raw_text_path = f"data/text/manifestos_raw/{row['party']}_{row['year']}.txt"
            manifesto_text = pdf_utils.extract_content(local_path)

            with open(raw_text_path, "w", encoding="utf-8") as f:
                f.write(manifesto_text)

            cleaned_text_path = (
                f"data/text/manifestos_cleaned/{row['party']}_{row['year']}.txt"
            )
            summarized = openai_utils.prompt_openai(
                system_prompt=SUMMARIZATION_PROMPT, text=manifesto_text
            )

            with open(cleaned_text_path, "w", encoding="utf-8") as f:
                f.write(summarized)
