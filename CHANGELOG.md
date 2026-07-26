# Changelog

All notable changes to Obsidian2Anki will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and this project follows [Semantic Versioning](https://semver.org/).

## [Unreleased]

No unreleased changes yet.

## [0.1.0] - 2026-07-25

### Added

- Added the first public release of Obsidian2Anki.
- Added an installable `obsidian2anki` command-line application.
- Added the `process` command for converting eligible notes from the configured inbox folder into Anki flashcards and moving successfully processed notes into the main notes folder.
- Added the `migrate` command for generating or regenerating cards for new and changed notes already stored in the main notes folder.
- Added the `format-notes` command for converting legacy notes to the required YAML-frontmatter structure with generated UUIDs.
- Added the `delete-card` command for deleting an individual generated Anki note and updating its related Obsidian metadata and local state.
- Added the `delete-note` command for deleting all generated Anki notes associated with an Obsidian note.
- Added the `clear` command for removing application-managed Anki notes, clearing generated frontmatter metadata, and resetting local state.
- Added the `doctor` command with Rich-formatted checks for Python, environment configuration, Obsidian folders, the prompt file, Gemini access, Anki connectivity, the configured deck, logging, and state storage.
- Added the `stats` command for displaying note-processing and generated-card statistics.
- Added `--dry-run` support for `process`, `migrate`, `format-notes`, and `clear`.
- Added global `--verbose` logging and `--version` output.
- Added shell-completion support through `argcomplete`.
- Added Rich terminal output and rotating file logs.
- Added environment-based configuration with Pydantic Settings and `.env` support.
- Added automatic creation of the configured state directory and `state.json` file.
- Added local JSON state tracking for note paths, titles, SHA-256 content hashes, generated Anki note IDs, card counts, and processing timestamps.
- Added SHA-256 change detection so unchanged notes can be skipped during migration.
- Added YAML frontmatter support for note `id`, `tags`, and generated `anki_cards` metadata.
- Added include-tag and exclude-tag filtering.
- Added Markdown normalization, including Obsidian wiki-link conversion and selective formatting removal while preserving fenced code blocks.
- Added Gemini-powered flashcard generation using structured JSON responses validated with Pydantic models.
- Added support for generating between one and five conceptual flashcards from each eligible note.
- Added AnkiConnect integration for connectivity checks, deck discovery and creation, note insertion, note lookup, tag lookup, and deletion.
- Added Anki serialization for `Front`, `Back`, and `NoteID` fields.
- Added duplicate-card retry handling when inserting generated cards into Anki.
- Added constructor-based dependency injection and protocol-defined application service boundaries.
- Added an Obsidian Templater-compatible note template.
- Added project documentation covering installation, configuration, workflow, architecture, CLI usage, and AI integration.
- Added `ROADMAP.md`, `SECURITY.md`, `SUPPORT.md`, `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, and the MIT license.

### Dependencies

- Added runtime support for Python 3.12 and later.
- Added `argcomplete` for shell completion.
- Added `google-genai` for Gemini integration.
- Added `pydantic` and `pydantic-settings` for data validation and configuration.
- Added `python-dotenv` for environment loading.
- Added `python-frontmatter` for Obsidian note metadata.
- Added `requests` for AnkiConnect communication.
- Added `rich` for terminal output.
- Added `tenacity` for retry utilities.

### Known Limitations

- Gemini retry handling does not yet reliably distinguish temporary rate limits from permanent client errors.
- Reprocessing a changed note removes its existing Anki notes before replacement generation and insertion have fully succeeded.
- State writes are not yet atomic and do not create automatic backups.
- Some service-level failures are logged without producing a non-zero CLI exit code.
- `format-notes` may reformat files beyond the legacy notes initially identified for conversion.
- `delete-note` requires additional protection when an unknown note ID is provided.
- Some AnkiConnect operations do not use explicit request timeouts.
- Vault folder scanning is non-recursive and is not restricted exclusively to Markdown files.
- The Gemini model, Anki note type, and Anki field mapping are currently hardcoded.
- The Anki `Basic` note type must contain a manually added `NoteID` field.
- Automated tests and continuous integration are not yet included.

For planned improvements, see [ROADMAP.md](ROADMAP.md).

[Unreleased]: https://github.com/NikaMalakmadze/Obsidian2Anki/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/NikaMalakmadze/Obsidian2Anki/releases/tag/v0.1.0
