URLS_PARQUET_PATH = "data/votes/urls.parquet"
RESULT_CSV_FOLDER = "data/votes/results"
ENTRYPOINTS_PARQUET_PATH = "data/votes/entrypoints.parquet"
OUTPUT_PARQUET_PATH = "output/votes.parquet"

# deepseek context window is 64000 tokens, one character is about 0.3 tokens
MAX_CONTENT_CHARS = 58000 * 3  #

EMBEDDING_MODEL = "text-embedding-3-small"

RELEVANT_TYPES = ["Gesetzentwurf", "Beschlussempfehlung", "Antrag", "Änderungsantrag"]


PROPOSERS = {
    "Union (CDU/CSU)": "Union",
    "SPD": "SPD",
    "FDP": "FDP",
    "BÜNDNIS 90/DIE GRÜNEN": "DIE_GRÜNEN",
    "DIE LINKE": "DIE_LINKE",
    "AfD": "AfD",
    "Bundesregierung": "Bundesregierung"
}