from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml
from src.cli.batch_compare import main as batch_main


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Run batch comparison from a YAML config.")
    ap.add_argument("config", type=Path, help="Path to YAML config file")
    return ap.parse_args()


def main() -> None:
    args = parse_args()

    with open(args.config, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if not isinstance(cfg, dict):
        raise ValueError("Config must be a YAML mapping")

    required = ["year", "gp", "session", "drivers"]
    missing = [k for k in required if k not in cfg]
    if missing:
        raise ValueError(f"Missing required config keys: {missing}")

    drivers = cfg["drivers"]
    if not isinstance(drivers, list) or len(drivers) < 2:
        raise ValueError("Config key 'drivers' must be a list with at least 2 drivers")

    argv = [
        "batch_compare.py",
        "--year",
        str(cfg["year"]),
        "--gp",
        str(cfg["gp"]),
        "--session",
        str(cfg["session"]),
        "--drivers",
        ",".join(str(d) for d in drivers),
    ]

    if "jobs" in cfg:
        argv += ["--jobs", str(cfg["jobs"])]

    if "out_dir" in cfg:
        argv += ["--out-dir", str(cfg["out_dir"])]

    if "distance_step_m" in cfg:
        argv += ["--distance-step-m", str(cfg["distance_step_m"])]

    if "fuel_coeff" in cfg:
        argv += ["--fuel-coeff", str(cfg["fuel_coeff"])]

    if "write_plots" in cfg:
        if bool(cfg["write_plots"]):
            argv += ["--write-plots"]
        else:
            argv += ["--no-plots"]

    if "config" in cfg:
        argv += ["--config", str(cfg["config"])]

    old_argv = sys.argv[:]
    try:
        sys.argv = argv
        batch_main()
    finally:
        sys.argv = old_argv


if __name__ == "__main__":
    main()
