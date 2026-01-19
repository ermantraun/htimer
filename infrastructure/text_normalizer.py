import re
import emoji
from ftfy import fix_text

TEXT_ONLY_RE = re.compile(r"[^a-zA-Zа-яА-ЯёЁ\s]")

class TextNormalizer:
    
    def normalize(self, text: str) -> str:

        text = fix_text(text)

        text = emoji.replace_emoji(text, replace="")

        text = TEXT_ONLY_RE.sub(" ", text)

        text = re.sub(r"\s+", " ", text).strip()

        return text