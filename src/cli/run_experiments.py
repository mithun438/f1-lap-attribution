from __future__ import annotations

import argparse
from itertools import product
from pathlib import Path

import pandas as pd
import yaml
from src.cli.batch_compare import main as batch_main


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run experiment grid from YAML config.")
    ap.add_argument("config", type=Path, help="Path to experiment YAML config")
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if not isinstance(cfg, dict):
        raise ValueError("Experiment config must be a YAML mapping")

    required = ["year", "gp", "session", "drivers", "experiments"]
    missing = [k for k in required if k not in cfg]
    if missing:
        raise ValueError(f"Missing required keys: {missing}")

    exp = cfg["experiments"]
    if not isinstance(exp, dict):
        raise ValueError("'experiments' must be a mapping")

    distance_steps = exp.get("distance_step_m", [1.0])
    fuel_coeffs = exp.get("fuel_coeff", [0.03])
    jobs = int(cfg.get("jobs", 1))
    write_plots = bool(cfg.get("write_plots", False))

    rows: list[dict] = []

    import sys

    for i, (distance_step_m, fuel_coeff) in enumerate(
        product(distance_steps, fuel_coeffs), start=1
    ):
        out_dir = (
            Path("reports")
            / "experiments"
            / f"{cfg['year']}_{cfg['gp'].replace(' ', '_')}_{cfg['session']}"
            / f"dstep_{distance_step_m}_fuel_{fuel_coeff}"
        )

        argv = [
            "batch_compare.py",
            "--year",
            str(cfg["year"]),
            "--gp",
            str(cfg["gp"]),
            "--session",
            str(cfg["session"]),
            "--drivers",
            ",".join(str(d) for d in cfg["drivers"]),
            "--jobs",
            str(jobs),
            "--distance-step-m",
            str(distance_step_m),
            "--fuel-coeff",
            str(fuel_coeff),
            "--out-dir",
            str(out_dir),
        ]

        if write_plots:
            argv += ["--write-plots"]
        else:
            argv += ["--no-plots"]

        print(
            f"[{i}] running experiment: distance_step_m={distance_step_m}, fuel_coeff={fuel_coeff}"
        )

        old_argv = sys.argv[:]
        try:
            sys.argv = argv
            batch_main()
        finally:
            sys.argv = old_argv

        ranked_csv = out_dir / "batch_summary_ranked.csv"
        summary_csv = out_dir / "batch_summary.csv"
        chosen = ranked_csv if ranked_csv.exists() else summary_csv

        if chosen.exists():
            df = pd.read_csv(chosen)
            mean_abs_delta = (
                float(df["abs_delta_lap_time_s"].mean())
                if "abs_delta_lap_time_s" in df.columns
                else None
            )
            rows.append(
                {
                    "distance_step_m": distance_step_m,
                    "fuel_coeff": fuel_coeff,
                    "out_dir": str(out_dir),
                    "summary_csv": str(chosen),
                    "mean_abs_delta_lap_time_s": mean_abs_delta,
                    "num_pairs": int(len(df)),
                }
            )

    if rows:
        out_root = Path("reports") / "experiments"
        out_root.mkdir(parents=True, exist_ok=True)
        out_csv = out_root / "experiment_summary.csv"
        pd.DataFrame(rows).to_csv(out_csv, index=False)
        print(f"Wrote: {out_csv}")


if __name__ == "__main__":
    main()
