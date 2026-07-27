import os
import re

from dotenv import load_dotenv
from groq import Groq


load_dotenv()


class HinglishConverter:
    def __init__(self) -> None:
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise ValueError(
                "GROQ_API_KEY is missing from the .env file."
            )

        self.client = Groq(api_key=api_key)

    def convert(self, text: str) -> str:
        response = self.client.chat.completions.create(
            model="openai/gpt-oss-20b",
            temperature=0,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Convert this speech transcript into natural "
                        "Hinglish written only in Roman English letters. "
                        "Correct obvious speech-recognition mistakes using "
                        "the sentence context. Preserve common English words. "
                        "Do not add explanations. Do not add new information. "
                        "Return only one corrected caption line."
                    ),
                },
                {
                    "role": "user",
                    "content": text,
                },
            ],
        )

        result = (
            response.choices[0].message.content or ""
        ).strip()

        # Remove accidental labels or quotation marks.
        result = re.sub(
            r"^(caption|hinglish|output)\s*:\s*",
            "",
            result,
            flags=re.IGNORECASE,
        )

        return result.strip("\"' ")