# Pipeline

## Purpose

This document describes how to run the telemetry-analysis pipeline and what outputs are generated.

The project supports:
- single-driver-pair comparison
- batch comparisons
- config-driven runs
- multi-config execution

---

## 1. Single comparison

Example:

```bash
python src/cli/run_pipeline.py --year 2023 --gp Italy --session Q --ref VER --tgt LEC --out-tag demo
```
This generates a comparison for a single driver pair.

Typical outputs:
    - raw delta plot
    - fuel-corrected delta plot (if fuel args are provided)
    - comparison CSV
    - HTML report

## 2. Batch comparison

Example: 

```bash
python src/cli/batch_compare.py --year 2023 --gp Italy --session Q --drivers VER,LEC,SAI --jobs 2
```
This runs all pairwise comparisons between the listed drivers.

For VER,LEC,SAI, the system generates:
    - VER vs LEC
    - VER vs SAI
    - LEC vs SAI

Typical outputs:
    - batch_summary.csv
    - batch_summary_ranked.csv
    - per-comparison CSVs
    - per-comparison HTML reports
    - batch index.html

## 3. No-plots mode

Example: 

```bash
python src/cli/batch_compare.py --year 2023 --gp Italy --session Q --drivers VER,LEC,SAI --jobs 2 --no-plots
```

This keeps analysis and exports but avoids PNG generation.

Useful for:
    - faster runs
    - CI
    - experimentation
    - batch scaling

## 4. Config driven execution

Example: 

```bash
python src/cli/run_from_config.py config/run_italy_q.yaml
```

Example config: 

```bash
year: 2023
gp: Italy
session: Q

drivers:
  - VER
  - LEC
  - SAI

jobs: 2
write_plots: false
fuel_coeff: 0.03
distance_step_m: 1.0
config: config/default.yaml
```

This enables reproducible run definitions.

## 5. Multi-config execution

Example: 

```bash
python src/cli/run_many_configs.py config/runs.yaml
```

Example multi-config file:

```bash
runs:
  - config/run_italy_q.yaml
  - config/run_spain_q.yaml
```

This allows multiple sessions or races to be processed in sequence.

Output layout: 

A typical output folder looks like:

```bash
reports/2023_Italy_Q/
├── batch_summary.csv
├── batch_summary_ranked.csv
├── index.html
├── batch_VER_vs_LEC_report.html
├── batch_VER_vs_LEC_comparison_table.csv
├── batch_VER_vs_LEC_delta_time_vs_distance.png
├── batch_VER_vs_LEC_delta_time_vs_distance_fuel_corrected.png
└── _cache/
```

Output meanings:
    - batch_summary.csv: Structured summary of all pairwise comparisons.

        Typical columns:
            ref
            tgt
            delta_lap_time_s
            ref_lap_time_s
            tgt_lap_time_s
            fuel_corrected_delta_s
            straight_time_loss_s
            batch_summary_ranked.csv
            - Same data as batch summary, but sorted by absolute lap delta.
            - Useful for identifying the largest performance gaps quickly.

    - *_comparison_table.csv: Distance-aligned telemetry comparison table.

        Typical columns:
            distance_m
            ref_time_s
            tgt_time_s
            delta_time_s
            ref_speed_kph
            tgt_speed_kph
            ref_throttle
            tgt_throttle
            ref_brake
            tgt_brake

    - *_report.html

        Per-comparison report containing:
        - summary metrics
        - raw delta plot
        - optional fuel-corrected plot
        - comparison table preview

    - index.html

        Batch-level navigation page linking:
        - summaries
        - comparison reports
        - comparison CSVs

Validation and analysis: 

    - The pipeline also supports follow-up validation workflows, such as:
        - ranked summary comparison
        - straight-line metric validation
        - future notebook or script-based cross-run analysis

Recommended usage flow:
    - Start with a batch comparison
    - Inspect batch_summary_ranked.csv
    - Open index.html
    - Drill into a single comparison report
    - Use comparison CSVs for deeper analysis or dashboards
