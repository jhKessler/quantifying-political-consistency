import pandas as pd

from src import config
from src.enums import VoteResultEnum
from src.votes.config import RESULT_CSV_FOLDER


def vote_counts_to_result(votes: pd.Series) -> str:
    return votes[
        [
            VoteResultEnum.ANNAHME.value,
            VoteResultEnum.ABLEHNUNG.value,
            VoteResultEnum.ENTHALTUNG.value,
        ]
    ].idxmax()


def flip_vote_result(vote_result: str) -> str:
    if vote_result == VoteResultEnum.ANNAHME.value:
        return VoteResultEnum.ABLEHNUNG.value
    elif vote_result == VoteResultEnum.ABLEHNUNG.value:
        return VoteResultEnum.ANNAHME.value
    if vote_result == VoteResultEnum.ENTHALTUNG.value:
        return VoteResultEnum.ENTHALTUNG.value
    raise ValueError(
        f"Invalid vote result: {vote_result}. Expected one of {VoteResultEnum.ANNAHME.value}, "
        f"{VoteResultEnum.ABLEHNUNG.value}, {VoteResultEnum.ENTHALTUNG.value}."
    )


def build_party_df(party: str) -> pd.DataFrame:
    df = pd.read_csv(f"{RESULT_CSV_FOLDER}/{party}.csv")
    df["ground_truth"] = df.apply(vote_counts_to_result, axis=1)
    df["party"] = party
    return df[["vote_id", "ground_truth", "party"]]


def load_party_results() -> pd.DataFrame:
    party_results = [build_party_df(party) for party in config.PARTIES]
    return pd.concat(party_results, ignore_index=True)


def load_predictions() -> pd.DataFrame:
    df = pd.read_parquet("data/predictions.parquet")
    return df.drop(columns=["content"]).rename(columns={"drucksache_title": "title"})


def merge_with_ground_truth(
    predictions: pd.DataFrame, ground_truth: pd.DataFrame
) -> pd.DataFrame:
    merged = predictions.merge(ground_truth, on=["vote_id", "party"], how="left")
    return merged[merged["ground_truth"].notna()]


def apply_flipped_ground_truth(df: pd.DataFrame) -> pd.DataFrame:
    mask = df["beschlussempfehlung"] == VoteResultEnum.ABLEHNUNG.value
    df.loc[mask, "ground_truth"] = df.loc[mask, "ground_truth"].apply(flip_vote_result)
    return df


def prepare_final_dataset() -> pd.DataFrame:
    party_results = load_party_results()
    predictions = load_predictions()
    with_ground_truth = merge_with_ground_truth(predictions, party_results)
    return apply_flipped_ground_truth(with_ground_truth)
