import re
import pandas as pd
from tqdm import tqdm
from loguru import logger
from src.drucksachen.parse import parse_beschlussempfehlung, extract_title_from_drucksache
from src.drucksachen import extractors

tqdm.pandas()

_MAX_LEN = 58000 * 3 # 

def _fetch_content(row: pd.Series) -> str | None:
    druck_id = row["drucksache_id"]
    if row["type"] == "Gesetzentwurf":
        return extractors.gesetzentwurf(druck_id)
    if row["type"] in {"Antrag", "Änderungsantrag", "Entschließungsantrag"}:
        return extractors.antrag(druck_id)
    logger.error(f"Unknown type {row['type']} in {druck_id}")
    return None

def build_votes_dataframe() -> pd.DataFrame:
    entry = pd.read_parquet("data/parquet/vote_entrypoints.parquet")
    beschluss = entry.query("type == 'Beschlussempfehlung'")
    direct = entry.query("type != 'Beschlussempfehlung'")

    votes: list[dict] = []
    for _, row in beschluss.iterrows():
        votes.extend(parse_beschlussempfehlung(row["vote"], row["drucksache_id"]))

    with tqdm(total=len(direct), desc="Processing direct votes") as bar:
        for _, row in direct.iterrows():
            votes.append(
                {"vote": row["vote"], "drucksache_id": row["drucksache_id"], "beschlussempfehlung": None}
            )
            bar.update(1)

    df = pd.DataFrame(votes)
    df["title"] = df["drucksache_id"].progress_apply(extract_title_from_drucksache)
    df["type"] = df["title"].str.split(" ").str[0]
    df.loc[df["type"].str.startswith("Beschlussempfehlung"), "type"] = "Beschlussempfehlung"

    df["content"] = df.progress_apply(_fetch_content, axis=1)

    pattern = re.compile(
        r'Deutscher Bundestag\s+–\s+\d+\.\s+Wahlperiode\s*\n–\s*\d+\s*–\s*\nDrucksache\s+\d+/\d+',
        flags=re.MULTILINE,
    )

    pattern2 = re.compile(
        r'Deutscher Bundestag \nDrucksache \d+/\d+ \n \d+. Wahlperiode \n\d+.\d+.\d+',
        flags=re.MULTILINE,
    )

    df['content'] = (
        df['content']
        .str.replace(pattern, '', regex=True)
        .str.replace(pattern2, '', regex=True)
        .str.replace(r'\s{2,}', ' ', regex=True)
        .str.strip()
    )

    # drop rows with content larger than deepseek context length. Should be only 4 rows. These are extremely large.
    # Since the small amount does not mess with our data, we drop them for purposes of simplicity and cost
    df = df[(df["content"].str.len() < _MAX_LEN)]


    df.to_parquet(
        "data/parquet/votes_content.parquet",
        index=False,
    )
