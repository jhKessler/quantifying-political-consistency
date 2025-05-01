import os
import pandas as pd
from tqdm import tqdm
from src.utils.download import download_file

# to clean up the party names
group_mapping = {
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


def calculate_votes_per_party(vote: pd.Series) -> pd.Series:
    os.makedirs("data/tmp/vote_xls", exist_ok=True)
    os.makedirs("data/csv/vote_counts", exist_ok=True)
    file_extension = os.path.splitext(vote["xls_url"])[-1]
    xls_path = f"data/tmp/vote_xls/{vote['id']}.{file_extension}"
    download_file(vote["xls_url"], xls_path)
    votes = pd.read_excel(xls_path)
    votes["Fraktion/Gruppe"] = votes["Fraktion/Gruppe"].map(group_mapping)
    by_party = (
        votes.groupby("Fraktion/Gruppe")[["ja", "nein", "Enthaltung"]]
        .sum(numeric_only=True)
        .loc[:, ["ja", "nein", "Enthaltung"]]
    )

    for party in by_party.index:
        # add the results to a csv for each party
        party_path = f"data/csv/vote_counts/{party}.csv"
        if not os.path.exists(party_path):
            pd.DataFrame(columns=["vote_id", "yes", "no", "abstain"]).to_csv(
                party_path, index=False
            )

        new_row = pd.Series(
            {
                "vote_id": vote["id"],
                "yes": by_party.loc[party, "ja"],
                "no": by_party.loc[party, "nein"],
                "abstain": by_party.loc[party, "Enthaltung"],
            }
        )
        new_row.to_frame().T.to_csv(party_path, mode="a", header=False, index=False)


def gather_vote_results():
    """Orchestrates the process of gathering vote results from the Bundestag website.

    - Downloads the vote result XLS files
    - Calculates the votes per party and saves them to CSV files
    """
    df = pd.read_parquet("data/parquet/votes.parquet")

    pbar = tqdm(total=len(df), desc="Calculating votes per party", unit="vote")
    for _, vote in df.iterrows():
        pbar.update(1)
        calculate_votes_per_party(vote)