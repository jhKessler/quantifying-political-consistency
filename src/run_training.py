from operator import le
import joblib
from sklearn.preprocessing import LabelEncoder
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score


def run_data_prepreprocessing(
    predictions: pd.DataFrame
) -> pd.DataFrame:
    subset = predictions.merge(
        predictions.groupby(["vote_id", "party"])
        .size()
        .reset_index(name="count")
        .drop_duplicates("vote_id")
        .drop(columns="party"),
        on="vote_id",
        how="left",
    ).rename(columns={"count": "beschlussempfehlung_drucksachen"})
    subset = subset[
        [
            "vote_id",
            "type",
            "beschlussempfehlung",
            "proposers",
            "party",
            "prediction",
            "category",
            "is_governing",
            "bundestag",
            "is_own_proposal",
            "beschlussempfehlung_drucksachen",
            "ground_truth",
        ]
    ]

    proposers = pd.DataFrame(
        subset["proposers"].apply(lambda li: {p: True for p in li}).tolist()
    ).fillna(False)
    proposers.columns = [f"proposer_{p}" for p in proposers.columns]
    data = pd.concat([subset, proposers], axis=1)
    data["voting_party"] = data["party"]
    data.drop(columns=["proposers"], inplace=True)
    data = pd.get_dummies(
        data,
        columns=["type", "prediction", "beschlussempfehlung", "party", "category"],
    )
    return data


def train_model(train: pd.DataFrame):
    train.drop(columns=["vote_id", "voting_party"], inplace=True)
    y = train.pop("ground_truth")
    X_train, X_test, y_train, y_test = train_test_split(
        train, y, test_size=0.2, random_state=42, stratify=y
    )

    encoder = LabelEncoder()
    y_train_enc = encoder.fit_transform(y_train)

    model = XGBClassifier(
        objective="multi:softprob",
        num_class=3,
        use_label_encoder=False,
        eval_metric="mlogloss",
    )

    model.fit(X_train, y_train_enc)

    y_pred_enc = model.predict(X_test)
    y_pred = encoder.inverse_transform(y_pred_enc)

    accuracy = accuracy_score(y_test, y_pred)
    print("Accuracy:", accuracy)

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, y_pred))

    joblib.dump(model, "output/xgboost_model.pkl")
    joblib.dump(encoder, "output/label_encoder.pkl")


def run_training():
    data = pd.read_parquet("output/votes.parquet")
    predictions = pd.read_parquet("output/predictions_deepseek_reasoner.parquet")

    test_ids = data["vote_id"].sample(frac=0.2, random_state=42).unique()

    processed = run_data_prepreprocessing(predictions)
    train_data = processed[~processed["vote_id"].isin(test_ids)]
    test_data = processed[processed["vote_id"].isin(test_ids)]
    train_model(train_data)
    test_data.to_parquet("output/xgboost_test_data.parquet", index=False)


if __name__ == "__main__":
    run_training()