#!/usr/bin/env python3
"""
Collect code metrics across GitHub repositories.

Outputs:
- data/current_loc_by_language.csv
- data/commit_activity_by_day.csv

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
import os
import shutil
import subprocess
from collections import defaultdict
from datetime import date
from pathlib import Path


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
) -> subprocess.CompletedProcess:
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

    # 1) Try a plain git clone (works for public repos)
    try:
        run_command(["git", "clone", f"https://github.com/{repo}.git", str(repo_dir)])
        return repo_dir
    except RuntimeError:
        # 2) If that fails and we have a GITHUB_TOKEN, try an authenticated clone
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            auth_url = f"https://x-access-token:{token}@github.com/{repo}.git"
            run_command(["git", "clone", auth_url, str(repo_dir)])
            return repo_dir

        # 3) As a last resort, try gh repo clone (may still fail if gh is unauthenticated)
        run_command(["gh", "repo", "clone", repo, str(repo_dir)])
        return repo_dir


def collect_current_loc(repo: str, repo_dir: Path, run_date: str) -> list[dict[str, str | int]]:
    cloc_args = [
        "cloc",
        str(repo_dir),
        "--json",
        f"--exclude-dir={','.join(EXCLUDE_DIRS)}",
    ]

    result = run_command(cloc_args)
    data = json.loads(result.stdout)

    rows: list[dict[str, str | int]] = []

    for language, stats in data.items():
        if language == "header":
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

    # Key: repo, date, author_email, author_name
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


def write_csv(path: Path, rows: list[dict[str, str | int]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def require_tool(name: str) -> None:
    if shutil.which(name) is None:
        raise RuntimeError(f"Required tool not found on PATH: {name}")


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

    run_date = date.today().isoformat()
    repo_list_path = Path(args.repo_list)
    workspace = Path(args.workspace)
    output = Path(args.output)

    author_emails = {email.lower().strip() for email in args.author_email}

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

    write_csv(
        output / "current_loc_by_language.csv",
        current_loc_rows,
        [
            "run_date",
            "repo",
            "language",
            "files",
            "blank",
            "comment",
            "code",
        ],
    )

    write_csv(
        output / "commit_activity_by_day.csv",
        commit_activity_rows,
        [
            "run_date",
            "repo",
            "commit_date",
            "author_email",
            "author_name",
            "commits",
            "added",
            "deleted",
            "net",
        ],
    )

    print(f"Wrote {output / 'current_loc_by_language.csv'}")
    print(f"Wrote {output / 'commit_activity_by_day.csv'}")


if __name__ == "__main__":
    main()