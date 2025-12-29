#!/usr/bin/env python3
# Copyright 2025 The IREE Authors
#
# Licensed under the Apache License v2.0 with LLVM Exceptions.
# See https://llvm.org/LICENSE.txt for license information.
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

"""Main script to collect benchmark data from GitHub workflow artifacts."""

import argparse
import json
import os
import sys
import tempfile
from github import Github, Auth
from pathlib import Path
from typing import List

from data_processing import (
    generate_html,
    get_history_file_path,
    process_benchmark_data,
    sort_and_trim_history,
)
from github_utils import (
    download_artifact,
    extract_json_from_artifact,
    get_workflow_runs,
)


def collect_data_from_artifacts(
    repo_name: str,
    branch: str,
    workflow: str,
    token: str,
    output_dir: Path,
    days_back: int,
    target_artifacts: List[str],
    max_commits: int,
) -> List[Path]:
    """Collect benchmark data from GitHub workflow artifacts and update history files.

    Processes workflow runs from the specified repository, branch, and workflow
    that occurred within the last `days_back` days. For each run, downloads and
    processes artifacts matching the `target_artifacts` list. New benchmark data
    is appended to existing history files (one per artifact), skipping commits
    that have already been processed. History files are sorted by commit timestamp
    and trimmed to keep only the most recent `max_commits` entries.

    Args:
        repo_name: GitHub repository name (e.g., "iree-org/iree")
        branch: Branch name to collect data from
        workflow: Workflow name to collect runs from
        token: GitHub authentication token
        output_dir: Directory where history files will be saved
        days_back: Number of days to look back for workflow runs
        target_artifacts: List of artifact names to collect data from
        max_commits: Maximum number of commits to keep in each history file

    Returns:
        List of Path objects pointing to the updated history files (one per artifact)
    """

    g = Github(auth=Auth.Token(token))
    repo = g.get_repo(repo_name)
    runs = get_workflow_runs(repo, branch, workflow, days_back)
    print(f"Found {len(runs)} completed runs on {branch} branch")

    output_dir.mkdir(parents=True, exist_ok=True)
    # Stores existing data/commits for each artifact.name.
    history_data = {}
    history_commits = {}

    for run in runs:
        commit_hash = run.head_sha[:8]
        print(f"  Processing run {run.id} (commit {commit_hash})")

        artifacts = list(run.get_artifacts())
        print(f"    Found {len(artifacts)} artifacts")

        for artifact in artifacts:
            # Check if this is a benchmark artifact we care about.
            if artifact.name not in target_artifacts:
                continue

            # Load history data if it exists.
            if artifact.name not in history_data:
                history_json_path = get_history_file_path(output_dir, artifact.name)
                if history_json_path.exists():
                    with open(history_json_path, "r") as f:
                        history_data[artifact.name] = json.load(f)
                    history_commits[artifact.name] = [
                        entry["commit_hash"] for entry in history_data[artifact.name]
                    ]
                else:
                    history_data[artifact.name] = []
                    history_commits[artifact.name] = []

            # Check if the commit has already been processed.
            if commit_hash in history_commits[artifact.name]:
                continue

            # Download the new data and process it.
            print(f"    Downloading artifact: {artifact.name}")
            with tempfile.TemporaryDirectory() as tmpdir:
                artifact_path = download_artifact(artifact, Path(tmpdir), token)
                if not artifact_path:
                    print(f"    Error: Failed to download artifact {artifact.name}")
                    sys.exit(1)

                json_path = extract_json_from_artifact(artifact_path)
                if not json_path:
                    print(f"    Error: Failed to extract JSON from artifact {artifact.name}")
                    sys.exit(1)

                result = process_benchmark_data(json_path, commit_hash)
                history_data[artifact.name].append(result)

    history_files = []
    for artifact_name, history_data in history_data.items():
        sort_and_trim_history(repo, history_data, max_commits)
        history_json_path = get_history_file_path(output_dir, artifact_name)
        with open(history_json_path, "w") as f:
            json.dump(history_data, f, indent=2)
        history_files.append(history_json_path)

    return history_files


def main():
    parser = argparse.ArgumentParser(description="Collect benchmark data from IREE workflows")

    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("./data"),
        help="Output directory for collected data",
    )

    parser.add_argument(
        "--github-token",
        default=os.environ.get("GITHUB_TOKEN"),
        help="GitHub token (default: from GITHUB_TOKEN env var)",
    )

    parser.add_argument(
        "--repo-name",
        type=str,
        required=True,
        help="Repository name to collect data from",
    )

    parser.add_argument(
        "--branch",
        type=str,
        required=True,
        help="Branch to collect data from",
    )

    parser.add_argument(
        "--workflow",
        type=str,
        required=True,
        help="Workflow to collect data from",
    )

    parser.add_argument(
        "--days-back",
        type=int,
        required=True,
        help="Number of days back to collect data from",
    )

    parser.add_argument(
        "--max-commits",
        type=int,
        default=200,
        help="Maximum number of commits to be tracked",
    )

    parser.add_argument(
        "--target-artifacts",
        nargs="+",
        required=True,
        help="List of artifacts to collect data from",
    )

    args = parser.parse_args()

    if not args.github_token:
        print("Error: GITHUB_TOKEN environment variable not set")
        sys.exit(1)

    data_files = collect_data_from_artifacts(
        token=args.github_token,
        output_dir=args.output_dir,
        days_back=args.days_back,
        repo_name=args.repo_name,
        branch=args.branch,
        workflow=args.workflow,
        target_artifacts=args.target_artifacts,
        max_commits=args.max_commits,
    )

    for data_file in data_files:
        generate_html(data_file)


if __name__ == "__main__":
    main()
