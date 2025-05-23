import pandas as pd
from src.votes.build import build_vote, download_vote_documents
from tqdm import tqdm
from loguru import logger
from src.drucksachen.processor import build_votes_dataframe


def build_data():
    """
    Main function to build the data for votes and drucksachen.
    It downloads the vote documents and builds the metadata for each vote.
    """
    votes = pd.read_parquet("data/parquet/votes.parquet")

    all_votes = None
    all_drucksachen = None

    for i, vote in tqdm(votes.iterrows()):
        try:
            vote_obj = build_vote(vote)
            documents = download_vote_documents(vote)
        except Exception as e:
            logger.error(f"Error processing vote {vote['id']}: {e}")
            continue

        if all_votes is None:
            all_votes = vote_obj
        else:
            all_votes = pd.concat([all_votes, vote_obj], ignore_index=True)

        if all_drucksachen is None:
            all_drucksachen = documents
        else:
            all_drucksachen = pd.concat([all_drucksachen, documents], ignore_index=True)

    all_drucksachen.to_parquet("data/parquet/drucksachen_base.parquet", index=False)
    all_votes.to_parquet("data/parquet/votes_base.parquet", index=False)
    build_votes_dataframe()
