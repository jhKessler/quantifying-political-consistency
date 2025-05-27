import numpy as np
from src.utils.openai_utils import get_embedding
import os

import pandas as pd
from src.prediction import config
from loguru import logger

data = pd.read_parquet(r"data\parquet\predicted_votes_deepseek-reasoner.parquet")


def vote_counts_to_result(votes: pd.Series) -> str:
    """Convert vote counts to a result string."""
    max_votes = votes[["yes", "no", "abstain"]].idxmax()
    if max_votes == "yes":
        return "zustimmung"
    elif max_votes == "no":
        return "ablehnung"
    elif max_votes == "abstain":
        return "enthaltung"
    else:
        logger.warning(f"Unexpected vote counts: {votes}")
        return None


# TODO flip around for beschlussempfelungen that vote against the recommendation
def mirror_decision(decision: str) -> str:
    """Mirror the decision for beschlussempfehlungen."""
    if decision == "zustimmung":
        return "ablehnung"
    elif decision == "ablehnung":
        return "zustimmung"
    else:
        return decision


for party in config.PARTIES:
    real_votes = (
        pd.read_csv(f"data/csv/vote_counts/{party}.csv")
        .rename(columns={"vote_id": "vote"})
        .drop_duplicates(subset="vote")
    )
    real_votes[f"{party}_ground_truth"] = real_votes.apply(
        vote_counts_to_result, axis=1
    )
    data = data.merge(
        real_votes[["vote", f"{party}_ground_truth"]], on="vote", how="left"
    )
    data[f"{party}_prediction"] = data[f"{party}_decision"].str["decision"]
    # Flip the decision for beschlussempfehlungen if they are against the underlying decision
    # This is necessary because the beschlussempfehlung is a recommendation to vote against, thus changing the context
    beschlussempfehlungen_filt = data["beschlussempfehlung"] == "ablehnen"
    data.loc[beschlussempfehlungen_filt, f"{party}_prediction"] = data.loc[
        beschlussempfehlungen_filt, f"{party}_prediction"
    ].apply(mirror_decision)

if os.path.exists("data/parquet/kategorien.parquet"):
    categories = pd.read_parquet("data/parquet/kategorien.parquet")
else:
    categories = pd.DataFrame(
        {
            "kategorie": [
                "Finanzen - Steuern, Staatsbudget, Haushalts- und Finanzpolitik",
                "Inneres & Migration - Innere Sicherheit, öffentliche Verwaltung, Migration, Staatsbürgerschaft",
                "Außenpolitik & Europäische Angelegenheiten - Diplomatie, internationale Beziehungen, EU-Politik",
                "Verteidigung & Sicherheit - Militär, Verteidigungsstrategie, Bundeswehr, Rüstung",
                "Wirtschaft & Energie - Industriepolitik, Mittelstand, Energieversorgung, Wirtschaftsordnungen",
                "Forschung & Technologie - Innovationsförderung, Raumfahrt, Forschungseinrichtungen, Technologietransfer",
                "Justiz & Verbraucherschutz - Rechtsprechung, Gesetzgebung, Verbraucherschutz, Datenschutz",
                "Bildung, Familie & Jugend - Schulen, Hochschulen, Familienförderung, Kinder- und Jugendpolitik",
                "Arbeit & Soziales - Arbeitsmarktpolitik, Sozialversicherung, Renten, Integration",
                "Digitalisierung & Modernisierung - E-Government, IT-Infrastruktur, digitale Verwaltung, Cybersecurity",
                "Verkehr & Infrastruktur - Straßen-, Schienen- und Luftverkehr, Mobilitätskonzepte, Infrastrukturprojekte",
                "Umwelt, Klima & Naturschutz - Umweltschutz, Klimapläne, Artenschutz, nukleare Sicherheit",
                "Gesundheit - Gesundheitssystem, Krankenversicherung, Arzneimittelregulierung, Pandemie- und Präventionspolitik",
                "Landwirtschaft & Ernährung - Agrarpolitik, Ernährungssicherheit, Ländliche Entwicklung",
                "Entwicklungszusammenarbeit - Entwicklungsprojekte, humanitäre Hilfe, internationale Zusammenarbeit",
                "Wohnen & Stadtentwicklung - Wohnungsbau, Städtebau, Bauordnung, Städtebauförderung",
            ]
        }
    )
    categories["embedding"] = categories["kategorie"].apply(get_embedding)
    categories.to_parquet("data/parquet/kategorien.parquet", index=False)


def get_closest_category(summary_embedding: np.array) -> str:
    distances = categories["embedding"].apply(
        lambda x: np.linalg.norm(np.array(x) - summary_embedding)
    )
    closest_index = distances.idxmin()
    return categories.iloc[closest_index]["kategorie"]


data["category"] = data["embedding"].apply(get_closest_category)

data.to_parquet("data/parquet/final.parquet", index=False)
