EMBEDDING_MODEL = "text-embedding-3-small"
DEEPSEEK_MODEL = "deepseek-chat"
THREADS = 8
SIMILARITY_K = 5

DEEPSEEK_SYSTEM_PROMPT = """
    Entscheide anhand der folgenden Informationen aus dem Wahlprogramm einer imaginären Partei, ob die Partei sich bei dem gegebenen Antrag enthalten hat, oder für bzw. gegen den Antrag im Bundestag gestimmt hat.
    Der Output muss immer mit entweder "enthält sich", "stimmt zu" oder "stimmt nicht zu" anfangen. mit einer kurzen Begründung wie du zu der Entscheidung gekommen bist.
"""

PARTIES = ["AfD", "DIE_GRÜNEN", "DIE_LINKE", "FDP", "SPD", "Union"]
