import os

from dotenv import load_dotenv
import anthropic

load_dotenv()

client = anthropic.Anthropic()


def prompt_claude(system_prompt: str, text: str, model: str = "claude-opus-4-1") -> str:
    response = client.messages.create(
        model=model,
        system=system_prompt,
        messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": text
                }
            ]
        }
            ],
        max_tokens=1000
    )
    return response.content[0].text
