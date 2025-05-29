

# enum for annehmen, ablehnen, enthaltung

from enum import Enum

class VoteResultEnum(Enum):
    ANNAHME = "Annahme"
    ABLEHNUNG = "Ablehnung"
    ENTHALTUNG = "Enthaltung"