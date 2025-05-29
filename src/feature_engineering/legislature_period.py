from datetime import datetime
from loguru import logger
import pandas as pd

manifesto_metadata = pd.read_csv(r"input\manifestos.csv")
manifesto_metadata["term_start"] = pd.to_datetime(manifesto_metadata["term_start"], format="%d.%m.%Y")

def get_legislature_period_metadata(party: str, date: datetime) -> dict:
    party_rows = manifesto_metadata[
        (manifesto_metadata["party"] == party)
        & (manifesto_metadata["term_start"] <= date)
    ].sort_values("term_start", ascending=True)
    if party_rows.empty:
        logger.warning(f"No manifesto data found for party '{party}' on date {date}.")
        return None
    return {
        "is_governing": party_rows.iloc[-1]["is_governing"],
        "bundestag": party_rows.iloc[-1]["bundestag"],
    }

