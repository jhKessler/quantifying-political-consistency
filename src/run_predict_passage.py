from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

import joblib
import pandas as pd
from loguru import logger


def load_csvs_in_dir(
    directory: Path, pattern: str = "*.csv", **read_csv_kwargs
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for p in sorted(directory.glob(pattern)):
        frames.append(pd.read_csv(p, **read_csv_kwargs))
    if not frames:
        raise FileNotFoundError(f"No CSVs found in {directory}")
    return pd.concat(frames, ignore_index=True)


def load_ground_truth(results_dir: Path) -> pd.DataFrame:
    gt = load_csvs_in_dir(results_dir)
    cols = ["vote_id", "Annahme", "Ablehnung", "Enthaltung"]
    missing = [c for c in cols if c not in gt.columns]
    if missing:
        raise KeyError(f"Missing columns in ground truth: {missing}")
    return gt.groupby("vote_id", as_index=True)[
        ["Annahme", "Ablehnung", "Enthaltung"]
    ].sum()


def find_constitution_amendment_vote_ids(votes_df: pd.DataFrame) -> set:
    mask = votes_df["drucksache_title"].str.contains(
        "Änderung des Grundgesetzes", na=False
    )
    return set(votes_df.loc[mask, "vote_id"].unique())


def filter_out_vote_ids(df: pd.DataFrame, excluded_ids: Iterable) -> pd.DataFrame:
    return df.loc[~df["vote_id"].isin(set(excluded_ids))].copy()


def add_predictions(df: pd.DataFrame, model: Any, encoder: Any) -> pd.DataFrame:
    feature_df = df.drop(
        columns=["vote_id", "voting_party", "ground_truth"], errors="ignore"
    )
    raw_pred = model.predict(feature_df)
    try:
        labels = encoder.inverse_transform(raw_pred)
    except Exception:
        try:
            labels = encoder.classes_[raw_pred]
        except Exception:
            labels = raw_pred
    out = df.copy()
    out["xgb_prediction"] = list(labels)
    return out


def seats_row_for_bundestag(seats_df: pd.DataFrame, bundestag_value: Any) -> pd.Series:
    row = seats_df.loc[seats_df["bundestag"] == bundestag_value]
    if row.empty:
        raise KeyError(f"No seat distribution for bundestag={bundestag_value!r}")
    return row.iloc[0]


def aggregate_predicted_seats_for_vote(
    vote_group: pd.DataFrame, seats_df: pd.DataFrame
) -> dict[str, int]:
    seat_row = seats_row_for_bundestag(
        seats_df, vote_group["bundestag"].iloc[0]
    ).to_dict()
    totals = {"Annahme": 0, "Ablehnung": 0, "Enthaltung": 0}
    for _, row in vote_group.iterrows():
        party = row["voting_party"]
        label = row["xgb_prediction"]
        seats = int(seat_row.get(party, 0))
        if label in totals:
            totals[label] += seats
    return totals


def compute_results(
    test_df_with_preds: pd.DataFrame, seats_df: pd.DataFrame, ground_truth: pd.DataFrame
) -> pd.DataFrame:
    records: list[dict] = []
    for vote_id, grp in test_df_with_preds.groupby("vote_id", sort=False):
        predicted_totals = aggregate_predicted_seats_for_vote(grp, seats_df)
        if vote_id not in ground_truth.index:
            continue
        gt_row = ground_truth.loc[vote_id]
        records.append(
            {
                "vote_id": vote_id,
                "passed_prediction": predicted_totals["Annahme"]
                > predicted_totals["Ablehnung"],
                "passed_ground_truth": int(gt_row["Annahme"])
                > int(gt_row["Ablehnung"]),
            }
        )
    return pd.DataFrame.from_records(records)


def build_confusion_matrix(results_df: pd.DataFrame) -> pd.DataFrame:
    return pd.crosstab(
        results_df["passed_ground_truth"], results_df["passed_prediction"]
    )


def main(
    test_data_path: Path = Path("output/xgboost_test_data.parquet"),
    model_path: Path = Path("output/xgboost_model.pkl"),
    encoder_path: Path = Path("output/label_encoder.pkl"),
    seats_path: Path = Path("input/seats_in_parliament.csv"),
    votes_parquet_path: Path = Path("output/votes.parquet"),
    results_dir: Path = Path("data/votes/results"),
) -> None:
    logger.info("Loading inputs") 
    test_df = pd.read_parquet(test_data_path)
    model = joblib.load(model_path)
    encoder = joblib.load(encoder_path)
    seats_df = pd.read_csv(seats_path, sep=";")
    votes_df = pd.read_parquet(votes_parquet_path)
    ground_truth = load_ground_truth(results_dir)

    logger.info("Filtering constitution amendments")
    excluded_ids = find_constitution_amendment_vote_ids(votes_df)
    test_df = filter_out_vote_ids(test_df, excluded_ids)

    logger.info("Predicting labels")
    test_df = add_predictions(test_df, model, encoder)

    logger.info("Computing results")
    results_df = compute_results(test_df, seats_df, ground_truth)

    logger.info("Confusion matrix")
    cm = build_confusion_matrix(results_df)
    print(cm)


main()
