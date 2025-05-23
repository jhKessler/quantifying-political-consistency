from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

load_dotenv()
client = OpenAI()

def get_embedding(text: str, model="text-embedding-3-small") -> list[float]:
    response = client.embeddings.create(
        input=text,
        model=model
    )
    return response.data[0].embedding


class MatchingTitle(BaseModel):
    index: int

def match_drucksache_to_vote(vote_title: str, available_drucksachen: list[dict]) -> MatchingTitle:
    response = client.responses.parse(
        model="gpt-4.1-mini",
        input=[
            {"role": "system", "content": "Given a vote title and a list of available drucksachen, match the most relevant drucksache to the vote title. "},
            {
                "role": "user",
                "content": f"Vote title: {vote_title}\nAvailable drucksachen: {available_drucksachen}",
            },
        ],
        text_format=MatchingTitle,
    )

    event = response.output_parsed
    return event