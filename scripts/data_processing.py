#!/usr/bin/env python3
# Copyright 2025 The IREE Authors
#
# Licensed under the Apache License v2.0 with LLVM Exceptions.
# See https://llvm.org/LICENSE.txt for license information.
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

"""Data processing and HTML generation utilities."""

import json
from pathlib import Path
from typing import Dict, List


def process_benchmark_data(json_path: Path, commit_hash: str) -> Dict:
    """Process benchmark JSON and extract performance metrics.

    Expected JSON structure:
    {
        "benchmark": {
            "headers": ["Name", "Current Time (ms)", "Golden Time (ms)", "Status"],
            "rows": [["benchmark_name", "current_time", "golden_time", "PASSED"], ...]
        },
        "compstat": {...},
        "quality": {...}
    }

    Extracted dictionary:
    {
        "commit_hash": commit_hash,
        "time_unit": "ms",
        "tests": [
            {
                "name": benchmark_name,
                "time": execution_time
            }
        ]
    }
    """
    with open(json_path, "r") as f:
        data = json.load(f)

    headers = data["benchmark"]["headers"]
    assert headers[0] == "Name"
    assert headers[1] == "Current Time (ms)"

    results = {
        "commit_hash": commit_hash,
        "time_unit": "ms",
        "tests": [],
    }

    rows = data["benchmark"]["rows"]
    for row in rows:
        # Remove any file extension suffix from test name.
        test_name = Path(row[0]).stem
        results["tests"].append({"name": test_name, "time": row[1]})

    return results


def get_history_file_path(output_dir: Path, artifact_name: str) -> Path:
    """Get the path for a history file given an artifact name."""
    artifact_base = Path(artifact_name).stem
    return output_dir / f"{artifact_base}_history.json"


def sort_and_trim_history(repo, data: List[Dict], max_commits: int) -> None:
    """Sort history by commit timestamp and trim to max_commits entries."""

    # Sort by commit timestamp to match commit history order.
    def get_commit_timestamp(entry):
        commit = repo.get_commit(entry["commit_hash"])
        return commit.commit.author.date

    data.sort(key=get_commit_timestamp)
    # Trim the history to the last max_commits commits.
    data[:] = data[-max_commits:]


def generate_html(history_json_path: Path) -> None:
    """Generate an HTML line chart for the given history JSON file."""

    with open(history_json_path, "r") as f:
        results_history = json.load(f)

    graph_data = {}
    time_unit = "ms"
    for entry in results_history:
        assert time_unit == entry["time_unit"]
        for test in entry["tests"]:
            name = test["name"]
            if name not in graph_data:
                graph_data[name] = {
                    "commit_hashes": [],
                    "time": [],
                }

    for entry in results_history:
        commit_hash = str(entry["commit_hash"])[:7]
        local_tests = dict.fromkeys(graph_data.keys(), None)
        for test in entry["tests"]:
            local_tests[test["name"]] = test
        for test_name, test in local_tests.items():
            graph_data[test_name]["commit_hashes"].append(commit_hash)
            # So that the time/commit horizontal/x axis is consistent
            # across tests, even if a test is missing for a commit,
            # we add time=0 if a test did not run successfully.
            if not test:
                graph_data[test_name]["time"].append(0)
            else:
                graph_data[test_name]["time"].append(test["time"])

    # Start building the HTML content.
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Benchmark Tracker</title>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }
            .chart-container { width: 80%; margin: 30px auto; }
            canvas { width: 100%; height: auto; }
        </style>
    </head>
    <body>
        <h1>Benchmark Tracker</h1>
    """

    # Add a graph for each test
    for test_name, data in graph_data.items():
        html_content += f"""
        <div class="chart-container">
            <h2>{test_name}</h2>"""
        html_content += f"""
            <canvas id="chart-{test_name.replace(' ', '-')}"></canvas>
        </div>
        <script>
            const ctx_{test_name.replace(' ', '_')} = document.getElementById('chart-{test_name.replace(' ', '-')}')
            const chart_{test_name.replace(' ', '_')} = new Chart(ctx_{test_name.replace(' ', '_')}, {{
                type: 'line',
                data: {{
                    labels: {data["commit_hashes"]},  // Truncated commit hashes as X-axis labels
                    datasets: [{{
                        label: 'Time ({time_unit})',
                        data: {data["time"]},   // Test time as Y-axis
                        borderColor: 'rgba(75, 192, 192, 1)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        borderWidth: 2
                    }}]
                }},
                options: {{
                    responsive: true,
                    scales: {{
                        x: {{
                            title: {{
                                display: true,
                                text: 'Commit Hash'
                            }}
                        }},
                        y: {{
                            beginAtZero: true,  // Ensures the Y-axis starts at 0
                            title: {{
                                display: true,
                                text: 'Time ({time_unit})'
                            }}
                        }}
                    }}
                }}
            }});
        </script>
        """

    # Close the HTML content
    html_content += """
    </body>
    </html>
    """

    html_path = history_json_path.with_suffix(".html")
    with open(html_path, "w") as f:
        f.write(html_content)
