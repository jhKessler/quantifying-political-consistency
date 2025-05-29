import re

import re

COUNTS = [
    "Erste",
    "Zweite",
    "Dritte",
    "Vierte",
    "Fünfte",
    "Sechste",
    "Siebte",
    "Achte",
    "Neunte",
    "Zehnte",
    "Erster",
    "Zweiter",
    "Dritter",
    "Vierter",
    "Fünfter",
    "Sechster",
    "Siebter",
    "Achter",
    "Neunter",
    "Zehnter",
]

TYPES = [
    "Beschlussempfehlung und Bericht",
    "Beschlussempfehlung",
    "Gesetzentwurf",
    "Antrag",
    "Änderungsantrag",
    "Entschließungsantrag",
    "Bericht",
    "Unterrichtung",
    "Ergänzung zu den Beschlussempfehlungen",
    "Kleine Anfrage",
    "Verordnung",
    "Antwort",
    "Große Anfrage",
]

_PATTERN = re.compile(
    rf"^(?:{'|'.join(map(re.escape, COUNTS))}\s)?"
    rf"(?:{'|'.join(map(re.escape, TYPES))})"
)


def is_title_start(first_page_text: str) -> bool:
    return _PATTERN.search(first_page_text)


def regex_drucksachen_ids(vote_name: str) -> list[str]:
    """
    Extracts relevant IDs from the vote name using regex.

    Args:
        vote_name (str): The name of the vote.

    Returns:
        list[str]: A list of extracted IDs.
    """
    pattern = re.compile(r"\d{2}/\d+")
    matches = pattern.findall(vote_name)
    return list(set(matches))
