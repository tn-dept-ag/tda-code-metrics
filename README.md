# TDA Code Metrics

This repository tracks code metrics across selected TDA/TDF GitHub repositories.

It collects two related kinds of metrics:

1. **Current codebase size** by repository and language using `cloc`.
2. **Committed line activity** by repository, date, and author using Git history.

The repository also publishes a simple static dashboard from the `docs/` folder using GitHub Pages.

## Dashboard

The dashboard is located at:

```text
/docs/index.html
```

Dashboard data is read from:

```text
/docs/data/
```

When GitHub Pages is enabled from the `main` branch and `/docs` folder, the dashboard is available at the repository's GitHub Pages URL.

For this repository, the expected GitHub Pages URL is:

```text
https://tn-dept-ag.github.io/tda-code-metrics/
```

The dashboard updates when the GitHub Actions workflow successfully regenerates the CSV outputs, copies them into `docs/data/`, and pushes the updated files to `main`.

## Repository Structure

```text
tda-code-metrics/
├─ .github/
│  └─ workflows/
│     └─ collect-metrics.yml
├─ config/
│  └─ repos.txt
├─ data/
│  ├─ current_loc_by_language.csv
│  ├─ commit_activity_by_day.csv
│  ├─ run_summary_history.csv
│  └─ repo_summary_history.csv
├─ docs/
│  ├─ index.html
│  ├─ .nojekyll
│  └─ data/
│     ├─ current_loc_by_language.csv
│     ├─ commit_activity_by_day.csv
│     ├─ run_summary_history.csv
│     └─ repo_summary_history.csv
├─ scripts/
│  └─ collect_metrics.py
├─ .gitignore
└─ README.md
```

## Tracked Repositories

Repositories are listed in:

```text
config/repos.txt
```

Use one repository per line:

```text
owner/repository-name
```

Blank lines and comment lines beginning with `#` are ignored.

Example:

```text
# One owner/repo per line.
tn-dept-ag/tda-template
tn-dept-ag/tdf-facilities
tn-dept-ag/tda-code-metrics
tn-dept-ag/tda-agol-content-management
tn-dept-ag/tdf-agol-admin-insights
tn-dept-ag/tda-agol-monitor-dependencies
tn-dept-ag/tda-admin-management
tn-dept-ag/tda-supervisor-management
tn-dept-ag/tdf-agol-data-backups
tn-dept-ag/.github
```

When adding or removing repositories, also confirm that the GitHub token used by the workflow has access to the same repository list.

## Output Files

| File | Purpose | Behavior |
|---|---|---|
| `data/current_loc_by_language.csv` | Current repository size by language | Recreated each run |
| `data/commit_activity_by_day.csv` | Commit activity by repository, date, and author | Recreated each run using the configured `--since` date |
| `data/run_summary_history.csv` | One summary row per metrics run | Preserves historical run summaries |
| `data/repo_summary_history.csv` | One summary row per repository per metrics run | Preserves historical repository summaries |
| `docs/data/*.csv` | Copies used by the GitHub Pages dashboard | Updated by the workflow |

## Metric Definitions

### Current LOC metrics

Current lines of code are calculated with `cloc`.

The current LOC output includes:

```text
run_date,repo,language,files,blank,comment,code
```

Important distinction:

- `current_loc_by_language.csv` is a point-in-time snapshot.
- It is not filtered by the `--since` date.
- It represents the current contents of each tracked repository at the time the workflow runs.

### Commit activity metrics

Committed line activity is calculated from Git history using `git log --numstat`.

The commit activity output includes:

```text
run_date,repo,commit_date,author_email,author_name,commits,added,deleted,net
```

The workflow currently filters commit activity using:

```text
--since 2026-01-01
```

This means `commit_activity_by_day.csv`, `run_summary_history.csv`, and `repo_summary_history.csv` summarize activity beginning on January 1, 2026.

## Automation

Metrics are collected by GitHub Actions using:

```text
.github/workflows/collect-metrics.yml
```

The workflow can be run two ways:

1. Manually from the GitHub Actions tab.
2. Automatically on the configured schedule.

Current schedule:

```yaml
cron: "0 6 * * 1"
```

This runs every Monday at 6:00 AM UTC.

Approximate Eastern time:

| Time of year | Local run time |
|---|---|
| Eastern Standard Time | Monday at 1:00 AM |
| Eastern Daylight Time | Monday at 2:00 AM |

The workflow performs these steps:

1. Checks out this repository.
2. Installs `cloc`.
3. Sets up Python.
4. Runs `scripts/collect_metrics.py`.
5. Updates CSV files in `data/`.
6. Copies CSV files to `docs/data/`.
7. Commits and pushes the updated metrics files.

## Required GitHub Secret

The workflow uses this repository secret:

```text
METRICS_REPO_TOKEN
```

This secret should contain a GitHub personal access token with read access to the repositories listed in:

```text
config/repos.txt
```

For a fine-grained personal access token, use repository-level access with at least:

```text
Contents: Read-only
Metadata: Read-only
```

Do not commit the token to the repository.

## Local Setup

From the repository root, use Command Prompt in VS Code.

Activate the virtual environment:

```cmd
.venv\Scripts\activate.bat
```

Confirm required tools:

```cmd
python --version
git --version
gh --version
cloc --version
```

Confirm GitHub CLI authentication:

```cmd
gh auth status
```

If needed, authenticate with:

```cmd
gh auth login
```

## Run Locally

Run the collector:

```cmd
python -u scripts\collect_metrics.py --repo-list config\repos.txt --workspace .cache\repos --output data --author-email YOUR_EMAIL@example.com --since 2026-01-01
```

If you use more than one Git commit email, add multiple `--author-email` arguments:

```cmd
python -u scripts\collect_metrics.py --repo-list config\repos.txt --workspace .cache\repos --output data --author-email FIRST_EMAIL@example.com --author-email SECOND_EMAIL@example.com --since 2026-01-01
```

After a successful local run, copy the CSV files to the dashboard data folder:

```cmd
copy data\*.csv docs\data\
```

Then commit the updates:

```cmd
git add data\*.csv docs\data\*.csv
git commit -m "Update code metrics"
git push
```

## Updating the Dashboard

The dashboard is a static HTML page:

```text
docs/index.html
```

It reads CSV data from:

```text
docs/data/
```

To update the dashboard design, edit `docs/index.html`.

To update the dashboard data, run the workflow or run the collector locally and copy the CSV files into `docs/data/`.

## Updating the Start Date

The workflow currently summarizes commit activity since:

```text
2026-01-01
```

To start a new reporting year, update the `--since` argument in:

```text
.github/workflows/collect-metrics.yml
```

Example:

```text
--since 2027-01-01
```

Current LOC metrics are not affected by this date because they represent the current state of each repository.

## Security Notes

Keep this repository private unless the following information is acceptable to expose:

- Internal repository names.
- Author names and commit emails.
- Commit volume and development activity patterns.
- Language breakdowns and codebase size.
- GitHub Pages dashboard data.

Do not commit:

- Personal access tokens.
- `.env` files.
- Cloned repository caches.
- Local virtual environments.
- Temporary output folders.

The `.gitignore` should continue excluding local caches such as:

```text
.cache/
repos/
.venv/
```

## Troubleshooting

### `Required tool not found on PATH`

Confirm the tool is installed and visible in the current terminal:

```cmd
where gh
where cloc
```

If a tool was just installed, fully close and reopen VS Code.

### `Could not resolve to a Repository`

Check that:

1. The repository name in `config/repos.txt` is correct.
2. The repository still exists.
3. The workflow token has access to the repository.
4. Organization SSO authorization is complete if required.

### `PermissionError: Permission denied` for a CSV

Close the CSV file in Excel or any other program that may have locked it, then rerun the script.

### Workflow push rejected with `fetch first`

Start a new workflow run instead of rerunning an old failed job after workflow changes.

The workflow is designed to sync with the latest `main` branch before pushing updated metrics.

## Maintenance Checklist

Use this checklist when maintaining the repository:

- Update `config/repos.txt` when repositories are added, renamed, archived, or removed.
- Update the GitHub PAT repository access when `config/repos.txt` changes.
- Review the workflow after each GitHub token expiration or permission change.
- Update the `--since` date when beginning a new reporting period.
- Confirm the dashboard still loads after changes to `docs/index.html` or `docs/data/`.
