# Obsidian2Anki Roadmap

This roadmap describes the planned direction of Obsidian2Anki after the current `0.1.0` development baseline. It is organized by release goals rather than fixed dates so reliability work can take priority over feature deadlines.

> [!IMPORTANT]
> The roadmap is directional, not a guarantee. Priorities may change when testing, user feedback, Gemini API changes, AnkiConnect changes, or data-safety concerns reveal more urgent work.

## Guiding Principles

Development should follow five priorities:

1. **Protect user data** — never risk losing Obsidian metadata, Anki notes, or synchronization state unnecessarily.
2. **Prefer correctness over speed** — synchronization must be predictable before concurrency or large-scale processing is introduced.
3. **Make failures recoverable** — interrupted or partially failed runs should be diagnosable and safe to resume.
4. **Keep the CLI scriptable** — commands should return reliable exit codes and support machine-readable output where useful.
5. **Preserve clear boundaries** — vault access, state management, AI generation, Anki access, and workflow orchestration should remain independently testable.

## Status Legend

| Status       | Meaning                                          |
| ------------ | ------------------------------------------------ |
| ✅ Available | Implemented in the current codebase              |
| 🔜 Next      | Highest-priority work for the next patch release |
| 🧭 Planned   | Intended for a later minor release               |
| 💡 Exploring | Useful direction that requires more design work  |

## Current Baseline — `0.1.0`

The current development version already provides:

- ✅ An installable `obsidian2anki` console command.
- ✅ `process`, `migrate`, `format-notes`, `clear`, `delete-card`, `delete-note`, `doctor`, and `stats` commands.
- ✅ Dry-run support for mutating bulk commands.
- ✅ Verbose logging, Rich terminal output, rotating log files, version output, and shell-completion integration.
- ✅ Obsidian Markdown parsing with YAML frontmatter, note IDs, tags, and generated `anki_cards` metadata.
- ✅ Include/exclude tag filtering.
- ✅ SHA-256 change detection and JSON-based local state tracking.
- ✅ Automatic creation of the configured state directory and `state.json` file.
- ✅ Gemini-powered structured flashcard generation validated through Pydantic models.
- ✅ AnkiConnect integration with deck creation, note insertion, note deletion, and deck statistics.
- ✅ Source-level documentation for installation, configuration, workflow, architecture, CLI usage, and AI behavior.

The releases below focus first on making these capabilities safer and easier to verify.

---

## `0.1.1` — Reliability and Data Safety

**Goal:** Remove known failure modes that can leave Obsidian, Anki, and `state.json` inconsistent.

### AI and retry safety

- 🔜 Distinguish Gemini rate limits from authentication errors, invalid requests, unavailable models, and other permanent failures.
- 🔜 Replace the unbounded Gemini retry loop with a configurable attempt limit, exponential backoff, jitter, and a clear final error.
- 🔜 Reset retry delay after a successful request so one temporary outage does not permanently slow later notes.
- 🔜 Stop including the API key in authentication-failure logs.
- 🔜 Resolve contradictory language instructions in `input/prompt.md` and add prompt-level validation examples.

### Synchronization safety

- 🔜 Generate and validate replacement cards before deleting cards from the previous successful version of a note.
- 🔜 Add compensating cleanup when only part of an Anki insertion succeeds.
- 🔜 Write state atomically through a temporary file and preserve a recoverable backup.
- 🔜 Validate corrupted or incompatible state data with a useful recovery message instead of failing during startup without guidance.
- 🔜 Keep `card_count`, `anki_note_ids`, vault metadata, and Anki note IDs synchronized after every deletion.

### CLI and service correctness

- 🔜 Return a non-zero exit code when a command completes with an operational failure.
- 🔜 Make services return structured outcomes instead of logging errors and silently returning success.
- 🔜 Fix `delete-note` so an unknown note ID exits safely before constructing a path from missing state data.
- 🔜 Ensure `format-notes` modifies only notes identified as legacy notes and never reformats already valid notes.
- 🔜 Add explicit confirmation or a force flag for destructive operations such as `clear`.

### Anki transport reliability

- 🔜 Add request timeouts to every AnkiConnect call.
- 🔜 Correct automatic Anki startup polling so it stops when Anki becomes reachable and does not report failure after success.
- 🔜 Separate Anki note IDs from card IDs consistently in names, logs, models, and documentation.
- 🔜 Validate that the configured note type contains `Front`, `Back`, and `NoteID` before processing begins.

### Exit criteria

`0.1.1` is ready when an interrupted or failed note update preserves the last known-good cards and produces a reliable non-zero command status with actionable logs.

---

## `0.2.0` — Test and Quality Foundation

**Goal:** Make behavior verifiable before expanding the synchronization engine.

- 🧭 Add unit tests for settings, content normalization, tag filtering, state hashing, state mutation, and CLI mapping.
- 🧭 Add service tests for processing, migration, formatting, deletion, clearing, diagnostics, and statistics.
- 🧭 Add mocked Gemini and AnkiConnect clients so tests never require external services.
- 🧭 Add integration tests using temporary vaults and state directories.
- 🧭 Add regression tests for every issue fixed in `0.1.1`.
- 🧭 Introduce coverage reporting with a documented minimum threshold.
- 🧭 Add CI for supported Python versions and major desktop operating systems where practical.
- 🧭 Run Ruff formatting/linting and a static type checker in CI.
- 🧭 Define development dependencies and optional dependency groups in `pyproject.toml`.
- 🧭 Add pre-commit hooks for formatting, linting, trailing whitespace, and common repository checks.
- 🧭 Add deterministic fixtures for legacy notes, valid notes, malformed frontmatter, empty notes, duplicate IDs, and stale Anki metadata.

### Exit criteria

`0.2.0` is ready when core workflows can be tested locally and in CI without a real Obsidian vault, Gemini key, or running Anki instance.

---

## `0.3.0` — Reconciliation and Resumable Sync

**Goal:** Detect and repair differences among the vault, Anki, and local state.

- 🧭 Add a `reconcile` command that reports missing cards, orphaned Anki notes, stale vault metadata, duplicate note IDs, and state entries whose files no longer exist.
- 🧭 Support a read-only reconciliation report before any repair is applied.
- 🧭 Add per-note checkpoints so large migrations can resume safely after interruption.
- 🧭 Record explicit processing status and last error information for failed notes.
- 🧭 Detect renamed or moved notes by stable frontmatter ID rather than treating path changes as unrelated files.
- 🧭 Handle notes removed from the vault through an explicit cleanup policy.
- 🧭 Scan only supported Markdown files and optionally recurse through subfolders.
- 🧭 Continue processing independent notes after one failure while producing a complete run summary.
- 🧭 Add duplicate-ID detection before any Anki mutation occurs.
- 🧭 Add state-schema versioning and migrations for future compatibility.

### Exit criteria

`0.3.0` is ready when the application can explain synchronization drift and safely resume or repair common inconsistent states.

---

## `0.4.0` — Configuration and Extensibility

**Goal:** Remove unnecessary hardcoding and make common workflows configurable without source edits.

- 🧭 Provide safe defaults for optional settings while keeping secrets and required paths explicit.
- 🧭 Validate paths, URLs, list values, retry counts, and folder relationships at configuration load time.
- 🧭 Make Gemini model, temperature, card-count range, retry policy, and prompt path configurable.
- 🧭 Make Anki note type and field mapping configurable instead of requiring a modified `Basic` type.
- 🧭 Support deck routing through tags or frontmatter.
- 🧭 Add a documented frontmatter schema with validation messages for `id`, `tags`, and `anki_cards`.
- 🧭 Store prompt/version metadata with state so users can intentionally regenerate cards after changing generation rules.
- 🧭 Define protocols for AI and Anki clients and use them directly in dependency injection.
- 💡 Explore additional AI providers without coupling core workflows to a provider-specific SDK.

### Exit criteria

`0.4.0` is ready when the supported model, note type, field names, and deck strategy can be changed through validated configuration.

---

## `0.5.0` — CLI Experience and Performance

**Goal:** Make larger vaults easier to preview, process, automate, and inspect.

- 🧭 Add progress reporting and end-of-run summaries with processed, skipped, failed, and retried counts.
- 🧭 Add `--json` output for diagnostics, statistics, dry runs, and automation.
- 🧭 Add note selection options such as `--id`, `--path`, `--tag`, and processing limits.
- 🧭 Add an interactive preview of generated cards before committing them to Anki.
- 🧭 Add bounded concurrency or batching only after rate limits and synchronization transactions are safe.
- 🧭 Cache unchanged normalized note content and prompt metadata where it materially reduces work.
- 🧭 Improve statistics with failure counts, last successful run, cards per note, and drift indicators.
- 🧭 Add shell-completion installation documentation and supported-shell tests.
- 💡 Explore a watch mode that responds to vault changes without polling too aggressively.

### Exit criteria

`0.5.0` is ready when large migrations provide clear progress, controlled selection, reliable summaries, and script-friendly output.

---

## `1.0.0` — Stable Release

**Goal:** Deliver a documented, tested, and migration-safe public interface.

The first stable release should require:

- 🧭 No known data-loss defects in supported workflows.
- 🧭 Stable command names, argument behavior, configuration keys, and exit-code conventions.
- 🧭 A versioned state schema with automatic migrations and backup/recovery guidance.
- 🧭 High-value unit and integration coverage for every mutating workflow.
- 🧭 Reconciliation and recovery tools for common inconsistencies.
- 🧭 A reproducible release process with signed or otherwise verifiable release artifacts where practical.
- 🧭 Installation from a published Python package in addition to editable source installation.
- 🧭 Complete README, installation, configuration, workflow, architecture, CLI, AI, examples, troubleshooting, security, support, changelog, and migration documentation.
- 🧭 A documented compatibility policy for Python, Obsidian note format, Anki, AnkiConnect, and the selected AI API.
- 🧭 Release notes and upgrade instructions for every breaking change.

---

## Documentation Backlog

The main technical guides are available. The next documentation work should add:

- 🧭 `docs/examples.md` with realistic note-to-card examples in multiple languages and formats.
- 🧭 `docs/troubleshooting.md` organized by startup, configuration, Gemini, Anki, state, and vault failures.
- 🧭 A state-recovery and backup guide after atomic persistence is implemented.
- 🧭 Contributor/developer setup after automated tests and CI exist.
- 🧭 Release and upgrade documentation once tagged releases begin.

## Ideas Deferred Until the Core Is Stable

These ideas may be valuable, but they should not displace synchronization correctness and testing:

- 💡 A graphical desktop interface.
- 💡 A dedicated Obsidian plugin.
- 💡 Mobile execution.
- 💡 Cloud-hosted synchronization.
- 💡 Shared-team vault workflows.
- 💡 Richer Anki note types such as cloze cards and media cards.

## How Priorities Are Chosen

Work should be prioritized in this order:

1. Security or data-loss risk.
2. Incorrect synchronization or unrecoverable state.
3. Broken installation or command execution.
4. Missing tests for existing behavior.
5. Usability and observability improvements.
6. Performance improvements.
7. New features.

For completed work and release history, see [CHANGELOG.md](CHANGELOG.md).
