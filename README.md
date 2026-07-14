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

The dashboard is not live in real time. It updates after each successful workflow run and after GitHub Pages serves the updated committed files.

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
tn-dept-ag/###-2305 (PRIVATE REPO)
tn-dept-ag/###-8886 (PRIVATE REPO)
tn-dept-ag/tda-code-metrics
tn-dept-ag/###-1371 (PRIVATE REPO)
tn-dept-ag/###-2615 (PRIVATE REPO)
tn-dept-ag/###-6673 (PRIVATE REPO)
tn-dept-ag/###-2249 (PRIVATE REPO)
tn-dept-ag/###-5427 (PRIVATE REPO)
tn-dept-ag/###-9580 (PRIVATE REPO)
tn-dept-ag/###-8658 (PRIVATE REPO)
tn-dept-ag/.github
```

When adding or removing repositories, also confirm that the GitHub App installation has access to the same repository list.

The current workflow is configured for the `tn-dept-ag` owner. If repositories from another owner are added, the GitHub App must also be installed on that owner, or the workflow must be updated to request an installation token for that owner.

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

1. Creates a temporary GitHub App installation token.
2. Checks out this repository using the GitHub App token.
3. Installs `cloc`.
4. Sets up Python.
5. Runs `scripts/collect_metrics.py`.
6. Updates CSV files in `data/`.
7. Copies CSV files to `docs/data/`.
8. Commits and pushes the updated metrics files using the GitHub App bot identity.

The workflow is configured to sync with the latest `main` branch before generating and pushing metrics. It also retries the push if `main` changes while the workflow is running.

## GitHub App Authentication

This repository uses a GitHub App for workflow authentication instead of a personal access token.

The GitHub App is used to generate a temporary installation token during each workflow run. That token is used to:

1. Clone or fetch the tracked repositories listed in `config/repos.txt`.
2. Commit updated metrics files back to `tn-dept-ag/tda-code-metrics`.

### Required GitHub App permissions

The GitHub App should be installed on the repositories listed in `config/repos.txt`, including this repository.

Minimum repository permissions:

| Permission | Access |
|---|---|
| Contents | Read and write |
| Metadata | Read-only |

`Contents: Read and write` is needed because the workflow reads tracked repositories and writes updated CSV files back to this repository.

### Required repository variable

The workflow uses this repository variable:

```text
APP_ID
```

Location:

```text
tn-dept-ag/tda-code-metrics
→ Settings
→ Secrets and variables
→ Actions
→ Variables
```

The value should be the numeric GitHub App ID.

### Required repository secret

The workflow uses this repository secret:

```text
APP_PRIVATE_KEY
```

Location:

```text
tn-dept-ag/tda-code-metrics
→ Settings
→ Secrets and variables
→ Actions
→ Secrets
```

The value should be the full GitHub App private key, including the begin and end lines:

```text
-----BEGIN RSA PRIVATE KEY-----
...
-----END RSA PRIVATE KEY-----
```

Do not commit the private key to the repository.

### Removed PAT secret

The previous PAT-based secret is no longer used:

```text
METRICS_REPO_TOKEN
```

This secret should remain deleted unless the workflow is intentionally reverted to PAT-based authentication.

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

Local runs use your local GitHub CLI authentication. They do not use the GitHub App secrets or workflow installation token.

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

## Updating Tracked Repositories

When adding, removing, renaming, archiving, or restoring repositories:

1. Update `config/repos.txt`.
2. Confirm the GitHub App is installed on each listed repository.
3. Confirm this repository is still included in the GitHub App installation.
4. Run the workflow manually from the Actions tab.
5. Confirm the dashboard still loads.

If a repository is outside `tn-dept-ag`, either keep it out of `config/repos.txt` or update the workflow and GitHub App installation strategy to support that owner.

## Security Notes

Keep this repository private unless the following information is acceptable to expose:

- Internal repository names.
- Author names and commit emails.
- Commit volume and development activity patterns.
- Language breakdowns and codebase size.
- GitHub Pages dashboard data.

Do not commit:

- GitHub App private keys.
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
3. The GitHub App is installed on the repository.
4. The workflow is requesting a token for the correct owner.

### `Resource not accessible by integration`

This usually means the GitHub App token does not have access to the repository or permission being requested.

Check that:

1. The GitHub App is installed on the repository.
2. The app has `Contents: Read and write` permission.
3. The repository is included in the app installation's selected repository list.
4. The workflow is using the expected `APP_ID` and `APP_PRIVATE_KEY` values.

### `Bad credentials` or app token creation fails

Check that:

1. `APP_ID` is the numeric GitHub App ID.
2. `APP_PRIVATE_KEY` contains the full private key text.
3. The private key has not been deleted or replaced in the GitHub App settings.
4. The GitHub App has been installed on `tn-dept-ag`.

### `PermissionError: Permission denied` for a CSV

Close the CSV file in Excel or any other program that may have locked it, then rerun the script.

### Workflow push rejected with `fetch first`

Start a new workflow run instead of rerunning an old failed job after workflow changes.

The workflow is designed to sync with the latest `main` branch before pushing updated metrics and to retry if the remote branch changes while the workflow is running.

## Maintenance Checklist

Use this checklist when maintaining the repository:

- Update `config/repos.txt` when repositories are added, renamed, archived, or removed.
- Update the GitHub App installation when `config/repos.txt` changes.
- Keep `APP_ID` as a repository variable.
- Keep `APP_PRIVATE_KEY` as a repository secret.
- Rotate the GitHub App private key if it is exposed, replaced, or no longer trusted.
- Do not recreate `METRICS_REPO_TOKEN` unless intentionally reverting to PAT-based authentication.
- Update the `--since` date when beginning a new reporting period.
- Confirm the dashboard still loads after changes to `docs/index.html` or `docs/data/`.
