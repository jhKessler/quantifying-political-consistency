from typing import List

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

from src.utils.llm import prompts
from src.votes import config

load_dotenv()
client = OpenAI()


def prompt_openai(system_prompt: str, text: str, model: str = "gpt-4.1-mini") -> str:
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        model=model,
    )
    return response.choices[0].message.content


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
                "content": prompts.MATCH_ENTRYPOINT,
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


def get_embedding(text: str, model=config.EMBEDDING_MODEL) -> list[float]:
    response = client.embeddings.create(input=text, model=model)
    return response.data[0].embedding



class VoteProposers(BaseModel):
    proposers: List[str]


def get_proposer(
    vote_title: str
) -> VoteProposers:
    response = client.responses.parse(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": prompts.GET_PROPOSER},
            {"role": "user", "content": f"Vote title: {vote_title}"},
        ],
        text_format=VoteProposers,
    )

    event = response.output_parsed.proposers
    return event
