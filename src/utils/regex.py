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
    "Gesetzesentwurf",
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
    "Entwurf eines",
]

_PATTERN = re.compile(
    rf"^(?:{'|'.join(map(re.escape, COUNTS))}\s)?"
    rf"(?:{'|'.join(map(re.escape, TYPES))})"
)


def is_title_start(first_page_text: str) -> bool:
    return _PATTERN.match(first_page_text)

def regex_drucksachen_type(title: str) -> str:
    pattern = re.compile(
        rf"^\s*(?:{'|'.join(map(re.escape, COUNTS))})?\s*"
        rf"({'|'.join(map(re.escape, TYPES))})",
        flags=re.IGNORECASE
    )
    m = pattern.match(title.strip())
    type_ = m.group(1) if m else None
    if not type_:
        raise ValueError(f"Type not found in {title}")
    
    if type_.startswith("Beschlussempfehlung"):
        return "Beschlussempfehlung"
    if (
        type_.startswith("Gesetzentwurf")
        or type_.startswith("Gesetzesentwurf")
        or type_.startswith("Entwurf eines")
    ):
        return "Gesetzentwurf"
    return type_.split()[0]

def regex_drucksachen_ids(vote_name: str) -> list[str]:
    """
    Extracts relevant IDs from the vote name using regex.

    Args:
        vote_name (str): The name of the vote.

    Returns:
        list[str]: A list of extracted IDs.
    """
    pattern = re.compile(r"\b\d{2}/\d+\b")

    matches = pattern.findall(vote_name)
    return list(set(matches))
