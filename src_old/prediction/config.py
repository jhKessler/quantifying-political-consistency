EMBEDDING_MODEL = "text-embedding-3-small"
DEEPSEEK_MODEL = "deepseek-reasoner"
THREADS = 16
SIMILARITY_K = 5

DEEPSEEK_SYSTEM_PROMPT = """
    Entscheide anhand der folgenden Informationen aus dem Wahlprogramm einer imaginären Partei, ob die Partei sich bei dem gegebenen Antrag enthalten hat, oder für bzw. gegen den Antrag im Bundestag gestimmt hat.
    Der Output muss immer mit entweder "enthält sich", "stimmt zu" oder "stimmt nicht zu" anfangen. mit einer kurzen Begründung wie du zu der Entscheidung gekommen bist.
"""

PARTIES = ["AfD", "DIE_GRÜNEN", "DIE_LINKE", "FDP", "SPD", "Union"]


CATEGORIES = [
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
