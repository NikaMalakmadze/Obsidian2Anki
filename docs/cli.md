# CLI Reference

This guide documents the command-line behavior implemented in the current repository snapshot.

> [!WARNING]
> Several commands modify Obsidian frontmatter, move source files, delete Anki notes, and rewrite local state. Back up the vault and Anki collection before the first real migration, formatting run, or bulk deletion.

## Contents

- [Command Structure](#command-structure)
- [Global Options](#global-options)
- [Command Summary](#command-summary)
- [`process`](#process)
- [`migrate`](#migrate)
- [`format-notes`](#format-notes)
- [`clear`](#clear)
- [`delete-card`](#delete-card)
- [`delete-note`](#delete-note)
- [`doctor`](#doctor)
- [`stats`](#stats)
- [Dry-Run Matrix](#dry-run-matrix)
- [Logging and Terminal Output](#logging-and-terminal-output)
- [Exit Statuses](#exit-statuses)
- [Shell Completion](#shell-completion)
- [Recommended Sequences](#recommended-sequences)
- [Troubleshooting](#troubleshooting)

## Command Structure

The package installs one console entry point:

```bash
obsidian2anki <command> [command options]
```

The parser requires a subcommand.

Implemented commands:

```text
migrate
process
clear
format-notes
stats
delete-card
delete-note
doctor
```

`doctor` is registered separately from the normal application commands and is routed directly from `main.py` before `build_app()`.

## Global Options

### Help

```bash
obsidian2anki --help
obsidian2anki process --help
```

`argparse` also adds `-h` / `--help` to each parser.

### Version

```bash
obsidian2anki --version
```

The version is read through:

```python
importlib.metadata.version("obsidian2anki")
```

The package must be installed so distribution metadata exists.

### Verbose logging

```bash
obsidian2anki --verbose process
obsidian2anki -v migrate --dry-run
```

`--verbose` changes the root logging level from `INFO` to `DEBUG`.

Because it is a top-level option, it must appear before the subcommand:

```bash
# Correct
obsidian2anki --verbose process

# Incorrect
obsidian2anki process --verbose
```

## Command Summary

| Command | Main source | Main mutations | Dry run |
| --- | --- | --- | :---: |
| `process` | Recursive `.md` scan of inbox | Anki, frontmatter, file location, state | Yes |
| `migrate` | Recursive `.md` scan of main folder | Anki, frontmatter, state | Yes |
| `format-notes` | Immediate entries in main folder | Source files | Yes |
| `clear` | Local state entries | Anki, frontmatter, state | Yes |
| `delete-card <card_id>` | One tracked Anki note ID | Anki, frontmatter, state | No |
| `delete-note <note_id>` | One vault frontmatter ID | Anki, frontmatter, state | No |
| `doctor` | Settings and runtime dependencies | Logs only | No |
| `stats` | Folders, state, Anki deck | Logs only | No |

## `process`

Process notes from `INBOX_FOLDER`.

### Syntax

```bash
obsidian2anki process
obsidian2anki process --dry-run
obsidian2anki --verbose process
```

### Discovery

`VaultManager.get_folder_notes(INBOX_FOLDER)`:

- verifies the configured root exists;
- scans nested directories recursively;
- includes only files whose suffix is exactly `.md`;
- parses frontmatter and normalized body content.

A missing folder is logged by `VaultManager`, which then implicitly returns `None`. `ProcessingService` treats that like no discovered notes.

### Eligibility

Every discovered note is checked with `has_right_tags()`.

A note passes when:

```text
no excluded tag is present
AND
(include list is empty OR at least one included tag is present)
```

`process` does not use state-based `needs_processing()`. Every eligible note still in the inbox is passed to the note lifecycle.

### Real-run behavior

For each eligible note:

1. empty normalized content is logged and treated as successful without moving or recording the note;
2. existing `anki_cards` are deleted before replacement generation;
3. Gemini generates flashcards;
4. Anki insertion is attempted;
5. insertion may regenerate and retry;
6. generated IDs are written to frontmatter;
7. the file is moved to the root of `MAIN_NOTES_FOLDER`;
8. a state entry is staged;
9. state is saved in the service `finally` block.

Processing continues to later notes even when `process_note()` returns `False`, because `ProcessingService` does not inspect the return value.

### Dry run

```bash
obsidian2anki process --dry-run
```

The service:

- discovers and parses inbox notes;
- logs the total discovered count;
- returns before tag evaluation and note processing.

It does **not** currently list tag-eligible notes or planned card replacements. Use dry run as a basic discovery/startup check, not as a complete execution plan.

### Exit behavior

Many note-level failures are caught inside `NoteProcessor`, logged, and converted to `False`. Because `ProcessingService` ignores that result, the command can finish with status `0` even when one or more notes failed.

## `migrate`

Process new or changed notes already located in `MAIN_NOTES_FOLDER`.

### Syntax

```bash
obsidian2anki migrate
obsidian2anki migrate --dry-run
obsidian2anki --verbose migrate --dry-run
```

### Discovery

Migration uses the same recursive `.md` discovery as `process`.

### Eligibility

A note must:

1. pass tag filters; and
2. be absent from state or differ by normalized-content hash or filename-derived title.

Tags and raw Markdown formatting are not part of the change hash.

### Candidate preview

Before mutation, migration builds a list of candidate titles and logs:

- candidate count;
- total discovered count;
- candidate titles at debug level.

Use:

```bash
obsidian2anki --verbose migrate --dry-run
```

for the most useful preview.

### Real-run behavior

Candidates are processed sequentially through `NoteProcessor`.

Migration stops after the first `False` result. State is still saved in a `finally` block, so successful staged entries before the failure are persisted.

### Dry run

Dry run performs discovery, tag checks, and state change detection, then returns before Anki, vault, or state mutation.

Normal application construction still occurs first. It may create the state directory/file, read existing state, and read the AI prompt.

## `format-notes`

Convert legacy main-folder files to required frontmatter.

### Syntax

```bash
obsidian2anki format-notes --dry-run
obsidian2anki format-notes
```

### Intended legacy input

The converter assumes the first line contains space-separated hashtag tokens:

```markdown
#Python #Functions

# Python Functions

A function groups reusable behavior.
```

It rewrites the file as:

```yaml
---
id: <generated UUID>
tags:
  - Python
  - Functions
---
```

followed by the remaining original lines.

### Discovery limitations

Unlike process and migration, formatter discovery:

- is non-recursive;
- iterates every immediate file in `MAIN_NOTES_FOLDER`;
- does not check `.md` before frontmatter parsing;
- considers a file formatted only when both `id` and `tags` keys exist.

Directories are skipped by the mutation condition but still affect the incorrectly calculated “total notes” log because the code counts a list of Boolean values rather than only `True` entries.

### Dry run

Dry run logs the number of files that appear to need formatting and, with `--verbose`, their filename-derived titles. It does not rewrite files.

### Real-run warning

The conversion is destructive and based on one legacy convention. Back up the main folder before running it.

A blank first line produces no tags; a normal prose first line is split into tag values after only removing leading `#` characters.

## `clear`

Delete every generated Anki note referenced by local state and reset tracking.

### Syntax

```bash
obsidian2anki clear --dry-run
obsidian2anki clear
```

### Real-run behavior

For every state entry:

1. `NoteProcessor.delete_note_cards()` clears the state's generated-ID list and saves it;
2. source `anki_cards` metadata is removed;
3. every recorded Anki note ID is deleted;
4. `ClearService` removes source metadata again;
5. after the loop, state is cleared and saved.

The source Markdown files are not deleted.

### Dry run

Dry run reads state, logs the number of tracked notes, and returns before mutation. It does not verify that every source file or Anki note still exists.

### Safety

The command has no confirmation prompt. Always run dry run first and keep backups.

## `delete-card`

Delete one tracked generated Anki note ID.

### Syntax

```bash
obsidian2anki delete-card 1749920000001
```

The positional argument is parsed through `CardId`, a `NewType` over `int`.

### Behavior

1. convert the value to `int` again in `DeletingService`;
2. locate and remove the ID from state;
3. save state;
4. delete the Anki note with `deleteNotes`;
5. remove the value from source `anki_cards`;
6. remove the whole state entry when no IDs remain.

### Important data-shape limitation

`VaultManager.remove_list_item()` assumes `anki_cards` was parsed as a comma-separated string and calls `.split(",")`.

Frontmatter containing one numeric ID may parse as an integer, while YAML-list syntax parses as a list. Those representations can raise during deletion even though `_process_file()` can read them successfully.

### State limitation

`StateManager.delete_card()` removes the ID but does not update `card_count`. The count remains stale until the state entry is replaced or removed.

### No dry run

Argument commands do not implement dry-run metadata.

## `delete-note`

Delete all tracked generated Anki notes associated with one Obsidian note ID.

### Syntax

```bash
obsidian2anki delete-note 9fb66ee5-6778-4bf4-817d-f82646d1237e
```

`note_id` is a string `NewType` and is not validated as a UUID.

### Behavior

1. look up the state entry by frontmatter ID;
2. delete each recorded Anki note ID;
3. remove source `anki_cards`;
4. remove the state entry.

The source Markdown file remains.

### Unknown ID defect

When the ID is absent, the service logs:

```text
Note with id: '...' is not in state
```

but does not return. It then attempts `Path(None)` and can raise. The normal command error boundary logs the exception and returns status `1`.

### No dry run

There is no preview or confirmation option.

## `doctor`

Display configuration or runtime diagnostics.

### Syntax

```bash
obsidian2anki doctor
obsidian2anki --verbose doctor
```

### Separate startup path

Doctor runs before `build_app()`. It therefore avoids normal construction of:

- `StateManager`;
- `NoteProcessor`;
- workflow services;
- the application facade.

### Environment-results mode

If `get_settings()` raises a Pydantic validation or settings error, doctor prints an **Environment Results** table with:

- Field
- Error Type
- Location
- Message
- Value

Sensitive field names containing `key`, `token`, `secret`, or `password` are redacted.

Runtime checks do not run in this mode.

### Runtime-results mode

With valid settings, doctor checks in this order:

1. Python version
2. `.env` file
3. local vault
4. inbox folder
5. main notes folder
6. state folder
7. prompt file
8. API key
9. Anki
10. Anki deck

The deck row is marked failed and skipped when Anki is unreachable.

### Side effects

Doctor is read-oriented but not offline. It:

- reads settings and prompt;
- inspects files/folders;
- contacts Gemini;
- contacts AnkiConnect;
- writes logs.

It does not construct `StateManager`, so it does not create the state folder or `state.json`.

### Prompt-loading caveat

After settings pass, `Doctor` creates `AI()` before `RuntimeChecker` runs. `AI()` immediately reads `PROMPT_FILE`. A missing or unreadable prompt can therefore raise before the runtime table shows the planned prompt row.

### Exit-status caveat

Failed environment or runtime rows do not currently produce a non-zero exit code. A completed `Doctor.run()` returns `None`, which means status `0`.

Unexpected exceptions also occur before the normal handler `try/except` and may escape directly.

See [Diagnostics](diagnostics.md).

## `stats`

Display current counts.

### Syntax

```bash
obsidian2anki stats
obsidian2anki --verbose stats
```

### Intended rows

- notes in `INBOX_FOLDER`;
- notes in `MAIN_NOTES_FOLDER`;
- processed state entries;
- unprocessed main-folder files;
- generated Anki notes in `DECK_NAME`.

### Scan behavior

Folder counts and unprocessed detection inspect only immediate files and do not restrict suffixes to `.md`.

The generated count comes from:

```text
findNotes query="deck:<DECK_NAME>"
```

### Current defect

With a non-empty state, `_processed_notes()` iterates `(id, StateNote)` pairs but logs `processed_note[1].title`. `StateNote` is not subscriptable. Because the argument expression is evaluated before logging-level filtering, this defect can occur even when debug output is not shown.

Until fixed, `stats` may fail for a non-empty state.

## Dry-Run Matrix

| Command | Parser accepts `--dry-run` | Evaluates eligibility | External mutation prevented | Startup side effects still possible |
| --- | :---: | :---: | :---: | :---: |
| `process` | Yes | No; returns before tag filtering | Yes | Yes |
| `migrate` | Yes | Yes | Yes | Yes |
| `format-notes` | Yes | Yes, immediate files | Yes | Yes |
| `clear` | Yes | Reads state count only | Yes | Yes |
| `delete-card` | No | — | — | Yes |
| `delete-note` | No | — | — | Yes |
| `doctor` | No | Diagnostic command | No data mutation intended | Uses separate startup |
| `stats` | No | Read command | No data mutation intended | Yes |

Normal dry-run commands still construct the complete application. That may create state storage, read the prompt, parse state JSON, and initialize clients.

## Logging and Terminal Output

### File logging

Every command calls `setup_logger()` after argument parsing.

```text
logs/obsidian2anki.log
```

Format:

```text
timestamp | level | logger name | message
```

Rotation:

- 5 MiB per file;
- three backups;
- UTF-8.

### Console logging

Most commands use Rich logging. `doctor` and `stats` are in `IGNORE_CONSOLE` and print their tables directly instead.

### Verbose mode

```bash
obsidian2anki --verbose migrate --dry-run
```

Useful debug information includes migration candidate names, note details, and transport diagnostics.

### Repeated in-process invocation

`setup_logger()` returns when the root logger already has handlers. Tests or embedded callers that run `main()` repeatedly must reset logging explicitly to change configuration between calls.

## Exit Statuses

Implemented top-level statuses:

| Situation | Status |
| --- | :---: |
| Normal handler returns | `0` |
| `KeyboardInterrupt` inside normal handler call | `130` |
| Exception inside normal handler call | `1` |

Important exceptions:

- `build_app()` runs before the normal `try`, so startup failures can escape instead of returning `1`.
- doctor runs before the normal `try`.
- services often catch failures internally and return/log without propagating them.
- doctor failed rows still return `0`.

Do not treat a zero status as proof that every note or diagnostic passed in this version.

## Shell Completion

`build_arg_parser()` calls:

```python
argcomplete.autocomplete(arg_parser.parser)
```

The `argcomplete` package is installed as a runtime dependency. Shell-level activation is still required for completion to appear.

## Recommended Sequences

### First setup

```bash
obsidian2anki doctor
obsidian2anki --verbose process --dry-run
obsidian2anki process
```

### Existing formatted vault

```bash
obsidian2anki --verbose migrate --dry-run
obsidian2anki migrate
```

### Legacy conversion

```bash
obsidian2anki format-notes --dry-run
# Back up the folder and inspect the legacy first-line format.
obsidian2anki format-notes
obsidian2anki migrate --dry-run
obsidian2anki migrate
```

### Bulk rebuild

```bash
obsidian2anki clear --dry-run
obsidian2anki clear
obsidian2anki migrate --dry-run
obsidian2anki migrate
```

This rebuild sequence is not transactional. Preserve backups.

## Troubleshooting

### `obsidian2anki: command not found`

Activate the intended virtual environment and reinstall:

```bash
python -m pip install -e .
```

### `unrecognized arguments: --verbose`

Move it before the command:

```bash
obsidian2anki --verbose process
```

### `unrecognized arguments: --dry-run`

Place it after a supported command:

```bash
obsidian2anki migrate --dry-run
```

Delete commands, doctor, and stats do not support it.

### Help or version fails

`--version` depends on installed package metadata. Run through the environment where the editable package is installed.

### Doctor shows environment errors

Correct the named `.env` fields. Secret-like values are intentionally hidden.

### Doctor crashes before runtime results

Verify `PROMPT_FILE`. AI construction reads the prompt before runtime checks execute.

### Anki cannot be reached

Open Anki, verify AnkiConnect and `ANKI_URL`, then rerun doctor. Normal `connect()` operations may try to launch an `anki` executable found on `PATH`.

### State JSON is malformed

Back up the file before editing. Normal commands load it during application construction and currently have no recovery path.

### `stats` fails with a `StateNote` error

This is the known `_processed_notes()` indexing defect. Inspect state and Anki through other means until the method is fixed.

### A command logs failures but exits `0`

This is current behavior for several caught note/service failures and all failed diagnostic rows. Inspect logs and Rich output.
