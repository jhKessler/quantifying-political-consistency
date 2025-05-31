from pathlib import Path

import pandas as pd
from loguru import logger

from src import config
from src.feature_engineering.categories import get_category_column
from src.feature_engineering.legislature_period import get_legislature_period_metadata
from src.feature_engineering.mirror_beschlussempfehlung import prepare_final_dataset
from src.prediction.config import PREDICTIONS_OUTPUT_PATH
from src.prediction.predict_partyline import predict_partyline
from src.votes.build import is_own_proposal
from src.votes.config import OUTPUT_PARQUET_PATH


def load_manifestos():
    if not Path("output/cleaned_manifestos.parquet").exists():
        raise FileNotFoundError(
            "Manifestos data not found. Please run the preprocessing step first."
        )
    manifestos = pd.read_parquet("output/cleaned_manifestos.parquet")
    manifestos["valid_starting"] = pd.to_datetime(
        manifestos["valid_starting"], format="%d.%m.%Y", dayfirst=True
    )
    return manifestos


def load_votes():
    if not Path(OUTPUT_PARQUET_PATH).exists():
        raise FileNotFoundError(
            "Votes data not found. Please run the preprocessing step first."
        )
    votes = pd.read_parquet(OUTPUT_PARQUET_PATH)
    votes["date"] = pd.to_datetime(
        votes["date"], format="%Y-%m-%d"
    )
    return votes


def run_prediction(name: str):
    votes = load_votes()
    manifestos = load_manifestos()

    all_predictions = None

    for party in config.PARTIES:
        logger.info(f"Processing party: {party}")
        party_votes = votes.copy()
        party_votes["party"] = party
        party_votes["reasoning"] = predict_partyline(party, votes, manifestos)
        party_votes = party_votes[party_votes["reasoning"].notna()]
        party_votes["prediction"] = party_votes["reasoning"].str["decision"]

        if all_predictions is None:
            all_predictions = party_votes
        else:
            all_predictions = pd.concat(
                [all_predictions, party_votes], ignore_index=True
            )

    all_predictions.to_parquet(PREDICTIONS_OUTPUT_PATH, index=False)
    dataset = prepare_final_dataset()
    dataset["category"] = get_category_column(dataset["summary_embedding"])

    dataset["metadata"] = dataset.apply(
        lambda row: get_legislature_period_metadata(row["party"], row["date"]), axis=1
    )
    dataset[
        [
            "is_governing",
            "bundestag",
        ]
    ] = dataset["metadata"].apply(pd.Series)
    dataset.drop(columns=["metadata"], inplace=True)

    dataset["vote_correct"] = dataset["prediction"] == dataset["ground_truth"]
    dataset["is_own_proposal"] = dataset.apply(is_own_proposal, axis=1)
    dataset["manifesto_context"] = dataset["reasoning"].str["context"]
    dataset["reasoning"] = dataset["reasoning"].str["reasoning"]

    dataset.to_parquet(f"output/predictions_{name}.parquet", index=False)
