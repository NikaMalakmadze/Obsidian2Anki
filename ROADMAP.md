# Obsidian2Anki Roadmap

This roadmap starts from the current `0.1.0` package plus the unreleased diagnostics refactor in the repository.

> [!IMPORTANT]
> Priorities are directional. Data safety, recoverability, and tests take precedence over new integrations or interfaces.

## Guiding Principles

1. Protect Obsidian notes, Anki data, and synchronization state.
2. Make every failure observable and recoverable.
3. Return reliable exit statuses for users and automation.
4. Keep AI, Anki, vault, state, diagnostics, and CLI boundaries independently testable.
5. Add performance and new interfaces only after synchronization is safe.

## Status Legend

| Status       | Meaning                                       |
| ------------ | --------------------------------------------- |
| ✅ Available | Implemented in the current repository         |
| 🔜 Next      | Highest-priority patch work                   |
| 🧭 Planned   | Intended after the next reliability release   |
| 💡 Exploring | Useful direction that needs design validation |

## Current Baseline

- ✅ Installable `obsidian2anki` console command.
- ✅ `process`, `migrate`, `format-notes`, `clear`, `delete-card`, `delete-note`, `doctor`, and `stats`.
- ✅ Dry-run support for bulk mutating commands.
- ✅ Recursive Markdown-only discovery for process and migration.
- ✅ Include/exclude tag filtering.
- ✅ Gemini structured output validated by Pydantic.
- ✅ AnkiConnect insertion, lookup, deck creation, and deletion.
- ✅ JSON state with normalized-content hashes and generated Anki note IDs.
- ✅ Rotating logs and Rich output.
- ✅ Doctor routed independently from the main app graph.
- ✅ Separate environment and runtime diagnostic tables.
- ✅ Secret-like environment values redacted in validation output.
- ✅ Detailed installation, configuration, workflow, architecture, CLI, AI, and diagnostics documentation.

## `0.1.1` — Correctness and Data Safety

**Goal:** remove defects that can lose previous cards, expose secrets, or leave the three data stores inconsistent.

### Synchronization safety

- 🔜 Generate and validate replacement cards before deleting the previous successful Anki notes.
- 🔜 Detect and compensate for partial `addNotes` results.
- 🔜 Make deletion operations idempotent when Anki notes or source files are already missing.
- 🔜 Keep `card_count`, `anki_note_ids`, and frontmatter synchronized after every deletion.
- 🔜 Update frontmatter through parsed YAML rather than inserting at raw line index 2.

### State safety

- 🔜 Write state through a temporary file and atomic replace.
- 🔜 Preserve a recoverable backup before replacing state.
- 🔜 Add schema versioning and useful invalid-state recovery errors.
- 🔜 Place state and prompt initialization inside a controlled startup error boundary.

### AI safety

- 🔜 Remove the API key from every log message and rotate exposed development keys.
- 🔜 Classify transient and permanent Gemini errors.
- 🔜 Add configurable bounded retries, jitter, and a final failure result.
- 🔜 Reset backoff after successful generation.
- 🔜 Resolve the contradictory language instruction in `input/prompt.md`.
- 🔜 Add schema constraints for non-empty text and one-to-five cards.

### CLI and service correctness

- 🔜 Return non-zero status when any note or diagnostic fails.
- 🔜 Replace log-only service outcomes with structured result objects.
- 🔜 Fix unknown-ID handling in `delete-note`.
- 🔜 Fix `delete-card` for integer, string, and YAML-list `anki_cards` representations.
- 🔜 Fix the `stats` processed-note indexing defect.
- 🔜 Make `process --dry-run` evaluate and list eligible notes.
- 🔜 Add confirmation or `--force` for destructive commands.

### Diagnostics correctness

- 🔜 Check prompt existence/readability before constructing `AI`.
- 🔜 Catch unexpected doctor exceptions and render an internal-error result.
- 🔜 Return diagnostic failure status when any row fails.
- 🔜 Add log-directory and log-writability checks.
- 🔜 Handle Anki becoming unavailable between reachability and deck lookup.
- 🔜 Remove the unused `DoctorService` protocol or define a deliberate diagnostics interface.

### File discovery consistency

- 🔜 Reuse one Markdown discovery policy across formatter, statistics, process, and migration.
- 🔜 Make recursive behavior explicit per command and preserve nested destination structure when configured.
- 🔜 Derive titles with `Path.stem` instead of truncating at the first period.

### Exit criteria

A failed or interrupted update preserves the previous good Anki notes, never writes secrets to logs, produces a non-zero status, and leaves recoverable state.

## `0.2.0` — Automated Test Foundation

**Goal:** verify all current behavior without requiring a real vault, Gemini key, or Anki instance.

- 🧭 Unit tests for settings, normalization, tag logic, hashing, state mutation, and CLI mapping.
- 🧭 Unit tests for `EnvironmentChecker`, `RuntimeChecker`, diagnostic row rendering, and table-width validation.
- 🧭 Service tests for process, migration, formatting, deletion, clearing, and statistics.
- 🧭 Fake Gemini and Anki clients with deterministic responses and errors.
- 🧭 Temporary-vault integration tests for movement, frontmatter, and state writes.
- 🧭 Regression tests for every `0.1.1` defect.
- 🧭 Coverage reporting with a documented threshold.
- 🧭 CI across supported Python versions and practical desktop platforms.
- 🧭 Ruff formatting/linting and static type checking.
- 🧭 Development dependency groups and pre-commit hooks.

### Exit criteria

Core workflows and diagnostics pass deterministically in CI without external services.

## `0.3.0` — Reconciliation and Recovery

**Goal:** detect and repair drift among vault metadata, state, and Anki.

- 🧭 Add a read-only `reconcile` report.
- 🧭 Detect missing Anki notes, orphaned generated notes, stale paths, duplicate frontmatter IDs, and missing source files.
- 🧭 Add explicit repair actions after preview.
- 🧭 Add per-note checkpoints and resumable migrations.
- 🧭 Record failed-note status and last error.
- 🧭 Continue independent migration candidates after failures while returning a complete summary.
- 🧭 Detect renamed/moved files by stable frontmatter ID.
- 🧭 Add state-schema migrations.

### Exit criteria

The application can explain common drift and safely resume or repair it.

## `0.4.0` — Configuration and Provider Boundaries

**Goal:** remove hard-coded integration choices and improve dependency injection.

- 🧭 Inject one validated settings object instead of calling `get_settings()` inside infrastructure classes.
- 🧭 Define protocols for AI generation, Anki operations, state storage, and vault access.
- 🧭 Build command-specific dependencies rather than one eager graph.
- 🧭 Configure Gemini model, generation controls, card limits, and retry policy.
- 🧭 Configure Anki model name and field mapping.
- 🧭 Validate target Anki fields before any mutation.
- 🧭 Support deck routing through frontmatter or tags.
- 🧭 Record prompt/model versions in state for deliberate regeneration.
- 💡 Add local-model and additional hosted-provider adapters.

### Exit criteria

Model, provider, note type, fields, and retry behavior can change through validated configuration and testable adapters.

## `0.5.0` — CLI Experience and Performance

**Goal:** make larger vaults easier to preview, automate, and inspect.

- 🧭 End-of-run summaries for processed, skipped, failed, retried, and unchanged notes.
- 🧭 `--json` output for doctor, stats, reconciliation, and dry runs.
- 🧭 Selectors such as `--id`, `--path`, `--tag`, and `--limit`.
- 🧭 Interactive generated-card review before commit.
- 🧭 Better statistics: cards per note, failures, last success, and drift.
- 🧭 Documented shell-completion setup and tests.
- 🧭 Bounded concurrency only after transactional safety and rate-limit controls exist.
- 💡 Watch mode with conservative filesystem event handling.

## `1.0.0` — Stable Release

Required before stability:

- 🧭 No known data-loss defects in supported workflows.
- 🧭 Stable commands, configuration keys, output contracts, and exit codes.
- 🧭 Versioned state schema with migrations and recovery guidance.
- 🧭 Strong unit/integration coverage for every mutating path.
- 🧭 Reconciliation and backup/restore documentation.
- 🧭 Reproducible release artifacts and published package installation.
- 🧭 Compatibility policy for Python, note format, Anki, AnkiConnect, and AI providers.
- 🧭 Upgrade notes for every breaking change.

## Documentation Backlog

- 🧭 Realistic `docs/examples.md` with multiple note types and languages.
- 🧭 Task-oriented troubleshooting index.
- 🧭 State backup, recovery, and reconciliation guide.
- 🧭 Developer/testing setup after CI exists.
- 🧭 Release and upgrade guide.
- 🧭 Threat model for external AI, local HTTP, prompt injection, and destructive operations.

## Ideas Deferred Until the Core Is Stable

- 💡 Dedicated Obsidian plugin.
- 💡 Desktop GUI.
- 💡 Mobile execution.
- 💡 Team/shared-vault workflows.
- 💡 Cloud synchronization.
- 💡 Cloze, media, and richer Anki note types.
- 💡 Agent-skill packaging for alternate automation workflows.

## Priority Order

1. Security and data-loss risk.
2. Synchronization correctness and recovery.
3. Broken startup or command behavior.
4. Tests for existing behavior.
5. Observability and automation.
6. Performance.
7. New interfaces and features.

See [CHANGELOG.md](CHANGELOG.md) for completed work.
