THREADS = 8
DEEPSEEK_MODEL = "deepseek-chat"

SIMILARITY_K = 5

PREDICTION_PROMPT = """
Entscheide anhand der folgenden Informationen aus dem Wahlprogramm einer imaginären Partei, ob die Partei sich bei dem gegebenen Antrag enthalten hat, oder für bzw. gegen den Antrag im Bundestag gestimmt hat.

Berücksichtige dabei:
- Eine Zustimmung ("stimmt zu") erfolgt nur, wenn der Antrag klar mit den Werten oder Forderungen der Partei übereinstimmt.
- Eine Ablehnung ("stimmt nicht zu") erfolgt nur, wenn der Antrag klar gegen die Positionen der Partei steht.
- Wenn die Position der Partei unklar, widersprüchlich oder nicht einschätzbar ist, dann wähle "enthält sich".

Der Output muss immer DIREKT mit entweder "enthält sich", "stimmt zu" oder "stimmt nicht zu" ANFANGEN. Schreibe keine Einleitung, fange direkt mit der Entscheidung an. Gib anschließend eine kurze Begründung.

"""

PREDICTIONS_OUTPUT_PATH = "data/predictions.parquet"
