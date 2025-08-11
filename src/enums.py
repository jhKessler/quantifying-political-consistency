from enum import Enum


class VoteResultEnum(Enum):
    ANNAHME = "Annahme"
    ABLEHNUNG = "Ablehnung"
    ENTHALTUNG = "Enthaltung"

class APIProviderEnum(Enum):
    OPENAI = "openai"
    DEEPSEEK = "deepseek"