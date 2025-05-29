THREADS = 16
DEEPSEEK_MODEL = "deepseek-chat"

SIMILARITY_K = 5

PREDICTION_PROMPT = """
    Entscheide anhand der folgenden Informationen aus dem Wahlprogramm einer imaginären Partei, ob die Partei sich bei dem gegebenen Antrag enthalten hat, oder für bzw. gegen den Antrag im Bundestag gestimmt hat.
    Der Output muss immer DIREKT mit entweder "enthält sich", "stimmt zu" oder "stimmt nicht zu" ANFANGEN. Schreibe keine Einleitung, fange direkt mit der Entscheidung an. mit einer kurzen Begründung wie du zu der Entscheidung gekommen bist.
"""

PREDICTIONS_OUTPUT_PATH = "data/predictions.parquet"
