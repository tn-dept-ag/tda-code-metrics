#!/usr/bin/env python3
"""
Collect code metrics across GitHub repositories.

Outputs:
- data/current_loc_by_language.csv
- data/commit_activity_by_day.csv
- data/run_summary_history.csv
- data/repo_summary_history.csv

Requirements:
- git
- gh
- cloc
- Python 3.10+
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


EXCLUDE_DIRS = [
    ".git",
    ".github",
    ".venv",
    "venv",
    "__pycache__",
    ".ipynb_checkpoints",
    "node_modules",
    "dist",
    "build",
    ".cache",
    "data",
    "outputs",
]


def run_command(
    args: list[str],
    cwd: Path | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        args,
        cwd=cwd,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    if check and result.returncode != 0:
        command = " ".join(args)
        raise RuntimeError(
            f"Command failed:\n{command}\n\nSTDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}"
        )

    return result


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required tool not found on PATH: {name}")


def read_repo_list(path: Path) -> list[str]:
    repos: list[str] = []

    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()

        if not line or line.startswith("#"):
            continue

        repos.append(line)

    return repos


def safe_repo_dir_name(repo: str) -> str:
    return repo.replace("/", "__")


def clone_or_update_repo(repo: str, workspace: Path) -> Path:
    workspace.mkdir(parents=True, exist_ok=True)
    repo_dir = workspace / safe_repo_dir_name(repo)

    if repo_dir.exists():
        run_command(["git", "fetch", "--all", "--prune"], cwd=repo_dir)
        run_command(["git", "pull", "--ff-only"], cwd=repo_dir, check=False)
        return repo_dir

    run_command(["gh", "repo", "clone", repo, str(repo_dir)])
    return repo_dir


def collect_current_loc(repo: str, repo_dir: Path, run_date: str) -> list[dict[str, str | int]]:
    result = run_command(
        [
            "cloc",
            str(repo_dir),
            "--json",
            f"--exclude-dir={','.join(EXCLUDE_DIRS)}",
        ]
    )

    data = json.loads(result.stdout)
    rows: list[dict[str, str | int]] = []

    for language, stats in data.items():
        if language in {"header", "SUM"}:
            continue

        rows.append(
            {
                "run_date": run_date,
                "repo": repo,
                "language": language,
                "files": int(stats.get("nFiles", 0)),
                "blank": int(stats.get("blank", 0)),
                "comment": int(stats.get("comment", 0)),
                "code": int(stats.get("code", 0)),
            }
        )

    return rows


def collect_commit_activity(
    repo: str,
    repo_dir: Path,
    run_date: str,
    author_emails: set[str],
    since: str | None,
) -> list[dict[str, str | int]]:
    command = [
        "git",
        "log",
        "--all",
        "--no-merges",
        "--numstat",
        "--date=short",
        "--pretty=format:@@COMMIT@@%H%x09%ad%x09%ae%x09%an",
    ]

    if since:
        command.insert(2, f"--since={since}")

    result = run_command(command, cwd=repo_dir)

    totals: dict[tuple[str, str, str, str], dict[str, int]] = defaultdict(
        lambda: {"commits": 0, "added": 0, "deleted": 0}
    )

    current_commit_key: tuple[str, str, str, str] | None = None
    counted_current_commit = False

    for raw_line in result.stdout.splitlines():
        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("@@COMMIT@@"):
            payload = line.replace("@@COMMIT@@", "", 1)
            parts = payload.split("\t")

            if len(parts) < 4:
                current_commit_key = None
                counted_current_commit = False
                continue

            _commit_hash, commit_date, author_email, author_name = parts[:4]
            author_email = author_email.lower().strip()

            if author_emails and author_email not in author_emails:
                current_commit_key = None
                counted_current_commit = False
                continue

            current_commit_key = (repo, commit_date, author_email, author_name)
            counted_current_commit = False
            continue

        if current_commit_key is None:
            continue

        columns = line.split("\t")

        if len(columns) < 3:
            continue

        added_raw, deleted_raw, _path = columns[:3]

        # Binary files show "-" instead of numeric line counts.
        if not added_raw.isdigit() or not deleted_raw.isdigit():
            continue

        if not counted_current_commit:
            totals[current_commit_key]["commits"] += 1
            counted_current_commit = True

        totals[current_commit_key]["added"] += int(added_raw)
        totals[current_commit_key]["deleted"] += int(deleted_raw)

    rows: list[dict[str, str | int]] = []

    for (repo_name, commit_date, author_email, author_name), values in sorted(totals.items()):
        added = values["added"]
        deleted = values["deleted"]

        rows.append(
            {
                "run_date": run_date,
                "repo": repo_name,
                "commit_date": commit_date,
                "author_email": author_email,
                "author_name": author_name,
                "commits": values["commits"],
                "added": added,
                "deleted": deleted,
                "net": added - deleted,
            }
        )

    return rows


def summarize_current_loc_by_repo(
    repos: Iterable[str],
    current_loc_rows: list[dict[str, str | int]],
) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {
        repo: {"current_files": 0, "current_code_lines": 0}
        for repo in repos
    }

    for row in current_loc_rows:
        repo = str(row["repo"])
        summary.setdefault(repo, {"current_files": 0, "current_code_lines": 0})
        summary[repo]["current_files"] += int(row["files"])
        summary[repo]["current_code_lines"] += int(row["code"])

    return summary


def summarize_commit_activity_by_repo(
    repos: Iterable[str],
    commit_activity_rows: list[dict[str, str | int]],
) -> dict[str, dict[str, int]]:
    summary: dict[str, dict[str, int]] = {
        repo: {"commits_since_start": 0, "added_since_start": 0, "deleted_since_start": 0, "net_since_start": 0}
        for repo in repos
    }

    for row in commit_activity_rows:
        repo = str(row["repo"])
        summary.setdefault(
            repo,
            {"commits_since_start": 0, "added_since_start": 0, "deleted_since_start": 0, "net_since_start": 0},
        )
        summary[repo]["commits_since_start"] += int(row["commits"])
        summary[repo]["added_since_start"] += int(row["added"])
        summary[repo]["deleted_since_start"] += int(row["deleted"])
        summary[repo]["net_since_start"] += int(row["net"])

    return summary


def build_history_rows(
    repos: list[str],
    current_loc_rows: list[dict[str, str | int]],
    commit_activity_rows: list[dict[str, str | int]],
    run_date: str,
    run_timestamp_utc: str,
    since: str,
    author_emails: set[str],
) -> tuple[list[dict[str, str | int]], list[dict[str, str | int]]]:
    loc_by_repo = summarize_current_loc_by_repo(repos, current_loc_rows)
    commits_by_repo = summarize_commit_activity_by_repo(repos, commit_activity_rows)
    author_filter = ";".join(sorted(author_emails)) if author_emails else "ALL"

    repo_rows: list[dict[str, str | int]] = []

    for repo in repos:
        loc = loc_by_repo.get(repo, {"current_files": 0, "current_code_lines": 0})
        commits = commits_by_repo.get(
            repo,
            {"commits_since_start": 0, "added_since_start": 0, "deleted_since_start": 0, "net_since_start": 0},
        )

        repo_rows.append(
            {
                "run_date": run_date,
                "run_timestamp_utc": run_timestamp_utc,
                "since": since,
                "author_filter": author_filter,
                "repo": repo,
                "current_files": loc["current_files"],
                "current_code_lines": loc["current_code_lines"],
                "commits_since_start": commits["commits_since_start"],
                "added_since_start": commits["added_since_start"],
                "deleted_since_start": commits["deleted_since_start"],
                "net_since_start": commits["net_since_start"],
            }
        )

    run_row = {
        "run_date": run_date,
        "run_timestamp_utc": run_timestamp_utc,
        "since": since,
        "author_filter": author_filter,
        "total_repos": len(repos),
        "current_files": sum(int(row["current_files"]) for row in repo_rows),
        "current_code_lines": sum(int(row["current_code_lines"]) for row in repo_rows),
        "commits_since_start": sum(int(row["commits_since_start"]) for row in repo_rows),
        "added_since_start": sum(int(row["added_since_start"]) for row in repo_rows),
        "deleted_since_start": sum(int(row["deleted_since_start"]) for row in repo_rows),
        "net_since_start": sum(int(row["net_since_start"]) for row in repo_rows),
    }

    return [run_row], repo_rows


def write_csv(path: Path, rows: list[dict[str, str | int]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def append_or_replace_csv(
    path: Path,
    new_rows: list[dict[str, str | int]],
    fieldnames: list[str],
    key_fields: list[str],
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    existing_rows: list[dict[str, str]] = []

    if path.exists():
        with path.open("r", newline="", encoding="utf-8") as csvfile:
            reader = csv.DictReader(csvfile)
            existing_rows = [row for row in reader]

    new_keys = {
        tuple(str(row.get(field, "")) for field in key_fields)
        for row in new_rows
    }

    kept_rows = [
        row
        for row in existing_rows
        if tuple(str(row.get(field, "")) for field in key_fields) not in new_keys
    ]

    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kept_rows)
        writer.writerows(new_rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Collect code metrics across repositories.")
    parser.add_argument("--repo-list", default="config/repos.txt", help="Path to repos.txt.")
    parser.add_argument("--workspace", default=".cache/repos", help="Local repo cache folder.")
    parser.add_argument("--output", default="data", help="Output folder.")
    parser.add_argument(
        "--author-email",
        action="append",
        default=[],
        help="Author email to include. Can be provided multiple times. If omitted, all authors are included.",
    )
    parser.add_argument(
        "--since",
        default=None,
        help="Optional git date filter, for example 2026-01-01 or '1 year ago'.",
    )

    args = parser.parse_args()

    require_tool("git")
    require_tool("gh")
    require_tool("cloc")

    run_started = datetime.now(timezone.utc)
    run_date = run_started.date().isoformat()
    run_timestamp_utc = run_started.isoformat(timespec="seconds").replace("+00:00", "Z")

    repo_list_path = Path(args.repo_list)
    workspace = Path(args.workspace)
    output = Path(args.output)
    since = args.since or ""
    author_emails = {email.lower().strip() for email in args.author_email if email.strip()}

    repos = read_repo_list(repo_list_path)

    if not repos:
        raise RuntimeError(f"No repositories found in {repo_list_path}")

    current_loc_rows: list[dict[str, str | int]] = []
    commit_activity_rows: list[dict[str, str | int]] = []

    for repo in repos:
        print(f"Processing {repo}")
        repo_dir = clone_or_update_repo(repo, workspace)

        current_loc_rows.extend(
            collect_current_loc(
                repo=repo,
                repo_dir=repo_dir,
                run_date=run_date,
            )
        )

        commit_activity_rows.extend(
            collect_commit_activity(
                repo=repo,
                repo_dir=repo_dir,
                run_date=run_date,
                author_emails=author_emails,
                since=args.since,
            )
        )

    current_loc_fields = [
        "run_date",
        "repo",
        "language",
        "files",
        "blank",
        "comment",
        "code",
    ]

    commit_activity_fields = [
        "run_date",
        "repo",
        "commit_date",
        "author_email",
        "author_name",
        "commits",
        "added",
        "deleted",
        "net",
    ]

    run_history_fields = [
        "run_date",
        "run_timestamp_utc",
        "since",
        "author_filter",
        "total_repos",
        "current_files",
        "current_code_lines",
        "commits_since_start",
        "added_since_start",
        "deleted_since_start",
        "net_since_start",
    ]

    repo_history_fields = [
        "run_date",
        "run_timestamp_utc",
        "since",
        "author_filter",
        "repo",
        "current_files",
        "current_code_lines",
        "commits_since_start",
        "added_since_start",
        "deleted_since_start",
        "net_since_start",
    ]

    run_history_rows, repo_history_rows = build_history_rows(
        repos=repos,
        current_loc_rows=current_loc_rows,
        commit_activity_rows=commit_activity_rows,
        run_date=run_date,
        run_timestamp_utc=run_timestamp_utc,
        since=since,
        author_emails=author_emails,
    )

    write_csv(output / "current_loc_by_language.csv", current_loc_rows, current_loc_fields)
    write_csv(output / "commit_activity_by_day.csv", commit_activity_rows, commit_activity_fields)

    append_or_replace_csv(
        output / "run_summary_history.csv",
        run_history_rows,
        run_history_fields,
        key_fields=["run_date", "since", "author_filter"],
    )

    append_or_replace_csv(
        output / "repo_summary_history.csv",
        repo_history_rows,
        repo_history_fields,
        key_fields=["run_date", "since", "author_filter", "repo"],
    )

    print(f"Wrote {output / 'current_loc_by_language.csv'}")
    print(f"Wrote {output / 'commit_activity_by_day.csv'}")
    print(f"Updated {output / 'run_summary_history.csv'}")
    print(f"Updated {output / 'repo_summary_history.csv'}")


if __name__ == "__main__":
    main()
