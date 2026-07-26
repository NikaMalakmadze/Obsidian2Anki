# CLI Reference

This guide documents the command-line interface for **Obsidian2Anki 0.1.0**. It explains global options, every available subcommand, argument validation, dry-run behavior, logging, exit statuses, command side effects, and current implementation constraints.

For initial setup, see [Installation](installation.md). For environment variables, see [Configuration](configuration.md). For the complete note lifecycle, see [Workflow](workflow.md). For internal command dispatch and dependency wiring, see [Architecture](architecture.md).

> [!CAUTION]
> Several commands modify multiple systems in one run. Depending on the command, Obsidian2Anki can generate or delete Anki notes, rewrite YAML frontmatter, move Markdown files, and update or clear `state.json`. Back up the Obsidian vault and Anki collection before the first real run and before destructive bulk operations.

## Contents

- [Command Structure](#command-structure)
- [Entry Point](#entry-point)
- [Startup Requirements](#startup-requirements)
- [Global Help](#global-help)
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
- [Dry-Run Behavior](#dry-run-behavior)
- [Verbose Output and Logging](#verbose-output-and-logging)
- [Terminal Output](#terminal-output)
- [Argument Validation](#argument-validation)
- [Exit Statuses](#exit-statuses)
- [Shell Completion](#shell-completion)
- [Recommended Command Sequences](#recommended-command-sequences)
- [Common CLI Mistakes](#common-cli-mistakes)
- [Troubleshooting](#troubleshooting)
- [Current CLI Constraints](#current-cli-constraints)

## Command Structure

The general command format is:

```text
obsidian2anki [GLOBAL_OPTIONS] COMMAND [COMMAND_OPTIONS] [ARGUMENTS]
```

Examples:

```bash
obsidian2anki process
obsidian2anki --verbose migrate --dry-run
obsidian2anki delete-card 1712345678901
obsidian2anki delete-note 9fb66ee5-6778-4bf4-817d-f82646d1237e
```

The position of each option matters:

- root options such as `--verbose` must appear **before** the command;
- command-specific options such as `--dry-run` must appear **after** the command;
- positional arguments such as `card_id` and `note_id` follow their command.

Correct:

```bash
obsidian2anki --verbose process --dry-run
```

Incorrect:

```bash
obsidian2anki process --verbose
obsidian2anki --dry-run process
```

The first incorrect command places a root option after the subcommand. The second places a subcommand-only option before the subcommand.

## Entry Point

The package exposes this console script through `pyproject.toml`:

```toml
[project.scripts]
obsidian2anki = "obsidian2anki.main:main"
```

After an editable installation:

```bash
python -m pip install -e .
```

the command should be available in the active virtual environment:

```bash
obsidian2anki --version
```

Expected output for the current project version:

```text
obsidian2anki 0.1.0
```

The console script calls `obsidian2anki.main:main`, which performs these high-level steps:

1. build the argparse parser;
2. register argcomplete integration;
3. parse the command line;
4. configure file and optional console logging;
5. construct the application and all dependencies;
6. map the selected command to an application method;
7. execute the method;
8. translate exceptions and keyboard interruption raised during the selected handler into process exit statuses.

## Startup Requirements

The CLI imports the application modules before parsing the command. Several modules load `Settings` at import time, so all required configuration variables must be valid even for commands such as:

```bash
obsidian2anki --help
obsidian2anki --version
```

At minimum, the Pydantic settings model must be able to resolve every required variable from the repository-root `.env` file or the process environment.

The current settings model requires:

```text
STATE_FOLDER
API_KEY
PROMPT_FILE
INCLUDE_TAGS
EXCLUDE_TAGS
ANKI_URL
DECK_NAME
LOCAL_VAULT
INBOX_FOLDER
MAIN_NOTES_FOLDER
MAX_RETRIES_ON_ANKI_DUPLICATE_CARD
```

After argument parsing, normal subcommands construct every dependency, not only the components directly needed by the selected operation. During that construction:

- the vault and Anki managers are initialized;
- the updated `StateManager` creates `STATE_FOLDER` and `state.json` when missing, then loads the state file;
- the AI component reads the configured prompt file;
- the Gemini client is created.

Consequently, a malformed state file or unreadable prompt can prevent a command from reaching its own handler.

> [!NOTE]
> `--help` and `--version` cause argparse to exit during parsing, before the application dependency container is instantiated. They still require import-time settings validation, but they do not normally construct the AI client or initialize runtime state.

## Global Help

Run:

```bash
obsidian2anki --help
```

The parser exposes this command surface:

```text
usage: obsidian2anki [-h] [-v] [--version]
                     {migrate,process,clear,format-notes,doctor,stats,delete-card,delete-note}
                     ...

Sync Obsidian notes into Anki flashcards.
```

Available root options:

```text
-h, --help     show help and exit
-v, --verbose  increase output verbosity
--version      show the installed package version and exit
```

Use command-specific help for syntax and arguments:

```bash
obsidian2anki process --help
obsidian2anki migrate --help
obsidian2anki delete-card --help
```

## Global Options

### `-h`, `--help`

Display root or subcommand help and exit without running the selected workflow.

Root help:

```bash
obsidian2anki --help
```

Subcommand help:

```bash
obsidian2anki clear --help
```

Argparse exits with status `0` after displaying requested help.

### `--version`

Display the version installed in Python package metadata:

```bash
obsidian2anki --version
```

The value comes from:

```python
importlib.metadata.version("obsidian2anki")
```

For the current package:

```text
obsidian2anki 0.1.0
```

`--version` is a root option and should be used without a subcommand.

### `-v`, `--verbose`

Change the logging level from `INFO` to `DEBUG`:

```bash
obsidian2anki --verbose process
obsidian2anki -v migrate --dry-run
```

The option must precede the subcommand:

```bash
# Correct
obsidian2anki --verbose stats

# Incorrect
obsidian2anki stats --verbose
```

Verbose mode can reveal:

- note names discovered by migration or formatting previews;
- folder note names collected by statistics;
- Anki connectivity attempts;
- additional processing and diagnostic details;
- full debug-level entries in `logs/obsidian2anki.log`.

It does not change processing logic or enable a dry run.

## Command Summary

| Command                 | Primary purpose                                                                    | Modifies vault | Modifies Anki | Modifies state | Supports `--dry-run` |
| ----------------------- | ---------------------------------------------------------------------------------- | :------------: | :-----------: | :------------: | :------------------: |
| `process`               | Process eligible notes from the inbox.                                             |      Yes       |      Yes      |      Yes       |         Yes          |
| `migrate`               | Process new or changed notes in the main folder.                                   |      Yes       |      Yes      |      Yes       |         Yes          |
| `format-notes`          | Add required YAML structure to legacy notes.                                       |      Yes       |      No       |       No       |         Yes          |
| `clear`                 | Delete all generated Anki notes tracked in state and clear managed metadata/state. |      Yes       |      Yes      |      Yes       |         Yes          |
| `delete-card <card_id>` | Delete one tracked generated Anki note.                                            |      Yes       |      Yes      |      Yes       |          No          |
| `delete-note <note_id>` | Delete all generated Anki notes linked to one tracked vault note.                  |      Yes       |      Yes      |      Yes       |          No          |
| `doctor`                | Display environment and dependency checks.                                         |      No¹       |      No¹      |      No¹       |          No          |
| `stats`                 | Display vault, state, and Anki counts.                                             |      No¹       |      No¹      |      No¹       |          No          |

¹ Application startup still creates the log directory and log file. With the updated state initialization, dependency construction may also create the configured state directory and an empty `state.json`. Anki-related reads can attempt to launch Anki when it is not already running.

## `process`

Process notes from the configured inbox folder.

### Syntax

```bash
obsidian2anki process [--dry-run]
```

Verbose forms:

```bash
obsidian2anki --verbose process
obsidian2anki --verbose process --dry-run
```

### Source folder

The command reads immediate files from:

```text
<LOCAL_VAULT>/<INBOX_FOLDER>
```

With the example configuration:

```text
/path/to/MyVault/00_Inbox
```

Folder traversal is not recursive. Every immediate regular file is passed to the frontmatter reader; the current implementation does not restrict discovery to `.md` files.

### Eligibility

Each note must:

- contain a readable `id` field;
- expose `tags` as a YAML list for tag filtering;
- contain no tag listed in `EXCLUDE_TAGS`;
- contain at least one tag listed in `INCLUDE_TAGS`, unless `INCLUDE_TAGS` is empty.

Excluded tags always take priority.

A note that fails tag filtering remains unchanged in the inbox.

### Real-run behavior

For each eligible inbox note, `process` calls the single-note workflow:

1. skip card generation when normalized content is empty;
2. when `anki_cards` metadata exists, try to delete the previously linked Anki notes first;
3. send the note to Gemini and validate the structured flashcard batch;
4. add the generated notes to the configured Anki deck;
5. regenerate and retry when Anki insertion returns no IDs;
6. write the returned IDs to `anki_cards` frontmatter;
7. move the source file from the inbox to `MAIN_NOTES_FOLDER`;
8. queue title, path, hash, card IDs, count, and timestamps for state;
9. save state when the command finishes, including when the service exits through an exception.

Example:

```bash
obsidian2anki process
```

### Failure behavior

`ProcessingService` does not stop after `process_note()` returns `False`; it continues to later eligible notes. Individual note errors are logged inside `NoteProcessor` and converted to a `False` result.

Because those per-note failures are handled internally, the top-level CLI can still return exit status `0` even when one or more notes fail. Review terminal output and the log file rather than relying only on the shell status.

### Dry run

```bash
obsidian2anki process --dry-run
```

The current preview:

- reads all immediate inbox files;
- reports the number of files found;
- does not enter the tag-filtering or single-note processing loop;
- does not call Gemini;
- does not add or delete Anki notes;
- does not write metadata;
- does not move files;
- does not add new state entries.

It is therefore a folder-level preview, not a complete per-note eligibility plan.

## `migrate`

Synchronize existing notes from the configured main notes folder.

### Syntax

```bash
obsidian2anki migrate [--dry-run]
```

Verbose forms:

```bash
obsidian2anki --verbose migrate
obsidian2anki --verbose migrate --dry-run
```

### Source folder

The command reads immediate files from:

```text
<LOCAL_VAULT>/<MAIN_NOTES_FOLDER>
```

### Eligibility and change detection

A note is selected only when both conditions are true:

1. it passes include/exclude tag filtering;
2. it needs processing.

A note needs processing when:

- its frontmatter `id` is not present in state; or
- its normalized content hash differs from the stored SHA-256 hash; or
- its filename-derived title differs from the stored title.

The hash is based on normalized note content, not raw Markdown bytes or tags.

### Real-run behavior

For every selected note, migration uses the same single-note workflow as `process`. Existing `anki_cards` are deleted before replacement generation, then successful IDs are written back and state is updated.

```bash
obsidian2anki migrate
```

Migration saves pending state in a `finally` block.

### Failure behavior

Unlike inbox processing, migration stops its loop after the first selected note for which `process_note()` returns `False`:

```text
selected note fails -> migration loop stops -> pending state is saved
```

The failure is still normally handled inside `NoteProcessor`, so the CLI may return status `0`. Check logs to verify that all selected notes completed.

### Dry run

```bash
obsidian2anki migrate --dry-run
```

The migration preview:

- reads main-folder notes;
- applies tag filtering;
- checks state and content/title changes;
- reports how many notes require processing;
- lists selected note titles at debug level when `--verbose` is enabled;
- avoids Gemini, Anki, vault writes, and new state entries.

For the most useful preview:

```bash
obsidian2anki --verbose migrate --dry-run
```

## `format-notes`

Convert legacy files in the main notes folder to the YAML structure required by Obsidian2Anki.

### Syntax

```bash
obsidian2anki format-notes [--dry-run]
```

Recommended preview:

```bash
obsidian2anki --verbose format-notes --dry-run
```

### Intended input

The formatter assumes a legacy note whose first line contains whitespace-separated Obsidian tags:

```markdown
#python #functions

# Python Functions

Content...
```

It removes the first line and rewrites the file as:

```yaml
---
id: <generated UUID>
tags:
  - python
  - functions
---
```

followed by the remaining lines.

### Preview behavior

The dry run:

- examines immediate files in `MAIN_NOTES_FOLDER`;
- classifies a file as legacy when parsed frontmatter contains fewer than two metadata keys;
- reports the legacy count and the current implementation's total directory-entry count;
- lists legacy filenames in verbose mode;
- does not write any note.

```bash
obsidian2anki --verbose format-notes --dry-run
```

### Real-run warning

> [!WARNING]
> The current real-run loop calls `ensure_note_format()` for **every immediate file** in the main notes folder, not only the files classified as legacy during the preview. Running it against already formatted notes can prepend new frontmatter, regenerate IDs, reinterpret the first line as tags, and damage existing metadata.

Back up the vault first. Until the loop is corrected, use this command only on a folder known to contain exclusively compatible legacy files.

```bash
obsidian2anki format-notes
```

The command does not update Anki or `state.json` directly, but changing note IDs can make existing state and Anki relationships inconsistent.

## `clear`

Delete all application-managed Anki notes referenced by state, remove `anki_cards` metadata from the corresponding vault files, and clear local state.

### Syntax

```bash
obsidian2anki clear [--dry-run]
```

Preview first:

```bash
obsidian2anki clear --dry-run
```

### Real-run behavior

For every state entry, `clear`:

1. marks the entry's generated ID list empty in state;
2. saves that state change;
3. removes the `anki_cards` property from the stored vault path;
4. calls Anki deletion for each stored generated ID;
5. logs the source note ID;
6. after all entries, replaces state with an empty object and saves it.

The Markdown note files and their content are not intentionally deleted. Their managed `anki_cards` metadata is removed.

Run:

```bash
obsidian2anki clear
```

### Safety considerations

> [!CAUTION]
> This command is destructive and has no confirmation prompt. `--dry-run` is the only built-in preview.

The operation spans state, vault files, and Anki without a transaction. If an Anki request fails, the connector can log the failure and return without raising, while later vault/state cleanup may continue. Backups are important.

### Dry run

```bash
obsidian2anki clear --dry-run
```

The current preview:

- reads state;
- reports how many source notes are tracked;
- does not enumerate their IDs;
- does not contact the per-note deletion workflow;
- does not modify vault metadata, Anki, or state.

## `delete-card`

Delete one generated Anki note ID and remove that ID from its source note metadata and state entry.

The project names the argument `card_id`, but AnkiConnect's `addNotes` and `deleteNotes` actions use the returned value as an **Anki note ID**.

### Syntax

```bash
obsidian2anki delete-card CARD_ID
```

Example:

```bash
obsidian2anki delete-card 1712345678901
```

### Argument type

`CARD_ID` is parsed as an integer by argparse. A non-integer is rejected before command execution:

```bash
obsidian2anki delete-card abc
```

Typical result:

```text
error: argument card_id: invalid int value: 'abc'
```

Argparse exits with status `2` for this parsing error.

### Real-run behavior

The command:

1. searches every state entry for the supplied generated ID;
2. removes it from the matching state's `anki_note_ids` list;
3. saves state;
4. sends `deleteNotes` to AnkiConnect;
5. removes the ID from the source note's `anki_cards` metadata;
6. deletes the complete state entry when no generated IDs remain.

If the ID is not found in state, the service logs a warning and returns without contacting Anki or changing the vault.

### No dry-run support

This command does not accept `--dry-run`:

```bash
# Invalid
obsidian2anki delete-card 1712345678901 --dry-run
```

Confirm the ID manually before execution.

### Exit-status caveat

A missing ID is logged and treated as a normal service return, so the command normally exits with status `0` even though nothing was deleted.

## `delete-note`

Delete all generated Anki notes associated with one tracked Obsidian note ID, remove the note's `anki_cards` metadata, and remove its state entry.

The source Markdown file itself is not deleted.

### Syntax

```bash
obsidian2anki delete-note NOTE_ID
```

Example:

```bash
obsidian2anki delete-note 9fb66ee5-6778-4bf4-817d-f82646d1237e
```

`NOTE_ID` is parsed as a string. The CLI does not validate UUID syntax; it uses the exact string as the state key.

### Real-run behavior

For a tracked note, the command:

1. obtains the source file path from state;
2. obtains every generated Anki ID from state;
3. deletes each generated Anki note;
4. removes `anki_cards` from the source file;
5. removes the complete state entry and saves state.

### Missing-state warning

> [!WARNING]
> The current implementation logs that an unknown note ID is absent but does not return immediately. It then attempts to construct a path and iterate IDs from missing values, which can raise an exception. The top-level CLI catches that exception and exits with status `1`.

Verify the ID in `state.json` before running the command.

### No dry-run support

This command has no preview option:

```bash
# Invalid
obsidian2anki delete-note NOTE_ID --dry-run
```

## `doctor`

Run environment and integration diagnostics and display a Rich table.

### Syntax

```bash
obsidian2anki doctor
```

Verbose logging:

```bash
obsidian2anki --verbose doctor
```

### Checks

The table contains these checks:

| Check             | What it verifies                                               |
| ----------------- | -------------------------------------------------------------- |
| Python Version    | The interpreter is Python 3.12 or newer.                       |
| `.env` File       | A repository-root `.env` file exists.                          |
| Local Vault       | `LOCAL_VAULT` exists and is a directory.                       |
| Inbox Folder      | `<LOCAL_VAULT>/<INBOX_FOLDER>` exists and is a directory.      |
| Main Notes Folder | `<LOCAL_VAULT>/<MAIN_NOTES_FOLDER>` exists and is a directory. |
| State Folder      | `<repository-root>/<STATE_FOLDER>` exists and is a directory.  |
| API key           | Gemini accepts the configured API key.                         |
| Prompt File       | `<repository-root>/<PROMPT_FILE>` exists as a file.            |
| Anki Deck         | `DECK_NAME` appears in Anki's deck list.                       |
| Anki              | AnkiConnect responds at `ANKI_URL`.                            |

Example table shape:

```text
╭─────┬───────────────────┬────────────────────────────────────╮
│     │ Check             │ Result                             │
├─────┼───────────────────┼────────────────────────────────────┤
│ ✅  │ Python Version    │ Python 3.13.x is supported.        │
│ ✅  │ .env File         │ .env file found at ...             │
│ ... │ ...               │ ...                                │
╰─────┴───────────────────┴────────────────────────────────────╯
```

### Side effects and network access

`doctor` does not intentionally alter vault notes, generated Anki notes, or existing state data. It does, however:

- initialize logging;
- construct all application dependencies;
- create the state folder/file when missing under the updated `StateManager`;
- read and parse the state file;
- read the prompt during AI initialization;
- send a Gemini API request to validate the key;
- query AnkiConnect for decks and status;
- potentially try to launch the `anki` executable because the deck check uses the normal Anki connector.

It is therefore a diagnostic command, but not an offline command.

### Startup limitation

Some conditions can prevent the table from appearing at all:

- missing required Pydantic settings;
- malformed JSON in `state.json`;
- an unreadable or missing prompt file during AI construction;
- other dependency-construction errors.

This happens because dependencies are constructed before `Doctor.run()` performs its checks.

### Exit-status caveat

Failed diagnostic rows are logged as an error, but `Doctor.run()` does not raise or return a failure code. When the table is produced successfully, the CLI normally exits with status `0` even if one or more checks show ❌.

Use the table contents—not only `$?` or `%ERRORLEVEL%`—to determine environment health.

## `stats`

Display summary counts from the vault, local state, and Anki.

### Syntax

```bash
obsidian2anki stats
```

Verbose logging:

```bash
obsidian2anki --verbose stats
```

### Intended statistics

The Rich table is designed to report:

| Statistic             | Source                                                         |
| --------------------- | -------------------------------------------------------------- |
| Notes in inbox folder | Immediate files in `INBOX_FOLDER`.                             |
| Notes in main folder  | Immediate files in `MAIN_NOTES_FOLDER`.                        |
| Processed notes       | Number of entries in local state.                              |
| Unprocessed notes     | Main-folder files whose absolute paths are not found in state. |
| Generated cards       | Anki note IDs returned by `findNotes` for `DECK_NAME`.         |

The "Generated Cards" label counts Anki notes, because the implementation uses AnkiConnect's `findNotes` action.

### Read behavior

The command reads:

- the immediate contents of both configured vault folders;
- all state entries;
- Anki notes in the configured deck.

It writes only logs and normal runtime initialization files. Anki lookup can attempt to launch Anki when unavailable.

### Current implementation defect

> [!WARNING]
> In the current source, `_processed_notes()` iterates `(id, StateNote)` pairs but then evaluates `processed_note[1].title`. `processed_note` is already a `StateNote`, so indexing it can raise `TypeError` whenever state contains at least one entry. In that situation, the top-level CLI logs an unhandled error and exits with status `1` before displaying the table.

Until corrected, `stats` is reliable only when state is empty or the bug is fixed. The intended debug statement should access:

```python
processed_note.title
```

rather than:

```python
processed_note[1].title
```

## Dry-Run Behavior

Dry run is implemented only for command definitions that declare `supports_dry_run=True`.

### Supported commands

```bash
obsidian2anki process --dry-run
obsidian2anki migrate --dry-run
obsidian2anki format-notes --dry-run
obsidian2anki clear --dry-run
```

### Unsupported commands

```text
delete-card
delete-note
doctor
stats
```

Passing `--dry-run` to an unsupported command produces an argparse error and exit status `2`.

### Comparison matrix

| Command        | What the preview calculates                                                                     | What the preview does not do                                                   |
| -------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------ |
| `process`      | Counts immediate inbox files.                                                                   | Does not determine or list eligible notes; does not call the per-note loop.    |
| `migrate`      | Filters tags, checks state/title/hash, counts selected notes, and lists titles in verbose mode. | Does not generate, delete, insert, move, write metadata, or add state entries. |
| `format-notes` | Detects and counts legacy files; lists them in verbose mode.                                    | Does not rewrite files.                                                        |
| `clear`        | Counts state entries.                                                                           | Does not list entries or modify Anki, vault metadata, or state.                |

### Runtime initialization still occurs

`--dry-run` prevents the selected service's main writes, but it is not a zero-side-effect process sandbox. Before the service executes, the application still:

- validates settings;
- configures logging and can create `logs/obsidian2anki.log`;
- constructs every dependency;
- creates the configured state directory and file when missing;
- reads state JSON;
- reads the prompt and creates the Gemini client.

No Gemini generation request is made by the four dry-run service paths.

## Verbose Output and Logging

### Default logging

Without `--verbose`, the root logger uses `INFO`:

```bash
obsidian2anki process
```

### Debug logging

With `--verbose`, it uses `DEBUG`:

```bash
obsidian2anki --verbose process
```

### File location

Every executed command configures a rotating log file at:

```text
<repository-root>/logs/obsidian2anki.log
```

The log directory is created automatically.

### Rotation

The current handler uses:

```text
maximum active file size: 5 MiB
backup count: 3
encoding: UTF-8
```

File entries use this format:

```text
TIMESTAMP | LEVEL    | LOGGER_NAME | MESSAGE
```

### Console logging

Most commands add a Rich logging handler to the terminal.

Console logging is intentionally disabled for:

```text
doctor
stats
```

Those commands print their own Rich tables through `Console.print()` while regular logs continue to go to the file.

### Repeated in-process calls

`setup_logger()` returns immediately when the root logger already has handlers. This is normally irrelevant for the installed one-command-per-process workflow, but tests or code that invokes `main()` multiple times in the same interpreter may retain the first call's level and console-handler choice.

## Terminal Output

Obsidian2Anki uses two output styles.

### Rich log output

Commands such as `process`, `migrate`, `clear`, `format-notes`, and deletion commands emit formatted logging to the terminal when console logging is enabled.

Typical messages include:

```text
Found 3 notes in '00_Inbox'.
Generated 4 flash cards for note with id: '...'.
Processed note with id: '...'.
Finished processing notes.
```

### Rich tables

`doctor` and `stats` print tables directly. Their normal logger console handler is disabled to avoid mixing log lines with table output.

### Standard streams

Argparse help and parsing errors use argparse's standard output/error behavior. The application does not currently provide machine-readable JSON output, quiet mode, or color-disable flags.

## Argument Validation

### Required subcommand

The parser requires one subcommand:

```bash
obsidian2anki
```

Without a command, argparse reports that `command` is required and exits with status `2`.

### `card_id`

`delete-card` uses `int` as its argparse conversion function:

```bash
obsidian2anki delete-card 1712345678901
```

Negative and zero values are syntactically accepted because there is no range validator, although they are unlikely to match state.

### `note_id`

`delete-note` uses plain string conversion:

```bash
obsidian2anki delete-note any-string
```

No UUID validator, length check, or state-existence check is performed by argparse.

### Option placement

Root options are not automatically inherited by subparsers. Use:

```bash
obsidian2anki --verbose migrate --dry-run
```

not:

```bash
obsidian2anki migrate --verbose --dry-run
```

### Extra arguments

Unexpected options or positional values produce an argparse error and status `2`.

## Exit Statuses

The top-level `main()` explicitly returns these statuses:

| Status | Meaning in the current CLI                                                                                                                 |
| :----: | ------------------------------------------------------------------------------------------------------------------------------------------ |
|  `0`   | Command returned without an uncaught exception; also used for help and version.                                                            |
|  `1`   | The selected handler raised an exception caught by the command boundary, or Python terminated because startup failed before that boundary. |
|  `2`   | Argparse rejected the command line or a typed argument.                                                                                    |
| `130`  | A `KeyboardInterrupt` was caught during command execution.                                                                                 |

### Important interpretation

Status `0` means the Python command handler returned; it does **not** always mean the requested domain operation fully succeeded.

Examples that can still end with `0`:

- `process_note()` catches an exception, logs it, and returns `False`;
- migration stops after a handled note failure;
- inbox processing continues after handled note failures;
- `delete-card` cannot find the supplied ID in state;
- `doctor` displays failed checks;
- an Anki connector call logs a request failure and returns `None` without raising to the top level.

For automation, inspect logs and verify resulting state/vault/Anki data rather than depending only on the process status.

### Keyboard interruption

Pressing `Ctrl+C` while the selected handler is executing is caught by the top-level boundary:

```text
Interrupted by user. Exiting.
```

The CLI returns `130`.

Service `finally` blocks still run while exceptions propagate. In particular, `process` and `migrate` call `state.save()` in `finally`, so already prepared state can be persisted during interruption.

## Shell Completion

The CLI calls:

```python
argcomplete.autocomplete(parser)
```

and declares `argcomplete` as a dependency. This provides the parser hook needed for shell completion when argcomplete has been activated for the shell and command.

Without shell registration, the CLI continues to work normally; pressing Tab simply will not use argcomplete's dynamic suggestions.

Completion candidates are derived from the argparse structure, including:

- subcommand names;
- global options;
- `--dry-run` on supported subcommands;
- help flags.

## Recommended Command Sequences

### First configuration check

Open Anki, then run:

```bash
obsidian2anki doctor
```

Read every table row. Do not treat status `0` as proof that every check passed.

### Preview and process the inbox

```bash
obsidian2anki process --dry-run
obsidian2anki process
```

The preview only confirms inbox discovery. For exact eligibility, inspect note tags and configuration before the real command.

### Preview and migrate existing notes

```bash
obsidian2anki --verbose migrate --dry-run
obsidian2anki migrate
```

Verbose migration preview is the most informative dry run because it lists selected note titles.

### Format a legacy-only folder

```bash
obsidian2anki --verbose format-notes --dry-run
```

Review the detected files, back up the vault, confirm the main folder contains only compatible legacy notes, then:

```bash
obsidian2anki format-notes
```

Because of the current all-files formatting defect, do not run the real command on a mixed or already formatted folder.

### Delete one generated item

Find the generated Anki note ID in the source note's `anki_cards` metadata or state, then:

```bash
obsidian2anki delete-card 1712345678901
```

Verify both Anki and the source frontmatter afterward.

### Delete all generated items for one source note

Confirm that the exact source `id` exists in state:

```bash
obsidian2anki delete-note 9fb66ee5-6778-4bf4-817d-f82646d1237e
```

### Clear all managed data

```bash
obsidian2anki clear --dry-run
```

Back up the vault and Anki collection, then:

```bash
obsidian2anki clear
```

## Common CLI Mistakes

### Placing `--verbose` after the command

Incorrect:

```bash
obsidian2anki process --verbose
```

Correct:

```bash
obsidian2anki --verbose process
```

### Placing `--dry-run` before the command

Incorrect:

```bash
obsidian2anki --dry-run migrate
```

Correct:

```bash
obsidian2anki migrate --dry-run
```

### Expecting dry run on deletion commands

Invalid:

```bash
obsidian2anki delete-card 123 --dry-run
obsidian2anki delete-note UUID --dry-run
```

Neither deletion command currently supports a preview.

### Assuming `process --dry-run` lists eligible notes

It only reads and counts inbox files before returning. It does not apply tag filtering in the preview path.

### Assuming `doctor` is fully offline

It validates the Gemini API key and queries Anki. It can also attempt to start Anki.

### Assuming a green shell status means successful diagnostics

`doctor` can display failed rows and still exit `0`.

### Using an Anki card number instead of the stored note ID

The `anki_cards` name is historical. The generated IDs originate from AnkiConnect `addNotes` and are passed to `deleteNotes`, so use the IDs stored by Obsidian2Anki rather than a browser card ID from another Anki API context.

### Running `format-notes` on formatted notes

The current write loop touches all files in the folder. Always preview and back up first.

## Troubleshooting

### `obsidian2anki: command not found`

Activate the virtual environment and install the project:

```bash
python -m pip install -e .
```

Then verify:

```bash
obsidian2anki --version
```

On Windows, ensure the active environment's `Scripts` directory is on the current shell path through activation.

### Help or version fails with a settings validation error

The CLI imports modules that instantiate cached settings before parsing. Create a complete repository-root `.env` file or provide every required variable through the environment.

See [Configuration](configuration.md).

### A normal command fails before logging its start message

Dependency construction occurs before dispatch. Check:

- `.env` parsing and required values;
- `PROMPT_FILE` existence and permissions;
- `STATE_FOLDER/state.json` JSON validity;
- vault path validity;
- package dependency installation.

### `unrecognized arguments: --verbose`

Move the option before the command:

```bash
obsidian2anki --verbose process
```

### `unrecognized arguments: --dry-run`

The selected command may not support dry run, or the option may be in the wrong position.

Supported pattern:

```bash
obsidian2anki migrate --dry-run
```

### `argument card_id: invalid int value`

Supply the numeric generated ID stored in `anki_cards` or state:

```bash
obsidian2anki delete-card 1712345678901
```

### `delete-note` exits with status `1` for an unknown ID

The current service does not return after detecting a missing state key. Confirm the exact ID in `state.json` before retrying.

### `stats` crashes with a `StateNote` indexing error

The current `_processed_notes()` implementation indexes a `StateNote` as though it were a tuple. Change:

```python
processed_note[1].title
```

to:

```python
processed_note.title
```

### The terminal reports an error but the command exits `0`

Some lower layers catch and log failures instead of raising. Inspect:

```text
logs/obsidian2anki.log
```

Then verify the source note's frontmatter, state entry, and Anki notes.

### Anki cannot be reached

Open Anki manually, confirm AnkiConnect is installed, and verify:

```env
ANKI_URL=http://localhost:8765/
```

Use:

```bash
obsidian2anki doctor
```

but remember that dependency construction and deck lookup can occur before all diagnostics are presented.

### State JSON is empty

An empty `state.json` is valid and loads as an empty state object.

### State JSON is malformed

Malformed JSON raises during `StateManager` construction and prevents command dispatch. Restore a valid backup or replace the file with an empty JSON object when intentionally resetting only local state:

```json
{}
```

Do not reset state casually when vault notes still contain `anki_cards`, because the cross-system links will become inconsistent.

## Current CLI Constraints

The current command-line implementation has these notable limitations:

1. **Import-time settings loading** — complete valid settings can be required before root help or version is displayed.
2. **Eager dependency construction** — every normal command constructs vault, Anki, state, AI, processor, and all services.
3. **No confirmation prompts** — destructive commands execute immediately.
4. **No dry run for targeted deletions** — `delete-card` and `delete-note` cannot preview changes.
5. **Inconsistent success signaling** — several handled operational failures still produce exit status `0`.
6. **Doctor failure rows do not affect exit status** — diagnostics must be read from the table.
7. **Doctor cannot diagnose every startup failure** — prompt and state loading occur before its checks run.
8. **`process --dry-run` is shallow** — it counts inbox files but does not determine eligibility.
9. **`clear --dry-run` is shallow** — it reports only the number of state entries.
10. **Flat-folder discovery** — note commands inspect only immediate files and do not recurse.
11. **No extension filter** — non-Markdown files in configured note folders can reach frontmatter parsing.
12. **Formatter write-loop defect** — real `format-notes` reformats every immediate file rather than only detected legacy files.
13. **Unknown `delete-note` defect** — a missing state key can lead to a top-level exception.
14. **Formatter count defect** — the reported total includes every immediate directory entry, not only regular files.
15. **Current `stats` defect** — non-empty state can trigger invalid `StateNote` indexing.
16. **Terminology mismatch** — `card_id`, `anki_cards`, and "Generated Cards" represent Anki note IDs in the current AnkiConnect calls.
17. **No structured output** — commands do not provide JSON, CSV, quiet, or no-color modes.
18. **No transaction boundary** — vault, Anki, and state changes can partially succeed.
19. **No reconciliation command** — the CLI cannot automatically repair disagreement between vault metadata, state, and Anki.

These constraints do not change the documented command syntax, but they should guide backups, automation, testing, and future CLI improvements.
