from pathlib import Path

import pandas as pd
from loguru import logger
from tqdm import tqdm

from src.manifestos import config
from src.utils import pdf
from src.utils.download import download_file
from src.utils.llm import openai_client, prompts


def download_manifestos():
    Path("data/manifestos/pdf").mkdir(parents=True, exist_ok=True)
    manifestos = pd.read_csv("input/manifestos.csv")
    output_path = Path(config.CLEANED_PARQUET_PATH)

    already_downloaded = (
        pd.read_parquet(output_path)
        if output_path.exists()
        else pd.DataFrame(
            columns=["party", "year", "summary", "raw_text", "valid_starting"]
        )
    )

    output = []

    with tqdm(
        total=len(manifestos),
        desc="Downloading and summarizing manifestos",
        unit="manifesto",
    ) as pbar:
        for _, row in manifestos.iterrows():
            pbar.update(1)
            mask = (already_downloaded["party"] == row["party"]) & (
                already_downloaded["year"] == row["year"]
            )
            if mask.any():
                output.append(already_downloaded[mask].iloc[0].to_dict())
                logger.info(
                    f"Manifesto for {row['party']} {row['year']} already downloaded. Skipping."
                )
                continue
            local_path = f"data/manifestos/pdf/{row['party']}_{row['year']}.pdf"
            try:
                download_file(row["url"], local_path)
            except RuntimeError:
                logger.error(
                    f"Failed to download manifesto for {row['party']} {row['year']}. URL: {row['url']}"
                )
                continue
            content = pdf.extract_content(local_path)
            summarized = openai_client.prompt_openai(
                system_prompt=prompts.SUMMARIZE_MANIFESTO, text=content
            )
            output.append(
                {
                    "party": row["party"],
                    "year": row["year"],
                    "summary": summarized,
                    "raw_text": content,
                    "valid_starting": row["valid_starting"],
                }
            )

    logger.info(f"Saving cleaned manifestos to parquet file at {output_path}.")
    df = pd.DataFrame(output)
    df.to_parquet(output_path, index=False)
    return df
