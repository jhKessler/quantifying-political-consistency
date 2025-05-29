from dotenv import load_dotenv
from openai import OpenAI
import os
from loguru import logger
load_dotenv()

client = OpenAI(
    api_key=os.environ["DEEPSEEK_API_KEY"],
    base_url=os.environ["DEEPSEEK_BASE_URL"],
)


def prompt_deepseek(system_prompt: str, text: str, model: str = "deepseek-chat") -> str:
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
        model=model,
    )
    return response.choices[0].message.content
