import re

REPLACEMENTS: list[tuple[str, str] | tuple[str, str, str]] = [
    (r"^\s*(?:-{3,}|\*{3,}|_{3,})\s*$", "", re.MULTILINE),  # horizontal rules
    (r"\*\*(.*?)\*\*", r"\1"),  # **bold**
    (r"\*(.*?)\*", r"\1"),  # *italic*
    (r"__(.*?)__", r"\1"),  # __bold__
    (r"_(.*?)_", r"\1"),  # _italic_
    (r"~~(.*?)~~", r"\1"),  # ~~strikethrough~~
    (r"`([^`]*)`", r"\1"),  # `inline code`
    (r"^#+\s*", "", re.MULTILINE),  # headings
]


def process_note_content(content: str) -> str:
    code_blocks: list[str] = []

    def save_code(match):
        code_blocks.append(match.group(0))
        return f"__CODE_BLOCK_{len(code_blocks) - 1}__"

    content = re.sub(
        r"```[\s\S]*?```",
        save_code,
        content,
        flags=re.MULTILINE,
    )

    # 2. Replace Obsidian links
    # [[js]] -> js
    # [[js|javascript]] -> javascript
    content = re.sub(
        r"\[\[([^|\]]+)(?:\|([^\]]+))?\]\]", lambda m: m.group(2) or m.group(1), content
    )

    for item in REPLACEMENTS:
        if len(item) == 2:
            content = re.sub(*item, content)
        else:
            pattern, repl, flags = item
            content = re.sub(pattern, repl, content, flags=flags)

    for i, block in enumerate(code_blocks):
        content = content.replace(f"__CODE_BLOCK_{i}__", block)

    return content
