# Configuration

Obsidian2Anki uses `pydantic-settings` to load environment variables from the process environment and from a repository-root `.env` file.

## Contents

- [Configuration Source](#configuration-source)
- [Complete Example](#complete-example)
- [Settings Reference](#settings-reference)
- [Path Resolution](#path-resolution)
- [Tag Filtering](#tag-filtering)
- [Anki Requirements](#anki-requirements)
- [Prompt and Model Configuration](#prompt-and-model-configuration)
- [State Configuration](#state-configuration)
- [Validation and Caching](#validation-and-caching)
- [Doctor Behavior](#doctor-behavior)
- [Security](#security)
- [Troubleshooting](#troubleshooting)

## Configuration Source

`config.py` defines:

```python
BASE_DIR = Path(__file__).resolve().parent.parent.parent
```

For a source checkout, this resolves to the repository root.

`Settings` uses:

```python
SettingsConfigDict(
    env_file=BASE_DIR / ".env",
    env_file_encoding="utf-8",
)
```

Normal environment variables can override values read from `.env` according to Pydantic Settings behavior.

`get_settings()` is decorated with `@lru_cache`, so one process normally uses one settings instance after its first successful load.

## Complete Example

```env
API_KEY=your_gemini_api_key
PROMPT_FILE=input/prompt.md

ANKI_URL=http://localhost:8765/
DECK_NAME=Programming

LOCAL_VAULT=/absolute/path/to/your/obsidian/vault
INBOX_FOLDER=00_Inbox
MAIN_NOTES_FOLDER=01_Notes

STATE_FOLDER=data

INCLUDE_TAGS=[]
EXCLUDE_TAGS=[]

MAX_RETRIES_ON_ANKI_DUPLICATE_CARD=3
```

Quoting scalar strings is optional in common `.env` files. JSON syntax is recommended for set/list-like values.

## Settings Reference

| Variable | Type | Code default | Required without external value | Used by |
| --- | --- | --- | :---: | --- |
| `STATE_FOLDER` | `str` | none | Yes | State storage and doctor folder check |
| `API_KEY` | `str` | none | Yes | Gemini generation and validation |
| `PROMPT_FILE` | `str` | none | Yes | Prompt loading and doctor file check |
| `INCLUDE_TAGS` | `set[str]` | empty set | No | Note eligibility |
| `EXCLUDE_TAGS` | `set[str]` | empty set | No | Note eligibility |
| `ANKI_URL` | `str` | `http://localhost:8765` | No | AnkiConnect HTTP endpoint |
| `DECK_NAME` | `str` | none | Yes | Insertion, lookup, stats, diagnostics |
| `LOCAL_VAULT` | `str` | none | Yes | Vault root |
| `INBOX_FOLDER` | `str` | none | Yes | New-note source |
| `MAIN_NOTES_FOLDER` | `str` | none | Yes | Processed/migration destination |
| `MAX_RETRIES_ON_ANKI_DUPLICATE_CARD` | `int` | none | Yes | Additional insertion attempts |

### `API_KEY`

Used to construct:

```python
genai.Client(api_key=settings.API_KEY)
```

The same value is passed to `AI.validate_key()` during doctor runtime checks.

> [!WARNING]
> `EnvironmentChecker` redacts key-like validation values, but `AI.validate_key()` currently logs the supplied key when it catches `APIError`. Protect the log directory and avoid sharing complete logs.

### `PROMPT_FILE`

Read by:

```python
BASE_DIR / settings.PROMPT_FILE
```

The file is loaded during `AI` construction, not lazily during the first generation call.

A missing or unreadable prompt can therefore prevent:

- every normal command from finishing application construction;
- doctor from reaching its runtime table after environment validation succeeds.

### `ANKI_URL`

Default:

```text
http://localhost:8765
```

The example includes a trailing slash. Requests accepts either form for the local endpoint.

The URL is used directly by `requests.post()`.

### `DECK_NAME`

Used for:

- default insertion deck;
- deck existence diagnostics;
- `findNotes query="deck:<name>"` statistics;
- automatic deck creation during insertion when absent.

The diagnostic command expects the deck to already exist and reports failure otherwise. The insertion path can attempt to create it.

### `LOCAL_VAULT`

Use an absolute path when possible.

Linux/macOS:

```env
LOCAL_VAULT=/home/user/Documents/MyVault
```

Windows:

```env
LOCAL_VAULT=C:/Users/User/Documents/MyVault
```

Forward slashes reduce escaping problems in `.env` files on Windows.

### `INBOX_FOLDER`

Resolved as:

```python
Path(LOCAL_VAULT) / INBOX_FOLDER
```

`process` recursively reads `.md` files below this folder.

### `MAIN_NOTES_FOLDER`

Resolved relative to the vault.

Used by:

- destination movement after inbox processing;
- recursive migration discovery;
- immediate-only formatting and statistics scans.

The folder must already exist. `VaultManager._move_to()` does not create it.

### `STATE_FOLDER`

Normal application construction resolves:

```python
BASE_DIR / STATE_FOLDER
```

and creates the directory recursively.

Doctor resolves the same path but only checks it; doctor does not create it because it does not construct `StateManager`.

### `INCLUDE_TAGS`

Recommended syntax:

```env
INCLUDE_TAGS=["Python", "JavaScript"]
```

An empty set accepts any note that is not excluded.

### `EXCLUDE_TAGS`

Recommended syntax:

```env
EXCLUDE_TAGS=["Draft", "Archive"]
```

Any exact matching excluded tag blocks processing.

### `MAX_RETRIES_ON_ANKI_DUPLICATE_CARD`

Controls the loop after the first unsuccessful `add_cards()` result.

With:

```env
MAX_RETRIES_ON_ANKI_DUPLICATE_CARD=3
```

the code can attempt insertion up to four times total:

1. initial generation/insertion;
2. retry 1;
3. retry 2;
4. retry 3.

Each retry regenerates cards with Gemini. The setting name mentions duplicate cards, but any falsy insertion result enters the same retry path.

No validation currently prevents zero or negative values. With `0`, only the initial attempt runs.

## Path Resolution

| Resource | Resolution |
| --- | --- |
| `.env` | `BASE_DIR / ".env"` |
| Prompt | `BASE_DIR / PROMPT_FILE` |
| State folder | `BASE_DIR / STATE_FOLDER` |
| State file | `<resolved state folder>/state.json` |
| Logs | `BASE_DIR / "logs" / "obsidian2anki.log"` |
| Inbox | `Path(LOCAL_VAULT) / INBOX_FOLDER` |
| Main folder | `Path(LOCAL_VAULT) / MAIN_NOTES_FOLDER` |

With `pathlib`, joining an absolute right-hand path discards the left-hand base. Absolute prompt or state paths therefore work even though the code uses `/` joining.

### Nested folders

These values may contain separators:

```env
INBOX_FOLDER=Learning/Inbox
MAIN_NOTES_FOLDER=Learning/Notes
```

Process and migration recurse below the resolved roots.

After successful inbox processing, the file is moved to the top level of the configured main folder, not to an equivalent nested path.

## Tag Filtering

The implemented logic is:

```python
has_no_excluded_tags = not any(
    tag in note.tags for tag in EXCLUDE_TAGS
)

has_required_include_tag = not INCLUDE_TAGS or any(
    tag in note.tags for tag in INCLUDE_TAGS
)

return has_no_excluded_tags and has_required_include_tag
```

### Truth table

| Include set | Exclude set | Result |
| --- | --- | --- |
| Empty | Empty | Every note passes. |
| Empty | Non-empty | Notes pass when they contain no excluded tag. |
| Non-empty | Empty | Notes pass when they contain at least one included tag. |
| Non-empty | Non-empty | Notes need an included tag and no excluded tag. |

### Matching rules

- exact string equality;
- case-sensitive;
- no leading `#` normalization during normal note parsing;
- no hierarchical tag expansion;
- no wildcard or regular-expression support.

Use the same spelling and capitalization as YAML frontmatter.

### YAML tag shape

Only a parsed list is accepted by `_process_file()`:

```yaml
tags:
  - Python
  - Algorithms
```

These forms are not treated as tag lists by the current code:

```yaml
tags: Python
```

```yaml
tags: "Python, Algorithms"
```

They become an empty `VaultNote.tags` list.

## Anki Requirements

### Endpoint

Anki Desktop must expose AnkiConnect at `ANKI_URL`.

`anki_running()` uses a one-second timeout. Other actions through `connect()` have no explicit timeout.

### Deck

`DECK_NAME` may be a nested Anki deck name such as:

```env
DECK_NAME=Programming::Python
```

The value is inserted directly into AnkiConnect queries and payloads.

### Note type and fields

The current code always sends:

```text
modelName = Basic
fields = Front, Back, NoteID
```

Add `NoteID` to the `Basic` note type before processing.

The model name and field mapping are not configurable.

## Prompt and Model Configuration

### Bundled prompt

Default example:

```env
PROMPT_FILE=input/prompt.md
```

The prompt asks for important concepts, concise answers, unique ideas, and one to five cards.

The current prompt also contains the contradictory line:

```text
Preserve the language of the note. Write On English!!!
```

Resolve that instruction according to the intended product behavior.

### Request payload

The model receives:

- prompt text;
- note title;
- note tags;
- normalized note content.

It does not receive frontmatter ID, local file path, or existing generated IDs.

### Hard-coded values

Not currently configurable:

- Gemini model: `gemini-3.1-flash-lite`;
- generation temperature or safety settings;
- card-count constraints in the schema;
- retryable Gemini exception categories;
- Gemini retry limit;
- Anki model name;
- Anki field mapping.

## State Configuration

### Automatic initialization

Normal app construction runs:

```python
state_folder.mkdir(parents=True, exist_ok=True)
state_file.touch(exist_ok=True)
```

An empty state file is loaded as an empty dictionary.

### Stored shape

```json
{
  "9fb66ee5-6778-4bf4-817d-f82646d1237e": {
    "title": "Iterators",
    "path": "/absolute/path/01_Notes/Iterators.md",
    "content_hash": "...",
    "card_count": 2,
    "anki_note_ids": [1749920000001, 1749920000002],
    "processed_at": "2026-08-02T10:00:00+00:00",
    "updated_at": "2026-08-02T10:00:00+00:00"
  }
}
```

### Current persistence behavior

- full JSON file rewrite;
- four-space indentation;
- Unicode preserved;
- no file lock;
- no temporary-file atomic replace;
- no automatic backup;
- no schema version;
- invalid JSON raises during construction.

### Doctor distinction

Doctor checks the configured state folder path without creating or loading state.

This makes it useful for reporting a missing state folder, but a brand-new installation may show a failed state row until a normal command constructs `StateManager` or the directory is created manually.

## Validation and Caching

### Required settings

Fields with no default must be provided by `.env` or the process environment. Missing fields produce Pydantic errors.

### Extra settings

The settings model does not explicitly override Pydantic's extra-field policy in code. Diagnostics can normalize `extra_forbidden` errors when they occur.

### Cache

After `get_settings()` succeeds, later calls in the same process return the cached object. Editing `.env` during a running process has no effect.

Tests that modify environment variables should call:

```python
get_settings.cache_clear()
```

before loading again.

### Eager consumers

Normal `Dependencies` constructs objects that call `get_settings()` internally. This duplicates settings access across classes but returns the same cached model.

## Doctor Behavior

Environment validation runs before normal application construction.

### Missing or invalid settings

Doctor prints a normalized environment table and returns. Sensitive-looking fields are redacted.

### Valid settings

Doctor then constructs `AnkiManager` and `AI`, followed by runtime checks.

### What doctor can validate

- Python version;
- `.env` file presence;
- vault and configured folders;
- state folder;
- prompt file;
- Gemini API access;
- Anki connectivity;
- deck presence.

### What doctor does not validate

- note frontmatter quality;
- unique note IDs;
- Anki field schema;
- state JSON validity;
- state/vault/Anki consistency;
- prompt quality;
- successful generation with the hard-coded model;
- logs directory writability;
- retry-count range.

See [Diagnostics](diagnostics.md).

## Security

- Keep `.env` out of version control.
- Restrict access to `logs/` because current API-key failure logging can expose the key.
- Treat `state.json` as private metadata; it contains absolute paths and Anki IDs.
- Review notes before sending them to Gemini.
- Do not put secrets in the prompt or eligible note bodies.
- Remove API keys, local paths, state data, and note content from issue reports.

## Troubleshooting

### `.env` is ignored

Confirm it is at repository root, the same location as `pyproject.toml`, or set environment variables directly.

### Missing-field table

Provide the exact field named in **Environment Results**. Remember that `ANKI_URL`, `INCLUDE_TAGS`, and `EXCLUDE_TAGS` have defaults; other model fields do not.

### Tag list fails to parse

Use JSON array syntax:

```env
INCLUDE_TAGS=["Python", "Math"]
```

### No notes pass filtering

Check exact case and YAML-list structure. An excluded tag always blocks the note.

### Prompt file is missing

Resolve the path relative to the repository root. Doctor may fail before displaying the runtime table because AI construction reads the prompt immediately.

### Vault folder is missing

Create both configured subfolders. Process/migrate log a missing root and return no notes; other services may raise when they directly call `.iterdir()`.

### State folder fails in doctor

Doctor does not create it. Create it manually or run a normal command after the rest of configuration is valid.

### State JSON is malformed

Back up the file, repair valid JSON and required fields, or deliberately reset it only when you understand the synchronization consequences.

### Anki rejects fields

Add `NoteID` to `Basic` with exact capitalization.

### Too many AI requests

Each unsuccessful Anki insertion can cause full regeneration, and Gemini `ClientError` retries are unbounded. Inspect logs before retrying the entire command.
