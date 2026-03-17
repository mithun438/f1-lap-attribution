from __future__ import annotations

import argparse
from pathlib import Path

import yaml
from src.cli.run_from_config import main as run_one_config


def parse_args():
    ap = argparse.ArgumentParser(description="Run multiple YAML configs")
    ap.add_argument("config", type=Path, help="Path to runs.yaml")
    return ap.parse_args()


def main():
    args = parse_args()

    with open(args.config, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if "runs" not in data:
        raise ValueError("runs.yaml must contain 'runs' list")

    runs = data["runs"]

    if not isinstance(runs, list):
        raise ValueError("'runs' must be a list")

    for i, cfg_path in enumerate(runs, start=1):
        cfg_path = Path(cfg_path)

        print(f"\n=== Run {i}/{len(runs)}: {cfg_path} ===\n")

        import sys

        old_argv = sys.argv[:]
        try:
            sys.argv = ["run_from_config.py", str(cfg_path)]
            run_one_config()
        finally:
            sys.argv = old_argv


if __name__ == "__main__":
    main()
