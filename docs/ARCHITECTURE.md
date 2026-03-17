# Architecture

## Overview

This project is a telemetry-driven lap comparison and attribution pipeline built around FastF1 data.

The system is designed as a modular engineering workflow with four main layers:

1. **Data ingestion**
2. **Telemetry alignment and analysis**
3. **Report and export generation**
4. **Visualization and dashboard consumption**

The goal is not to reproduce proprietary Formula 1 tooling, but to build a clean, reproducible telemetry-analysis system with strong software engineering structure.

---

## High-level flow

```text
FastF1 session data
    ↓
fastest lap extraction
    ↓
parquet telemetry traces
    ↓
distance-based resampling
    ↓
delta + comparison metrics
    ↓
CSV / HTML / PNG exports
    ↓
dashboard + manual analysis
```

## Module layout

src/data/ - Responsible for ingestion and raw lap extraction.

fastf1_utils.py

    - loads FastF1 sessions
    - extracts fastest lap pair
    - writes processed telemetry traces to parquet
    - supports cache directory routing

src/telemetry/ - Responsible for alignment, metric computation, and analysis logic.

Typical responsibilities include:

    - distance-based resampling
    - delta trace computation
    - fuel correction logic
    - straight-line physics-inspired metric
    - helper utilities for comparison and transformation

Examples:

    - resample.py
    - delta_trace.py
    - fuel_curve.py
    - physics.py
    
This layer should remain computation-focused and avoid visualization concerns.
    - src/reports/ 
        - Responsible for creating artifacts and reports.
        Examples:
            - delta plots
            - comparison table CSV exports
            - HTML comparison reports
            - HTML batch index pages
        Examples:
            - plot_delta_time.py
            - export_comparison_table.py
            - html_report.py
            - html_index.py

This layer consumes computed outputs and turns them into user-facing artifacts.
    - src/cli/
        - Responsible for orchestration.

        Execution modes include:
            - run_pipeline.py: single comparison entrypoint
            - batch_compare.py: multiple pairwise comparisons
            - run_from_config.py: config-driven single run
            - run_many_configs.py: batch pipeline over multiple configs

This layer is the control surface of the system.
    - dashboard.py
      - A lightweight Streamlit viewer that reads generated outputs from the reports/ directory.
      - It is intentionally separate from the core pipeline so that:
        - report generation stays deterministic
        - dashboard remains read-only
      - UI concerns do not leak into analysis code

## Execution modes:
    - Single comparison
        - Used for focused lap analysis between two drivers.
    - Batch comparison
        - Used for all-vs-all style comparisons over a selected driver set.
    - Config-driven execution
        - Used for reproducible runs with predefined settings.
    - Multi-config execution
        - Used for running multiple race/session configs in sequence.

## Output structure

A typical batch run produces: 

```bash
reports/2023_Italy_Q/
├── batch_summary.csv
├── batch_summary_ranked.csv
├── index.html
├── batch_VER_vs_LEC_report.html
├── batch_VER_vs_LEC_comparison_table.csv
├── batch_VER_vs_LEC_delta_time_vs_distance.png
└── _cache/
```

## Design principles
1. Reproducibility
    - Runs should be executable from config or CLI with deterministic output structure.

2. Separation of concerns
    - telemetry computation lives in src/telemetry/
    - artifact generation lives in src/reports/
    - orchestration lives in src/cli/

3. Batch scalability
    - Batch mode and parallel execution are first-class workflow paths, not afterthoughts.

4. Reportability
    - The system should produce outputs that are useful both for manual review and future dashboards.

5. Extensibility
    - New metrics, correction models, reports, or session-level analyses should be addable without breaking the core structure.

## Current limitations

- Fuel correction is heuristic and not a complete physical model
- Straight-line metric is a simplified proxy, not a validated race-engineering model
- The dashboard is read-only and not a full telemetry exploration UI
- No live telemetry ingestion or streaming mode exists yet

## Future extensions

    - Potential next steps include:
        - sector-level or corner-level attribution exports
        - richer vehicle dynamics modeling
        - multi-session benchmarking
        - experiment runners for parameter sweeps
        - full dashboard navigation across reports and plots
        - publishable demo deployment