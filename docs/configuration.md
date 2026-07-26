# Configuration

This guide explains every configuration value used by **Obsidian2Anki 0.1.0**, how paths are resolved, how tag filters interact, and which important behaviors are currently fixed in source code rather than configurable through `.env`.

> [!IMPORTANT]
> The current `Settings` model defines no fallback values. Every variable listed in this document must be present, including list settings that are intentionally empty.

For initial installation and external-service setup, see [Installation](installation.md).

## Contents

- [Configuration source](#configuration-source)
- [Complete example](#complete-example)
- [Settings reference](#settings-reference)
- [Gemini configuration](#gemini-configuration)
- [Anki configuration](#anki-configuration)
- [Obsidian vault configuration](#obsidian-vault-configuration)
- [State configuration](#state-configuration)
- [Tag filtering](#tag-filtering)
- [Anki insertion retries](#anki-insertion-retries)
- [Path-resolution rules](#path-resolution-rules)
- [Environment examples](#environment-examples)
- [Values not currently configurable](#values-not-currently-configurable)
- [Validation and startup behavior](#validation-and-startup-behavior)
- [Security guidance](#security-guidance)
- [Troubleshooting](#troubleshooting)

## Configuration Source

Obsidian2Anki loads settings with `pydantic-settings` from:

```text
<repository-root>/.env
```

The repository root is calculated from the installed source layout and stored as `BASE_DIR`. In the recommended editable installation, it is the directory containing `pyproject.toml`.

Create the local configuration file from the provided example:

Linux or macOS:

```bash
cp .env.example .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

Windows Command Prompt:

```bat
copy .env.example .env
```

The `.env` file should remain local and must not be committed.

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

This example processes every non-excluded note, uses `00_Inbox` for normal processing, moves successfully processed notes into `01_Notes`, and stores local state in `data/state.json`.

## Settings Reference

| Variable                             | Type                     | Required | Recommended example            | Purpose                                                                             |
| ------------------------------------ | ------------------------ | :------: | ------------------------------ | ----------------------------------------------------------------------------------- |
| `API_KEY`                            | String                   |   Yes    | `your_gemini_api_key`          | Authenticates requests to the Google Gemini API.                                    |
| `PROMPT_FILE`                        | String path              |   Yes    | `input/prompt.md`              | Selects the prompt prepended to each note sent to Gemini.                           |
| `ANKI_URL`                           | URL string               |   Yes    | `http://localhost:8765/`       | AnkiConnect HTTP endpoint.                                                          |
| `DECK_NAME`                          | String                   |   Yes    | `Programming`                  | Exact Anki deck used for generated notes and statistics.                            |
| `LOCAL_VAULT`                        | Directory path           |   Yes    | `/home/user/Documents/MyVault` | Root directory of the Obsidian vault.                                               |
| `INBOX_FOLDER`                       | Vault-relative path      |   Yes    | `00_Inbox`                     | Folder read by `obsidian2anki process`.                                             |
| `MAIN_NOTES_FOLDER`                  | Vault-relative path      |   Yes    | `01_Notes`                     | Destination for processed inbox notes and source for migration.                     |
| `STATE_FOLDER`                       | Repository-relative path |   Yes    | `data`                         | Directory in which `state.json` is created and maintained.                          |
| `INCLUDE_TAGS`                       | JSON array of strings    |   Yes    | `[]`                           | Optional allowlist for note tags.                                                   |
| `EXCLUDE_TAGS`                       | JSON array of strings    |   Yes    | `[]`                           | Denylist for note tags. Any match prevents processing.                              |
| `MAX_RETRIES_ON_ANKI_DUPLICATE_CARD` | Integer                  |   Yes    | `3`                            | Number of regeneration-and-insertion retries after the first failed Anki insertion. |

> [!NOTE]
> “Required” means the variable must exist in `.env`; it does not mean it must contain a non-empty value. Empty tag lists are valid, but an empty API key, vault path, or deck name will not produce a usable setup.

## Gemini Configuration

### `API_KEY`

`API_KEY` is passed directly to the Google Gen AI client:

```env
API_KEY=your_actual_gemini_api_key
```

The key is used for both:

- validating the Gemini connection in `obsidian2anki doctor`;
- generating flashcards during `process` and `migrate`.

A syntactically present but invalid key still allows Pydantic settings construction, but Gemini validation and generation will fail.

### `PROMPT_FILE`

`PROMPT_FILE` selects the text prompt used for card generation:

```env
PROMPT_FILE=input/prompt.md
```

The path is resolved relative to the repository root:

```text
<repository-root>/input/prompt.md
```

The current AI flow reads the full prompt once when the application is constructed. It then appends a JSON representation of the note containing:

- `title`;
- `tags`;
- processed note `content`;
- existing `anki_cards` metadata.

The note ID and filesystem path are excluded from the model input.

A custom prompt does not need a placeholder such as `{note}`. The note JSON is appended automatically.

Example custom location:

```env
PROMPT_FILE=input/prompts/programming.md
```

The corresponding file must exist at:

```text
<repository-root>/input/prompts/programming.md
```

> [!WARNING]
> A missing or unreadable prompt prevents dependency construction. In the current application structure, this can stop commands before their handlers run, including `doctor`.

### Prompt output requirements

Gemini is requested to return structured JSON matching the internal flashcard schema:

```json
{
	"cards": [
		{
			"question": "...",
			"answer": "...",
			"tags": ["..."]
		}
	]
}
```

Keep custom prompts compatible with this purpose. Avoid asking for Markdown surrounding the JSON, unrelated explanations, or a different object shape.

The model name is currently hardcoded and cannot be selected through `.env`; see [Values not currently configurable](#values-not-currently-configurable).

## Anki Configuration

### `ANKI_URL`

`ANKI_URL` is the HTTP endpoint used for every AnkiConnect request:

```env
ANKI_URL=http://localhost:8765/
```

The standard local AnkiConnect endpoint is expected. Keep the trailing slash or omit it consistently; both normally resolve to the same local server endpoint, but the documented project value includes it.

Obsidian2Anki uses AnkiConnect API version `6` and sends JSON requests to this URL.

Commands that depend on Anki include:

- `process`;
- `migrate`;
- `clear`;
- `delete-card`;
- `delete-note`;
- `stats`;
- `doctor`.

Anki should be open with AnkiConnect enabled. The application attempts to find and launch an `anki` executable when Anki is unreachable, but this depends on the executable being available on the system `PATH`.

### `DECK_NAME`

`DECK_NAME` is the exact deck name used by the application:

```env
DECK_NAME=Programming
```

Deck names are matched as strings. Preserve capitalization, spaces, and nested-deck separators exactly.

Nested Anki deck example:

```env
DECK_NAME=Knowledge::Programming
```

This setting is used to:

- assign generated notes to the configured deck;
- locate notes for `stats`;
- verify deck existence in `doctor`.

The processing code attempts to create the configured deck when it is missing, but `doctor` currently reports a missing deck as a failed check. Creating the deck manually during installation gives the clearest setup and diagnostic result.

### Required Anki note type

The Anki note type is not selected through `.env`. Generated notes currently use the hardcoded model name:

```text
Basic
```

That model must expose these fields:

```text
Front
Back
NoteID
```

`Front` and `Back` exist in Anki's standard Basic note type. `NoteID` must be added manually. Field names are case-sensitive.

## Obsidian Vault Configuration

### `LOCAL_VAULT`

`LOCAL_VAULT` is the root directory of the Obsidian vault:

```env
LOCAL_VAULT=/home/user/Documents/MyVault
```

Use an absolute path. The vault manager constructs it directly with `Path(LOCAL_VAULT)`, so a relative value would be resolved against the process working directory rather than reliably against the repository.

Linux:

```env
LOCAL_VAULT=/home/nika/Documents/MyVault
```

macOS:

```env
LOCAL_VAULT=/Users/nika/Documents/MyVault
```

Windows:

```env
LOCAL_VAULT=C:/Users/Nika/Documents/MyVault
```

Forward slashes are recommended on Windows because they avoid accidental backslash escaping and remain accepted by Python path handling.

Do not include `INBOX_FOLDER` or `MAIN_NOTES_FOLDER` in this value.

Correct:

```env
LOCAL_VAULT=C:/Users/Nika/Documents/MyVault
INBOX_FOLDER=00_Inbox
MAIN_NOTES_FOLDER=01_Notes
```

Incorrect:

```env
LOCAL_VAULT=C:/Users/Nika/Documents/MyVault/00_Inbox
```

### `INBOX_FOLDER`

`INBOX_FOLDER` is resolved inside `LOCAL_VAULT` and is read by normal processing:

```env
INBOX_FOLDER=00_Inbox
```

Resolved path:

```text
<LOCAL_VAULT>/00_Inbox
```

`obsidian2anki process` reads immediate files from this folder. After a note is processed successfully, its metadata is updated and the file is moved to `MAIN_NOTES_FOLDER`.

Nested vault-relative folders are allowed when the directory already exists:

```env
INBOX_FOLDER=Flashcards/Inbox
```

### `MAIN_NOTES_FOLDER`

`MAIN_NOTES_FOLDER` is also resolved inside the vault:

```env
MAIN_NOTES_FOLDER=01_Notes
```

Resolved path:

```text
<LOCAL_VAULT>/01_Notes
```

It serves two roles:

1. destination for successfully processed inbox notes;
2. source directory scanned by `obsidian2anki migrate` and `format-notes`.

The folder must already exist before processing because the current vault manager does not create vault folders automatically.

### Folder-scanning behavior

The current implementation:

- scans only immediate directory entries;
- does not recurse into nested directories;
- processes every immediate regular file;
- does not currently filter files by the `.md` extension.

Keep unrelated files out of the configured inbox and main-notes directories.

Folder names and path capitalization must match the filesystem exactly on case-sensitive systems.

## State Configuration

### `STATE_FOLDER`

`STATE_FOLDER` controls where Obsidian2Anki stores its local processing state:

```env
STATE_FOLDER=data
```

This path is resolved relative to the repository root:

```text
<repository-root>/data/state.json
```

The updated `StateManager` automatically performs both initialization steps:

```python
self.state_folder.mkdir(parents=True, exist_ok=True)
self.state_file.touch(exist_ok=True)
```

Therefore:

- the configured state directory is created when missing;
- missing parent directories are created;
- `state.json` is created when missing;
- an empty `state.json` is loaded as an empty state.

No manual `mkdir`, `touch`, or `{}` initialization is required.

Custom example:

```env
STATE_FOLDER=.obsidian2anki/state
```

Resolved path:

```text
<repository-root>/.obsidian2anki/state/state.json
```

The repository directory must be writable by the current user.

### What state stores

Each processed note is indexed by its YAML `id`. Its state entry includes:

- note title;
- absolute vault path;
- SHA-256 hash of processed note content;
- generated Anki note IDs;
- card count;
- processing timestamp;
- update timestamp.

This state allows migration to skip unchanged notes and enables delete and clear operations to connect Obsidian notes with generated Anki notes.

> [!CAUTION]
> Do not edit or delete `state.json` casually. Losing it breaks the application's record of which Anki notes belong to which Obsidian notes. Back it up together with the vault before destructive maintenance.

### State filename

Only the directory is configurable. The filename is currently fixed as:

```text
state.json
```

## Tag Filtering

### `INCLUDE_TAGS`

`INCLUDE_TAGS` is an allowlist:

```env
INCLUDE_TAGS=["Python", "JavaScript"]
```

Behavior:

- `[]` allows every note that is not excluded;
- a non-empty list requires at least one exact matching note tag.

The matching rule is **any**, not all. A note tagged only with `Python` passes the example above even though it does not contain `JavaScript`.

### `EXCLUDE_TAGS`

`EXCLUDE_TAGS` is a denylist:

```env
EXCLUDE_TAGS=["Draft", "Archive"]
```

If a note contains any exact excluded tag, it is skipped.

Exclusion takes precedence over inclusion. A note with both `Python` and `Draft` is not processed when using the two examples above.

### Combined logic

A note is eligible only when both conditions are true:

```text
no note tag appears in EXCLUDE_TAGS
AND
INCLUDE_TAGS is empty OR at least one note tag appears in INCLUDE_TAGS
```

Example configuration:

```env
INCLUDE_TAGS=["Python", "JavaScript"]
EXCLUDE_TAGS=["Draft", "Archive"]
```

| Note tags                 | Result  | Reason                                              |
| ------------------------- | ------- | --------------------------------------------------- |
| `Python`                  | Process | Matches an included tag and has no excluded tag.    |
| `JavaScript`, `Reference` | Process | At least one included tag matches.                  |
| `React`                   | Skip    | No included tag matches.                            |
| `Python`, `Draft`         | Skip    | Excluded tags override included tags.               |
| `Draft`                   | Skip    | Contains an excluded tag.                           |
| No tags                   | Skip    | The include list is non-empty and no tag can match. |

With both lists empty:

```env
INCLUDE_TAGS=[]
EXCLUDE_TAGS=[]
```

all notes pass the tag filter.

### List syntax

Tag settings must use JSON-array syntax:

```env
INCLUDE_TAGS=["Python", "React"]
EXCLUDE_TAGS=["Archive"]
```

Do not use comma-separated plain text:

```env
# Invalid for list parsing
INCLUDE_TAGS=Python,React
```

Do not remove empty list variables:

```env
INCLUDE_TAGS=[]
EXCLUDE_TAGS=[]
```

### Matching rules

Tag matching is:

- exact;
- case-sensitive;
- based on whole strings.

These values are different:

```text
Python
python
#Python
```

The note parser expects YAML frontmatter `tags` to be a list. For example:

```yaml
---
id: 5df48ffc-c025-4a52-92ee-394a404f80d0
tags:
  - Python
  - Iterators
---
```

A non-list `tags` value is currently treated as an empty tag list by the vault parser.

## Anki Insertion Retries

### `MAX_RETRIES_ON_ANKI_DUPLICATE_CARD`

```env
MAX_RETRIES_ON_ANKI_DUPLICATE_CARD=3
```

The value controls how many times Obsidian2Anki regenerates the flashcard batch and tries Anki insertion again after the initial insertion returns no IDs.

With a value of `3`, the maximum sequence is:

1. initial Gemini generation and Anki insertion;
2. retry 1 with a newly generated batch;
3. retry 2 with a newly generated batch;
4. retry 3 with a newly generated batch.

Therefore, `3` allows up to **four total insertion attempts**.

Set it to zero to disable regeneration retries:

```env
MAX_RETRIES_ON_ANKI_DUPLICATE_CARD=0
```

Use a non-negative integer. The current settings model validates the type as `int` but does not define a minimum value.

Despite the variable name, the retry loop is triggered by any falsy result from Anki note insertion, not only a confirmed duplicate-card error.

Increasing this value can increase Gemini requests, processing time, and the chance of producing alternative wording for the same note.

## Path-Resolution Rules

Obsidian2Anki does not resolve every path from the same base.

| Setting             | Resolution base                    | Example                       |
| ------------------- | ---------------------------------- | ----------------------------- |
| `.env`              | Repository root                    | `<repo>/.env`                 |
| `PROMPT_FILE`       | Repository root                    | `<repo>/input/prompt.md`      |
| `STATE_FOLDER`      | Repository root                    | `<repo>/data/state.json`      |
| `LOCAL_VAULT`       | Used directly as a filesystem path | `/home/user/MyVault`          |
| `INBOX_FOLDER`      | `LOCAL_VAULT`                      | `/home/user/MyVault/00_Inbox` |
| `MAIN_NOTES_FOLDER` | `LOCAL_VAULT`                      | `/home/user/MyVault/01_Notes` |
| Log directory       | Repository root, fixed in code     | `<repo>/logs`                 |

Recommended rules:

1. use repository-relative values for `PROMPT_FILE` and `STATE_FOLDER`;
2. use an absolute path for `LOCAL_VAULT`;
3. use vault-relative paths for `INBOX_FOLDER` and `MAIN_NOTES_FOLDER`;
4. do not begin vault-relative folder settings with the vault path again.

## Environment Examples

### Process every note

```env
INCLUDE_TAGS=[]
EXCLUDE_TAGS=[]
```

### Process only programming notes

```env
INCLUDE_TAGS=["Python", "JavaScript", "React", "CSS"]
EXCLUDE_TAGS=[]
```

### Process programming notes except drafts

```env
INCLUDE_TAGS=["Python", "JavaScript", "React", "CSS"]
EXCLUDE_TAGS=["Draft", "Archive", "Ignore"]
```

### Use nested vault folders

```env
LOCAL_VAULT=/home/user/Documents/Knowledge
INBOX_FOLDER=Flashcards/Inbox
MAIN_NOTES_FOLDER=Flashcards/Notes
```

Both nested directories must already exist.

### Keep state in a hidden project directory

```env
STATE_FOLDER=.local/obsidian2anki
```

This creates:

```text
<repository-root>/.local/obsidian2anki/state.json
```

Review `.gitignore` before choosing a custom state path. The state file should not be committed.

### Use a nested Anki deck

```env
DECK_NAME=Knowledge::Computer Science::Python
```

### Windows example

```env
API_KEY=your_gemini_api_key
PROMPT_FILE=input/prompt.md

ANKI_URL=http://localhost:8765/
DECK_NAME=Programming

LOCAL_VAULT=C:/Users/Nika/Documents/MyVault
INBOX_FOLDER=00_Inbox
MAIN_NOTES_FOLDER=01_Notes

STATE_FOLDER=data

INCLUDE_TAGS=["Python", "JavaScript"]
EXCLUDE_TAGS=["Draft", "Archive"]

MAX_RETRIES_ON_ANKI_DUPLICATE_CARD=3
```

## Values Not Currently Configurable

The following behavior is fixed in source code in version `0.1.0`:

| Behavior                   | Current value or rule                   | Source area               |
| -------------------------- | --------------------------------------- | ------------------------- |
| Gemini model               | `gemini-3.1-flash-lite`                 | `core/ai.py`              |
| Initial Gemini retry delay | `7` seconds                             | `AI.__init__`             |
| Maximum Gemini retry delay | `60` seconds                            | `AI.generate_note_cards`  |
| Gemini retry pattern       | Doubles after each caught `ClientError` | `core/ai.py`              |
| AnkiConnect API version    | `6`                                     | `utils/anki_connecter.py` |
| Anki note type             | `Basic`                                 | `models.py`               |
| Anki fields                | `Front`, `Back`, `NoteID`               | `AnkiCard.serialize`      |
| State filename             | `state.json`                            | `core/state_manager.py`   |
| Log directory              | `<repository-root>/logs`                | `utils/logger.py`         |
| Log filename               | `obsidian2anki.log`                     | `utils/logger.py`         |
| Log rotation               | 5 MiB, three backups                    | `utils/logger.py`         |
| Vault scan depth           | Immediate files only                    | `core/vault_manager.py`   |
| Input extension filter     | None                                    | `core/vault_manager.py`   |

Changing these behaviors currently requires a source-code change rather than an `.env` update.

## Validation and Startup Behavior

### All settings load together

The `Settings` class contains every variable without a Python default. Pydantic validates them as one configuration object.

A missing value can produce a validation error similar to:

```text
Field required
```

Keep every key from `.env.example`, even when a list is intentionally empty.

### Settings are cached

`get_settings()` is decorated with `lru_cache`, and several modules obtain settings at import time. As a result:

- one CLI invocation uses one stable settings object;
- editing `.env` does not alter a process that is already running;
- rerun the command after changing `.env`.

Normal CLI use starts a fresh process, so no manual cache clearing is needed between separate commands.

### Dependency construction happens early

The application constructs the vault manager, Anki manager, state manager, AI client, and services before dispatching the selected command.

Consequences include:

- `.env` must be complete before normal CLI use;
- `PROMPT_FILE` must exist and be readable;
- `STATE_FOLDER` must point to a writable location;
- an incomplete configuration may fail before `doctor` can report its table.

### Verify configuration

After editing `.env`, run:

```bash
obsidian2anki doctor
```

For additional logs:

```bash
obsidian2anki --verbose doctor
```

The diagnostic command checks the Python version, `.env`, vault paths, state folder, API key, prompt file, deck, and Anki connectivity.

Because the AI client and settings are constructed before diagnostics, use Pydantic error output and the troubleshooting section below when `doctor` cannot start.

## Security Guidance

### Protect `API_KEY`

- Keep `.env` out of version control.
- Never place the real key in `.env.example`.
- Do not paste `.env` into public issues or screenshots.
- Rotate the key immediately if it is exposed.

> [!WARNING]
> In the current implementation, failed API-key validation logs the supplied invalid key value. Treat `logs/obsidian2anki.log` and its rotated backups as sensitive. Do not upload them publicly without reviewing and redacting secrets.

### Protect local state

`state.json` contains absolute note paths and Anki note IDs. It does not contain the Gemini key, but it can expose local filesystem structure and should remain private.

### Review custom prompts

A custom prompt is combined with the content of every processed note. Do not process confidential notes unless sending their content to the configured AI service is acceptable.

## Troubleshooting

### `.env` is ignored

Confirm that the file is named exactly:

```text
.env
```

and is stored beside `pyproject.toml`, not inside `src/`, `docs/`, or the vault.

### Pydantic reports missing fields

Compare `.env` against `.env.example`. All of these keys must exist:

```text
API_KEY
PROMPT_FILE
ANKI_URL
DECK_NAME
LOCAL_VAULT
INBOX_FOLDER
MAIN_NOTES_FOLDER
STATE_FOLDER
INCLUDE_TAGS
EXCLUDE_TAGS
MAX_RETRIES_ON_ANKI_DUPLICATE_CARD
```

Use `[]` for intentionally empty tag lists.

### A tag list cannot be parsed

Use valid JSON arrays with double-quoted strings:

```env
INCLUDE_TAGS=["Python", "React"]
```

Do not use Python set syntax, YAML list syntax, or an unquoted comma-separated string.

### No notes pass the tag filter

Check all of the following:

- note frontmatter stores `tags` as a YAML list;
- capitalization matches `.env` exactly;
- no tag appears in `EXCLUDE_TAGS`;
- at least one tag appears in `INCLUDE_TAGS` when that list is non-empty;
- note tags do not include a leading `#` unless the `.env` value also includes it.

Temporarily disable filters to isolate the problem:

```env
INCLUDE_TAGS=[]
EXCLUDE_TAGS=[]
```

### The prompt file is not found

`PROMPT_FILE` is repository-relative, not relative to the current terminal directory.

For:

```env
PROMPT_FILE=input/prompt.md
```

verify:

```text
<repository-root>/input/prompt.md
```

### The vault is not found

Use an absolute `LOCAL_VAULT` path and confirm the directory exists.

Do not wrap the value in mismatched quotes. On Windows, prefer forward slashes.

### The inbox or main folder is not found

These folders are resolved below the vault root and are not created automatically.

For:

```env
LOCAL_VAULT=/home/user/MyVault
INBOX_FOLDER=00_Inbox
MAIN_NOTES_FOLDER=01_Notes
```

create:

```text
/home/user/MyVault/00_Inbox
/home/user/MyVault/01_Notes
```

### The state directory cannot be created

`StateManager` creates the configured directory automatically. A failure usually means:

- the repository path is not writable;
- `STATE_FOLDER` points into a protected location;
- a regular file already occupies one of the directory path components;
- the configured path is invalid for the operating system.

### `state.json` contains invalid JSON

An empty file is accepted, but a non-empty file must contain valid JSON matching the state schema.

Restore a known-good backup. Do not replace the file with `{}` unless you intentionally accept losing all processing relationships.

### Anki is unreachable

Check:

```env
ANKI_URL=http://localhost:8765/
```

Then verify that Anki is open and AnkiConnect is enabled.

### The deck check fails

Ensure `DECK_NAME` matches the Anki deck exactly. Check spaces, capitalization, and `::` separators for nested decks.

### Anki reports an unknown field

The current note model sends `Front`, `Back`, and `NoteID`. Add `NoteID` to the Anki `Basic` note type and restart or reopen the relevant Anki screens.

### Too many Gemini requests occur

Lower:

```env
MAX_RETRIES_ON_ANKI_DUPLICATE_CARD=1
```

or disable insertion regeneration retries:

```env
MAX_RETRIES_ON_ANKI_DUPLICATE_CARD=0
```

This setting does not control the separate Gemini `ClientError` retry loop, whose delay behavior is currently fixed in source code.

## Next Step

After configuration is valid, continue with the workflow documentation to understand how inbox processing, migration, state tracking, metadata updates, and Anki synchronization work together.
