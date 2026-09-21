# TDA Code Metrics — AI Agent Configuration

This document defines standard operating procedures, environmental constraints, and coding standards for AI coding agents working in the `tda-code-metrics` repository.

These instructions are intended for Codex in VS Code and may also be followed by other coding agents such as Cline, Gemini, or Claude Code (see also `CLAUDE.md`).

## What This Repository Is

`tda-code-metrics` collects and publishes code activity metrics (current lines of code by language via `cloc`, and committed line activity via Git history) across selected `tn-dept-ag` GitHub repositories. A scheduled GitHub Actions workflow (`.github/workflows/collect-metrics.yml`) runs `scripts/collect_metrics.py`, writes CSV output to `data/`, masks private repository names, copies the public-safe CSVs to `docs/data/`, and pushes the result to `main` so GitHub Pages can serve `docs/index.html` as a static dashboard.

This is not a GIS/geospatial repository. There is no `geopandas`, `arcpy`, ArcGIS Online/Enterprise integration, or spatial data anywhere in this project.

## Primary Objective

Make the smallest safe change that satisfies the user's request while preserving the existing repository structure, coding style, and documentation format.

## Repository Data Classification

- Treat this repository as Tennessee Department of Agriculture work content by default.
- This repository's data is internal GitHub activity metadata, not GIS, customer, or regulated data. It includes: internal `tn-dept-ag`/`tn-dept-forestry` repository names, author names and commit emails, commit volume/activity patterns, and language/codebase-size breakdowns.
- `docs/` and `docs/data/*.csv` are published publicly via GitHub Pages. The workflow masks private repository names before writing to `docs/data/`, but author names/emails and language/LOC data for private repos are still published. Do not weaken or remove that masking step without explicit user confirmation.
- Do not open this repository with personal Gemini, personal cloud tools, or other personal-provider tools unless the user explicitly confirms the content is approved for cross-provider use.

## VS Code Repository Access

- Treat the currently opened VS Code workspace folder as the active repository.
- Use repository-relative paths in all explanations and edits.
- Prefer direct workspace file tools for reading, searching, creating, and editing files.
- Use open editor tabs, selected text, and visible file context when available.
- If a needed file is not visible or accessible through workspace file tools, ask the user to confirm that the correct folder is open in VS Code or to paste the relevant file contents.
- Do not invent file paths, repository structure, schemas, function names, or configuration values that have not been observed in the workspace or provided by the user.

## Working Guidelines

- Make the smallest, most efficient change that satisfies the request.
- Preserve existing code architecture, Markdown structure, and wording unless the task explicitly asks for broader refactoring or cleanup.
- Prefer plain Markdown and GitHub-supported syntax over custom HTML for documentation.
- Treat documentation as a team-wide default; avoid unnecessary formatting churn.
- Before editing, inspect only the files needed for the task.
- After editing, summarize the changed files and the purpose of each change.

## Project Facts

- **Language/runtime:** Python only. `scripts/collect_metrics.py` uses only the standard library (`argparse`, `csv`, `json`, `subprocess`, `pathlib`, etc.) — there is no `requirements.txt`, `pyproject.toml`, `src/`, or `notebooks/` in this repository.
- **CI Python version:** 3.13 (`.github/workflows/collect-metrics.yml` → `actions/setup-python@v6`). `.python-version` and `.devcontainer/devcontainer.json` should match.
- **External tools:** `cloc` (for current-LOC metrics) and the `gh` CLI (for repo discovery and, locally, authentication) must be on `PATH`.
- **Dev tooling:** `ruff` (lint/format) and `pre-commit` are configured via `.pre-commit-config.yaml`. There is no automated test suite.
- **Input/output layout:** `config/repos.txt` (git-ignored, private) or `config/repos.example.txt` (tracked template) as input; `data/*.csv` as canonical output; `docs/data/*.csv` as the public-safe copies read by the dashboard.
- If you add a real Python dependency, you must also add a dependency-management file (e.g. `requirements.txt` or `pyproject.toml`) and update this section — don't assume one already exists.

## Environment & Tooling Constraints

- **Execution Surface Matters:** Codex Desktop on managed Windows workstations may block local shell and PowerShell execution. Codex CLI running inside Ubuntu/WSL can use scoped Linux terminal commands when the user launches it from the target repo.
- **Prefer WSL for Commands:** For command-dependent inspection, tests, formatters, package tooling, or Linux-first workflows, use the WSL terminal/Codex CLI from the repository root.
- **Direct File IO Fallback:** If terminal execution is blocked in the current surface, use direct file-read, file-search, and file-write/edit tools for repository work.
- **Command-Based Verification:** When command execution is available, run narrowly scoped read-only checks or project validation commands such as `git diff`, `ruff check .`, or relevant script help/version checks. If commands are blocked, perform manual review and report what was not run.
- **Dependency Installation:** Do not install packages, extensions, CLIs, or system tools unless the user explicitly asks for setup or approves the install.
- **Ask When Blocked:** If the required context cannot be accessed through available tools, ask the user for the exact path, file contents, schema, or error text.

## File Editing Workflow

1. Identify the relevant file or folder from the user's request.
2. Use workspace file-search/read tools or scoped WSL commands to inspect the smallest necessary context.
3. Make targeted edits with direct file-write/edit tools or a focused patch.
4. Run relevant validation when command execution is available and safe for the repo.
5. If terminal execution is blocked, perform manual review instead of command-based validation.
6. In the final response, report:
   - files changed;
   - what changed;
   - commands run, or validation not performed because terminal execution was blocked;
   - any follow-up action the user needs to run manually.

## Validation

- For Markdown-only edits, review heading levels, links, tables, fenced code blocks, and list indentation.
- For `.github/workflows/collect-metrics.yml` and other YAML/JSON edits, validate syntax carefully — this workflow is the only thing that keeps the dashboard current, and it authenticates and pushes to `main` via a GitHub App token, so a broken workflow fails silently until the next scheduled run.
- For `scripts/collect_metrics.py` edits, inspect surrounding code for imports, naming conventions, indentation, and expected side effects. Remember it must keep working with the standard library only unless a dependency file is deliberately introduced.
- Do not introduce generated artifacts, build outputs, lockfiles, logs, cache directories, or editor metadata such as `.vscode/` files unless explicitly requested.
- When command execution is available, run the narrowest meaningful check (see Default Validation Commands). If commands are blocked, tell the user the exact command to run manually.

## Default Validation Commands

When command execution is available, prefer the narrowest relevant check:

- Markdown-only edits: manually review Markdown structure (or run `pre-commit run markdownlint --all-files` if `pre-commit` is installed).
- Python linting/formatting: `ruff check .` and `ruff format --check .`, or `pre-commit run --all-files` to run the full configured hook set.
- GitHub Actions or other YAML edits: validate syntax with available tooling (e.g. `pre-commit run check-yaml --all-files`); otherwise inspect indentation and key structure carefully.
- There is no `pytest` suite in this repository; do not assume one exists.

## Repository Data Handling

- `data/*.csv` and `docs/data/*.csv` are small, plain-text CSVs — read them directly when needed, no special handling required.
- Never commit `config/repos.txt` (it can contain private repository names), a GitHub App private key, or a `.env` file.
- Do not weaken the private-repo-name masking logic embedded in `.github/workflows/collect-metrics.yml` without explicit user confirmation — it is what makes it safe to publish `docs/data/` publicly.

## Script Networking Constraints

- **Corporate Proxy:** TDA team members operate behind a Zscaler corporate proxy.
- **External Requests:** `scripts/collect_metrics.py` and local `git`/`gh` commands make outbound network requests. When troubleshooting local runs, remind the user they may need to configure their environment to trust the local Zscaler certificate path.
- **TLS Verification:** Do not recommend disabling TLS verification except as a temporary internal troubleshooting step. If mentioned, clearly label `verify=False` or equivalent settings as temporary and not appropriate for production.

## Coding Standards & Preferences

- **Python:** Standard library only, matching `scripts/collect_metrics.py`. Don't introduce a third-party dependency without also adding a dependency-management file and flagging it to the user.
- **Formatting:** Follow `ruff`/`ruff-format` conventions as configured in `.pre-commit-config.yaml`.
- **Markdown:** Preserve existing heading style, list style, table alignment, and terminology unless the user asks for cleanup.
- **Workflow YAML:** Preserve the existing retry/masking logic in `.github/workflows/collect-metrics.yml` unless the user explicitly asks to change it.

## Git and Pull Request Behavior

- Read-only git commands such as `git status`, `git diff`, `git log`, and `git show` may be used for context and validation when command execution is available.
- Do not stage, commit, push, reset, clean, rebase, or create branches unless the user explicitly asks for that git action.
- Never use destructive git commands to discard user work unless the user explicitly requests that exact operation.
- The scheduled workflow pushes directly to `main` under a GitHub App bot identity. Do not attempt to replicate, trigger, or bypass that push behavior manually.
- If a commit message or PR summary is requested, draft it from the edits made and clearly state whether git commands were run.

## When Access Fails

If repository files cannot be accessed or edited from Codex in VS Code, Codex Desktop, or Codex CLI:

- Ask the user to confirm that VS Code is opened at the repository root, not a parent folder, child folder, or disconnected workspace.
- Ask the user to open the target file in the editor or paste the relevant contents.
- Continue using the provided content rather than attempting terminal workarounds.
- Do not claim that files were changed unless a direct file-write/edit tool reported success.

## Definition of Done

A task is complete when the requested direct edits are made and the response includes a brief summary of changed files, important assumptions, and any manual validation the user should perform.
