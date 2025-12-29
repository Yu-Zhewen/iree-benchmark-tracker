#!/usr/bin/env python3
# Copyright 2025 The IREE Authors
#
# Licensed under the Apache License v2.0 with LLVM Exceptions.
# See https://llvm.org/LICENSE.txt for license information.
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

"""GitHub API utilities for downloading workflow artifacts."""

import requests
import sys
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional


def get_workflow_runs(
    repo,
    branch: str,
    workflow_name: str,
    days_back: int,
) -> List:
    """Get workflow runs from the last N days for a specific branch.

    Returns runs sorted by commit timestamp to match commit history order.
    """

    # Find workflow by name.
    workflow = None
    for w in repo.get_workflows():
        if w.name == workflow_name:
            workflow = w
            break

    if workflow is None:
        print(f"Error: Workflow '{workflow_name}' not found")
        sys.exit(1)

    # Get runs from the last N days.
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_back)
    runs = []
    for run in workflow.get_runs(branch=branch):
        if run.created_at >= cutoff_date:
            runs.append(run)
        else:
            break

    return runs


def download_artifact(artifact, download_dir: Path, github_token: str) -> Optional[Path]:
    """Downloads an artifact and returns the path to the downloaded file."""

    try:
        download_url = artifact.archive_download_url
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github+json",
        }
        response = requests.get(download_url, headers=headers, stream=True)
        response.raise_for_status()

        artifact_dir = download_dir / artifact.name
        artifact_dir.mkdir(parents=True, exist_ok=True)
        artifact_path = artifact_dir / "artifact.zip"
        with open(artifact_path, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        return artifact_path
    except Exception as e:
        return None


def extract_json_from_artifact(artifact_path: Path) -> Optional[Path]:
    """Expects a zip file with a single JSON file inside."""

    artifact_dir = artifact_path.parent
    with zipfile.ZipFile(artifact_path, "r") as zip_ref:
        zip_ref.extractall(artifact_dir)

    json_files = list(artifact_dir.rglob("*.json"))
    if json_files:
        return json_files[0]
    else:
        return None
