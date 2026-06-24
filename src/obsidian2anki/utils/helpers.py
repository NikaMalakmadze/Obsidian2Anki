import re


def process_note_content(content: str) -> str:
    return re.sub(r"\[\[([^|\]]+)\|([^\]]+)\]\]", r"\2", content)
