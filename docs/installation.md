# Installation

These instructions describe source installation for the current `0.1.0` package plus the unreleased diagnostics refactor present in this repository snapshot.

> [!IMPORTANT]
> Obsidian2Anki is not yet a one-command setup. You must configure `.env`, prepare vault folders, install AnkiConnect, and add `NoteID` to Anki's `Basic` note type.

## Contents

- [Requirements](#requirements)
- [1. Clone the Repository](#1-clone-the-repository)
- [2. Create a Virtual Environment](#2-create-a-virtual-environment)
- [3. Install the Package](#3-install-the-package)
- [4. Create Configuration](#4-create-configuration)
- [5. Prepare Gemini](#5-prepare-gemini)
- [6. Prepare Anki](#6-prepare-anki)
- [7. Prepare the Obsidian Vault](#7-prepare-the-obsidian-vault)
- [8. Configure Templater](#8-configure-templater)
- [9. Initialize and Diagnose](#9-initialize-and-diagnose)
- [10. Process a Test Note](#10-process-a-test-note)
- [Shell Completion](#shell-completion)
- [Updating](#updating)
- [Uninstalling](#uninstalling)
- [Troubleshooting](#troubleshooting)

## Requirements

| Requirement | Purpose |
| --- | --- |
| Python 3.12+ | Runtime and source syntax |
| Git | Clone/update source |
| Obsidian | Source-note editor and vault |
| Templater plugin | Generate stable UUID frontmatter |
| Anki Desktop | Stores generated notes |
| AnkiConnect | Local HTTP integration |
| Gemini API key | AI generation and doctor validation |

Verify Python:

```bash
python --version
```

On systems where `python` points elsewhere:

```bash
python3.12 --version
```

## 1. Clone the Repository

```bash
git clone https://github.com/NikaMalakmadze/Obsidian2Anki.git
cd Obsidian2Anki
```

The working directory should contain:

```text
pyproject.toml
.env.example
src/
input/
template/
docs/
```

Relative prompt, state, and log paths are based on this repository root as calculated by `BASE_DIR`.

## 2. Create a Virtual Environment

### Linux and macOS

```bash
python3.12 -m venv venv
source venv/bin/activate
```

### Windows PowerShell

```powershell
py -3.12 -m venv venv
venv\Scripts\Activate.ps1
```

### Windows Command Prompt

```bat
py -3.12 -m venv venv
venv\Scripts\activate.bat
```

Upgrade packaging tools:

```bash
python -m pip install --upgrade pip
```

## 3. Install the Package

Editable source installation:

```bash
python -m pip install -e .
```

Verify that the console entry point exists:

```bash
obsidian2anki --help
obsidian2anki --version
```

The command uses distribution metadata for `--version`, so installation is required even when running from the repository.

## 4. Create Configuration

### Copy the example

Linux/macOS:

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

### Edit required values

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

Required model fields with no defaults:

- `STATE_FOLDER`
- `API_KEY`
- `PROMPT_FILE`
- `DECK_NAME`
- `LOCAL_VAULT`
- `INBOX_FOLDER`
- `MAIN_NOTES_FOLDER`
- `MAX_RETRIES_ON_ANKI_DUPLICATE_CARD`

`ANKI_URL`, `INCLUDE_TAGS`, and `EXCLUDE_TAGS` have defaults in code.

### Paths

Use an absolute vault path.

Linux/macOS:

```env
LOCAL_VAULT=/home/nika/Documents/MyVault
```

Windows:

```env
LOCAL_VAULT=C:/Users/Nika/Documents/MyVault
```

`PROMPT_FILE` and `STATE_FOLDER` are repository-relative unless absolute.

### Tag lists

Use JSON-array syntax:

```env
INCLUDE_TAGS=["Python", "JavaScript"]
EXCLUDE_TAGS=["Draft", "Archive"]
```

Matching is exact and case-sensitive.

For full settings behavior, see [Configuration](configuration.md).

## 5. Prepare Gemini

Place the Gemini API key in `API_KEY`.

The current AI layer:

- creates `google.genai.Client` during normal app construction;
- reads the prompt immediately;
- uses hard-coded model `gemini-3.1-flash-lite`;
- requests JSON matching `FlashcardBatch`.

Review `input/prompt.md` before processing real notes. Its current language rule is contradictory:

```text
Preserve the language of the note. Write On English!!!
```

Edit it according to the intended behavior.

> [!CAUTION]
> Eligible note title, tags, and normalized body are sent to Gemini. Do not process sensitive notes unless external processing is acceptable.

> [!WARNING]
> A failed API-key validation currently logs the supplied key. Protect `logs/obsidian2anki.log` and do not share it unredacted.

## 6. Prepare Anki

### Install Anki Desktop

Install and start Anki Desktop.

### Install AnkiConnect

Install the AnkiConnect add-on and restart Anki when required.

The default endpoint is:

```text
http://localhost:8765
```

### Create the destination deck

Create the exact deck named by `DECK_NAME`.

The insertion code can create a missing deck, but doctor reports a missing configured deck as a failed runtime row. Creating it manually produces a clean setup check.

### Add `NoteID` to `Basic`

Open:

```text
Tools → Manage Note Types → Basic → Fields
```

Add:

```text
NoteID
```

Keep the existing fields:

```text
Front
Back
```

The code always serializes:

```json
{
  "modelName": "Basic",
  "fields": {
    "Front": "...",
    "Back": "...",
    "NoteID": "..."
  }
}
```

Anki will reject insertion when the field does not exist.

### Keep Anki open

Doctor's connectivity check does not auto-launch Anki. Normal AnkiConnect operations may attempt to run an executable named `anki` from `PATH`, but this is not reliable on every platform or installation layout.

## 7. Prepare the Obsidian Vault

Create the folders configured in `.env`:

```text
MyVault/
├── 00_Inbox/
├── 01_Notes/
└── Templates/
```

Both inbox and main folder must already exist.

### Process/migrate discovery

These commands recursively scan nested directories and include only `.md` files.

### Formatting/statistics discovery

`format-notes` and `stats` inspect immediate entries only and do not consistently restrict them to Markdown. Keep unrelated files out of the configured roots until those implementations are unified.

### Destination movement

Successfully processed inbox notes are moved to the root of `MAIN_NOTES_FOLDER`. Nested inbox directory structure is not preserved.

## 8. Configure Templater

### Copy the template

Copy:

```text
template/note.md
```

into the vault's templates folder.

The bundled template is:

```markdown
---
id: <% crypto.randomUUID() %>
tags:
---

---
```

The first block is YAML frontmatter. The final `---` is body content and is later removed by the normalization rules as a horizontal rule.

### Enable Templater

1. Open Obsidian Settings.
2. Enable Community Plugins.
3. Install and enable Templater.
4. Set its template folder.
5. Configure a folder template for the inbox if desired.

### Verify expansion

A new note should contain a real UUID, not the literal template expression:

```yaml
---
id: 9fb66ee5-6778-4bf4-817d-f82646d1237e
tags:
---
```

### Add tags as a YAML list

```yaml
tags:
  - Python
  - Functions
```

A scalar or comma-separated string is treated as an empty tag list by normal note parsing.

### Unique IDs

Never copy one already-expanded frontmatter ID into several notes. State is keyed only by that ID.

## 9. Initialize and Diagnose

### Understand state initialization

Normal app construction creates:

```text
<STATE_FOLDER>/state.json
```

Doctor is now independent and does **not** construct `StateManager`. Therefore:

- doctor can report missing/invalid `.env` values;
- doctor does not create the state folder;
- a fresh setup may show the state-folder check as failed.

You may create the default directory manually:

Linux/macOS:

```bash
mkdir -p data
```

Windows PowerShell:

```powershell
New-Item -ItemType Directory -Force data
```

The repository normally already contains `data/.gitkeep`.

### Run doctor

```bash
obsidian2anki doctor
```

#### Environment-results mode

When settings are invalid, the table shows:

- field;
- error type;
- location;
- message;
- value.

Key-like values are redacted.

#### Runtime-results mode

When settings are valid, it checks:

- Python 3.12+;
- `.env`;
- local vault;
- inbox;
- main folder;
- state folder;
- prompt file;
- Gemini API key;
- Anki;
- deck.

> [!CAUTION]
> `AI()` reads the prompt before runtime checks are assembled. A missing prompt may raise before the table can report it. Check `PROMPT_FILE` manually when doctor stops after the environment phase without a runtime table.

> [!NOTE]
> Failed rows currently do not set a non-zero exit status. Read the table instead of relying only on `$?`.

### Preview inbox discovery

```bash
obsidian2anki --verbose process --dry-run
```

This parses and counts inbox notes but returns before tag filtering. It is not a full plan of eligible notes.

## 10. Process a Test Note

Create `00_Inbox/Functions.md`:

```markdown
---
id: 9fb66ee5-6778-4bf4-817d-f82646d1237e
tags:
  - Python
---

# Functions

A function groups reusable behavior and may accept arguments and return a value.
```

Run:

```bash
obsidian2anki process
```

On success, expect:

1. one Gemini request, unless retry behavior is triggered;
2. one `addNotes` request to AnkiConnect;
3. `anki_cards` inserted into frontmatter;
4. file moved to `MAIN_NOTES_FOLDER` root;
5. a state entry written at service completion;
6. generated Anki notes in the configured deck.

Inspect:

```text
logs/obsidian2anki.log
```

and verify the Anki note fields.

### Test migration

Edit the moved note's normalized content and run:

```bash
obsidian2anki --verbose migrate --dry-run
obsidian2anki migrate
```

> [!WARNING]
> Current replacement deletes old generated Anki notes before the new batch is safely generated and inserted.

## Shell Completion

The parser integrates `argcomplete`, but shell activation is separate from package installation.

For Bash, one common approach is:

```bash
activate-global-python-argcomplete --user
```

or register only this command according to the local `argcomplete` setup.

Completion is optional; command execution does not depend on it.

## Updating

From the repository:

```bash
git pull
python -m pip install -e .
```

Before updating:

- back up the vault;
- back up Anki;
- back up `state.json`;
- read `CHANGELOG.md`;
- compare `.env.example` with local `.env`.

The state schema is not versioned yet.

## Uninstalling

Remove the installed package:

```bash
python -m pip uninstall Obsidian2Anki
```

Then optionally remove the virtual environment and source checkout.

Uninstalling Python code does not remove:

- generated Anki notes;
- vault `anki_cards` metadata;
- moved source files;
- local state or logs.

Use `clear` only after backups and while the installed code can still access all tracked resources.

## Troubleshooting

### `obsidian2anki` is not found

Activate the virtual environment and reinstall editable mode.

### Python syntax error during import

Use Python 3.12 or later.

### Environment Results shows missing fields

Fill every required field. `ANKI_URL`, `INCLUDE_TAGS`, and `EXCLUDE_TAGS` are the only configured defaults relevant here.

### Doctor reports missing state folder

Doctor does not create it. Create it manually or run a normal command after all other startup requirements are valid.

### Doctor stops before runtime table

Verify the prompt path and file permissions. Prompt loading occurs while constructing `AI`.

### State JSON is malformed

Normal commands may fail during `build_app()` before command error handling. Back up and repair valid JSON.

### Anki is unreachable

Open Anki manually, verify AnkiConnect, and verify `ANKI_URL`.

### Deck check fails

Create the exact `DECK_NAME`. Nested deck names must match exactly.

### Anki reports an unknown field

Add `NoteID` to `Basic` with exact case.

### No inbox notes are found

Confirm the folder path and `.md` suffix. Discovery is recursive but suffix comparison is exact.

### Notes are skipped

Check exact include/exclude tag spelling and YAML-list syntax.

### A filename has an unexpected title

Only the portion before the first period becomes the title.

### Templater expression remains literal

Insert the note through Templater or run the template command; simply copying template text does not evaluate JavaScript.

### Formatting damages a file

Restore from backup. The formatter assumes one specific legacy first-line hashtag format and is not a general frontmatter repair tool.
