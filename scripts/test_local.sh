#!/bin/bash
# Copyright 2025 The IREE Authors
#
# Licensed under the Apache License v2.0 with LLVM Exceptions.
# See https://llvm.org/LICENSE.txt for license information.
# SPDX-License-Identifier: Apache-2.0 WITH LLVM-exception

# Test script for running the benchmark tracker locally

set -e

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Activate virtual environment
source "$REPO_ROOT/venv/bin/activate"

# Check if GITHUB_TOKEN is set
if [ -z "$GITHUB_TOKEN" ]; then
    echo "Error: GITHUB_TOKEN environment variable is not set"
    echo ""
    echo "To set it, run:"
    echo "  export GITHUB_TOKEN='your_token_here'"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p "$REPO_ROOT/data"

echo "Collecting performance data from IREE workflows..."
python "$SCRIPT_DIR/collect.py" \
    --repo-name "iree-org/iree" \
    --branch main \
    --workflow "PkgCI" \
    --output-dir "$REPO_ROOT/data" \
    --days-back 2 \
    --target-artifacts "torch_models_cpu_task_summary.json" "torch_models_amdgpu_mi325_summary.json"

if [ -n "$(ls -A "$REPO_ROOT/data"/*.html 2>/dev/null)" ]; then
    echo ""
    echo "Done! Check the generated files:"
    echo "  - History data: $REPO_ROOT/data/*_history.json"
    echo "  - HTML graphs: $REPO_ROOT/data/*.html"
    echo ""
    echo "To view the graphs, open any $REPO_ROOT/data/*.html file in a browser"
else
    echo "Warning: No data was collected. Check the output above for errors."
fi
