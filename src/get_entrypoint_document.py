import os
import pandas as pd
from loguru import logger
from tqdm import tqdm
from src.utils import openai_utils


def get_entrypoint_documents():
    votes = pd.read_parquet("data/parquet/votes_base.parquet")
    drucksachen = pd.read_parquet("data/parquet/drucksachen_base.parquet")

    if os.path.exists("data/parquet/vote_entrypoints.parquet"):
        logger.info("Vote entrypoints already exist. Skipping...")
        return
    drucksachen_by_vote = drucksachen.groupby("vote")

    all_entrypoints = []

    with tqdm(total=len(votes), desc="Matching closest drucksache") as pbar:
        for _, vote in votes.iterrows():
            pbar.update(1)
            if vote["id"] not in drucksachen_by_vote.groups:
                logger.warning(f"Vote {vote['id']} Does not have any drucksachen")
                continue
            drucksachen_for_this_vote = drucksachen_by_vote.get_group(vote["id"]).copy()
            available_drucksachen = [{"index": index, "title": title} for index, title in enumerate(drucksachen_for_this_vote["title"].values)]
            
            if len(available_drucksachen) == 1:
                matched_drucksache = drucksachen_for_this_vote.iloc[0]
            else:
                match = openai_utils.match_drucksache_to_vote(
                    vote["title"],
                    available_drucksachen
                )
                matched_drucksache = drucksachen_for_this_vote.iloc[match.index]

            all_entrypoints.append({
                "vote": vote["id"],
                "drucksache_title": matched_drucksache["title"],
                "drucksache_id": matched_drucksache["drucksache"],
            })

    entrypoints = pd.DataFrame(all_entrypoints)
    entrypoints["type"] = entrypoints["drucksache_title"].str.split(" ").str[0]
    entrypoints.loc[entrypoints["type"].str.startswith("Beschlussempfehlung"), "type"] = "Beschlussempfehlung"
    # drop all other types
    entrypoints = entrypoints[entrypoints["type"].isin(["Gesetzentwurf", "Beschlussempfehlung", "Antrag", "Änderungsantrag"])]
    entrypoints.to_parquet("data/parquet/vote_entrypoints.parquet", index=False)
