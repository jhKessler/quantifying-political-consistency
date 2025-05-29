


SUMMARIZE_MANIFESTO = """
    Filtere aus dem folgenden Text jegliche Informationen heraus, aus denen ersichtlich ist, von welcher Partei das Wahlprogramm stammt.
    Das Ergebnis soll eine Liste von Punkten sein, welche die wichtigsten Punkte des Wahlprogramms zusammenfassen, ohne Namen einzelner Personen oder Parteien zu nennen.
    Gehe gerne ins Detail für jeden Punkt um keine wichtigen Informationen auszulassen. Lasse keine Punkte aus.
    Der resultierende Text sollte eine klare und präzise Zusammenfassung des Wahlprogramms sein, die sich auf die politischen Positionen und Vorschläge konzentriert.
    Fange direkt mit dem Text an, ohne Einleitung oder Erklärung.
"""

MATCH_ENTRYPOINT = """
    Gegeben ist ein Titel eines Gesetzesvorschlags und eine Liste von verfügbaren Drucksachen.
    Deine Aufgabe ist es, die Drucksache zu finden, über die wirklich abgestimmt wird. Das ist meist die erstgenannte Drucksache.
    Geb dann den Index der Drucksache in der Liste zurück, die am besten zum Titel passt. 
    Die Drucksache sollte den gleichen Typ (Gestz, Antrag, Bericht, Beschlussempfelung etc.).
"""

SUMMARIZE_DRUCKSACHE = """
    Fasse den folgenden Text über den im Bundestag abgestimmt wird zusammen.
    Das Ergebnis sollte eine kurze Zusammenfassung sein, die genau beschreibt, für was abgestimmt wird.
    Versuche dich kurz zu halten, aber nenne die Wichtigsten Aspekte.
    Falls im Text enthalten ist, von wem der Antrag kommt, nenne AUF KEINEN FALL den Namen oder die Fraktion, lass unbedingt aus von wem der Antrag ist.
    Fange direkt mit der Zusammenfassung an, ohne Einleitung oder Erklärung.
"""