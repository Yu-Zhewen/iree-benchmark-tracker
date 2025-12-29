# IREE Benchmark Tracker

This repository collects performance benchmark data from IREE CI workflows and generates interactive HTML graphs for tracking performance over time.

## Overview

This repository runs a nightly GitHub Actions workflow that:
1. Collects performance artifacts from IREE CI workflows
2. Stores historical data per artifact with commit information in the `data/` directory
3. Generates interactive HTML graphs using Chart.js
4. Publishes the graphs to the `gh-pages` branch for web hosting

The published graphs are available at:

`https://Yu-Zhewen.github.io/iree-benchmark-tracker/data/torch_models_amdgpu_mi325_summary_history.html`

`https://Yu-Zhewen.github.io/iree-benchmark-tracker/data/torch_models_cpu_task_summary_history.html`

## Test Locally

To test the benchmark tracker locally:

1. **Set up the environment:**
   ```bash
   # Clone the repository
   git clone https://github.com/Yu-Zhewen/iree-benchmark-tracker.git
   cd iree-benchmark-tracker

   # Create and activate a virtual environment
   python -m venv .venv
   source .venv/bin/activate
   # Install dependencies
   pip install -r ./scripts/requirements.txt
   ```

2. **Set your GitHub token:**
   ```bash
   export GITHUB_TOKEN='your_token_here'
   ```

3. **Run the test script:**
   ```bash
   ./scripts/test_local.sh
   ```

4. **View the results:**
   - History data: `data/*_history.json`
   - HTML graphs: `data/*.html`
   - Open any HTML file in your browser to view the interactive charts
