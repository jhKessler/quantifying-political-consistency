from pathlib import Path
from typing import TypedDict

import pandas as pd
from loguru import logger

from src.enums import VoteResultEnum
from src.utils.download import download_file
from src.votes import config


class VoteResult(TypedDict):
    annahme: int
    ablehnung: int
    enthaltung: int


party_mapping = {
    "CDU/CSU": "Union",
    "SPD": "SPD",
    "BÜ90/GR": "DIE_GRÜNEN",
    "BÜNDNIS`90/DIE GRÜNEN": "DIE_GRÜNEN",
    "FDP": "FDP",
    "AfD": "AfD",
    "DIE LINKE.": "DIE_LINKE",
    "DIE LINKE": "DIE_LINKE",
    "Die Linke": "DIE_LINKE",
    "Fraktionslos": "Fraktionslos",
    "fraktionslose": "Fraktionslos",
    "fraktionslos": "Fraktionslos",
    "BSW": "BSW",
}


def append_vote_results(xls_path: str, vote_id: str) -> None:
    votes = pd.read_excel(xls_path)
    votes["Fraktion/Gruppe"] = votes["Fraktion/Gruppe"].map(party_mapping)
    by_party = (
        votes.groupby("Fraktion/Gruppe")[["ja", "nein", "Enthaltung"]]
        .sum(numeric_only=True)
        .loc[:, ["ja", "nein", "Enthaltung"]]
    ).rename(
        columns={
            "ja": VoteResultEnum.ANNAHME.value,
            "nein": VoteResultEnum.ABLEHNUNG.value,
            "Enthaltung": VoteResultEnum.ENTHALTUNG.value,
        }
    )

    for party in by_party.index:
        # add the results to a csv for each party
        party_path = f"data/votes/results/{party}.csv"
        if not Path(party_path).exists():
            # create empty csv with headers if it doesn't exist
            pd.DataFrame(
                columns=[
                    "vote_id",
                    VoteResultEnum.ANNAHME.value,
                    VoteResultEnum.ABLEHNUNG.value,
                    VoteResultEnum.ENTHALTUNG.value,
                ]
            ).to_csv(party_path, index=False)
        else:
            # check if the vote_id already exists in the csv
            existing_votes = pd.read_csv(party_path)
            if vote_id in existing_votes["vote_id"].values:
                continue
        new_row = pd.Series(
            {
                "vote_id": vote_id,
                VoteResultEnum.ANNAHME.value: by_party.loc[party, VoteResultEnum.ANNAHME.value],
                VoteResultEnum.ABLEHNUNG.value: by_party.loc[party, VoteResultEnum.ABLEHNUNG.value],
                VoteResultEnum.ENTHALTUNG.value: by_party.loc[party, VoteResultEnum.ENTHALTUNG.value],
            }
        )
        new_row.to_frame().T.to_csv(party_path, mode="a", header=False, index=False)


def calculate_vote_result(
    vote_id: str, xls_url: str
) -> VoteResult:
    Path(config.RESULT_CSV_FOLDER).mkdir(parents=True, exist_ok=True)
    Path(f"data/votes/all/{vote_id}").mkdir(parents=True, exist_ok=True)

    file_extension = xls_url.split(".")[-1]
    local_path = f"data/votes/all/{vote_id}/result.{file_extension}"
    download_file(xls_url, local_path)
    append_vote_results(local_path, vote_id)
