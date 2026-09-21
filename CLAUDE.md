# Claude Code Configuration

This document defines Claude Code-specific settings, project context, and development guidance for this repository.

## Overview

`tda-code-metrics` collects code activity metrics (current lines of code by language via `cloc`, and committed line activity via Git history) across selected `tn-dept-ag` GitHub repositories, and publishes a static dashboard from `docs/` via GitHub Pages. See `README.md` for the full data model, workflow, and troubleshooting guide.

This repository is not a GIS/geospatial project — there is no `geopandas`, `arcpy`, ArcGIS Online/Enterprise integration, or spatial data here. For agent-wide constraints (data classification, git/PR behavior, validation commands), see `AGENTS.md`; this file only adds Claude Code-specific setup notes.

## Claude Code Project Setup

### Python Environment

- **Python version:** 3.13, matching `.python-version` and the CI workflow's `actions/setup-python@v6` step.
- **Dependencies:** `scripts/collect_metrics.py` uses only the Python standard library — there is no `requirements.txt` or `pyproject.toml`. Do not assume one exists.
- **Dev tools:** `ruff` (lint/format) and `pre-commit`, configured in `.pre-commit-config.yaml`. There is no automated test suite.
- **External CLI tools:** `cloc` and `gh` must be installed and authenticated (`gh auth login`) for local runs — see "Run Locally" in `README.md`.

### Code Organization

```text
tda-code-metrics/
├── .github/workflows/collect-metrics.yml   # Scheduled/manual metrics collection + publish
├── config/
│   ├── repos.example.txt                   # Tracked template for the local repo list
│   └── repos.txt                           # Git-ignored local repo list (may name private repos)
├── data/                                   # Canonical CSV output (git-tracked, NOT git-ignored)
│   ├── current_loc_by_language.csv         # Point-in-time snapshot, recreated each run
│   ├── commit_activity_by_day.csv          # Recreated each run using --since
│   ├── run_summary_history.csv             # Append-only history
│   └── repo_summary_history.csv            # Append-only history
├── docs/                                   # GitHub Pages dashboard
│   ├── index.html
│   └── data/*.csv                          # Public-safe copies of data/*.csv (private repos masked)
├── scripts/collect_metrics.py              # The collector; stdlib-only
├── AGENTS.md                               # Agent-wide constraints (data handling, git, validation)
├── CLAUDE.md                               # This file
└── README.md                               # Full project documentation
```

`data/*.csv` and `docs/data/*.csv` are committed, published output — not scratch or regenerable-and-discardable files. Never add them to `.gitignore` or delete them as cleanup.

## AI Agent Notes

Refer to `AGENTS.md` for:

- Repository data classification and confidentiality rules (this repo publishes `docs/data/` publicly; private repo names are masked by the workflow, author names/emails are not)
- Constraints on shell execution and direct file I/O
- Validation commands
- Git and pull request behavior, including the workflow's automated push to `main`

### For Claude Code Users

Claude Code can read, edit, and write files directly. Key guidelines:

1. Use existing code patterns and style as a reference.
2. Keep changes minimal and focused on the user's request.
3. Validate syntax and logic before reporting completion.
4. Refer to `AGENTS.md` for data handling, networking, and repository-specific constraints.

## Development Workflow

### Running Code

- **Collector script:**

  ```bash
  python -u scripts/collect_metrics.py --repo-list config/repos.txt --workspace .cache/repos --output data --author-email you@example.com --since 2026-01-01
  ```

  See "Run Locally" in `README.md` for the full local setup (venv activation, `gh auth login`, copying CSVs to `docs/data/`).

- **Workflow:** `.github/workflows/collect-metrics.yml`, runnable manually from the GitHub Actions tab or on its weekly schedule.

### Code Quality

- **Linting/formatting:** `ruff check .` and `ruff format --check .`, or `pre-commit run --all-files` to run the full hook set (trailing whitespace, YAML/JSON checks, ruff, markdownlint).
- **Testing:** No automated test suite exists in this repository.

### Editing and Validation

When Claude Code or other agents edit files:

1. Review changes for correctness.
2. Run `ruff check .` / `pre-commit run --all-files` when available.
3. Manually review Markdown, JSON, and YAML syntax if tools are unavailable — especially `.github/workflows/collect-metrics.yml`, since it authenticates via a GitHub App and pushes directly to `main`.
4. Test script changes locally before assuming the scheduled workflow will succeed.

## Networking & Security

- **Corporate Proxy:** TDA team members operate behind Zscaler proxy; local runs of `git`/`gh`/the collector script may need to trust the local Zscaler certificate.
- **Secrets:** The workflow uses a GitHub App (`APP_ID` variable, `APP_PRIVATE_KEY` secret) rather than a personal access token. Never commit private keys, `.env` files, or a `config/repos.txt` containing private repository names. See "GitHub App Authentication" in `README.md`.

## Validation & Testing

### Manual Review (When Tools Unavailable)

- Markdown: check heading levels, links, and list indentation.
- JSON/YAML: validate syntax, indentation, and required fields — particularly the workflow file.
- Python: inspect imports, naming, indentation, and side effects; confirm no new third-party dependency was introduced without also adding a dependency file.

### Automated Checks (When Available)

- `ruff check .` / `ruff format --check .` (or `pre-commit run --all-files`)
- No `pytest` suite exists.

## Getting Help

- **Claude Code Documentation:** `/help` in Claude Code
- **Project Questions:** Refer to `AGENTS.md` or `README.md`
- **Bug Reports:** Report issues at [claude-code-issues](https://github.com/anthropics/claude-code/issues)
