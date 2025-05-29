from typing import List
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel
from src.prediction import config
load_dotenv()
client = OpenAI()


def get_embedding(text: str, model=config.EMBEDDING_MODEL) -> list[float]:
    response = client.embeddings.create(input=text, model=model)
    return response.data[0].embedding


class MatchingTitle(BaseModel):
    index: int


def match_drucksache_to_vote(
    vote_title: str, available_drucksachen: list[dict]
) -> MatchingTitle:
    response = client.responses.parse(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": "Given a vote title and a list of available drucksachen, match the most relevant drucksache to the vote title. ",
            },
            {
                "role": "user",
                "content": f"Vote title: {vote_title}\nAvailable drucksachen: {available_drucksachen}",
            },
        ],
        text_format=MatchingTitle,
    )

    event = response.output_parsed
    return event

class CategoryEntry(BaseModel):
    category: str
    percentage: int

class LobbyregisterEntryDistribution(BaseModel):
    categories: List[CategoryEntry]


def classify_lobbyregister_entry(
        entry: dict
) -> LobbyregisterEntryDistribution:
    response = client.responses.parse(
        model="gpt-4.1-mini",
        input=[
            {
                "role": "system",
                "content": rf"""
                    Gegeben ist der folgende Eintrag im Lobbyregister.
                    Geb für jede Kategorie eine Prozentzahl, wie viel des Geldes du schätzt für jede Kategorie ausgegeben wird.
                    Die Summe aller Werte muss immer 100 sein.
                    Output als JSON-Objekt mit den Kategorien und den jeweiligen Prozentwerten.
                    Kategorien: {config.CATEGORIES}
                """,
            },
            {
                "role": "user",
                "content": f"Lobbyregister Eintrag: {entry}",
            },
        ],
        text_format=LobbyregisterEntryDistribution,
    )

    event = response.output_parsed
    return event


def prompt_openai(system_prompt: str, text: str, model: str = "gpt-4.1-mini") -> str:
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        model=model,
    )
    return response.choices[0].message.content
