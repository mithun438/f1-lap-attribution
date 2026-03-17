from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


def find_ranked_summaries(reports_dir: Path) -> list[Path]:
    return sorted(reports_dir.glob("*/batch_summary_ranked.csv"))


def load_all_summaries(reports_dir: Path) -> pd.DataFrame:
    files = find_ranked_summaries(reports_dir)
    if not files:
        raise FileNotFoundError("No batch_summary_ranked.csv files found")

    dfs = []
    for f in files:
        df = pd.read_csv(f)
        df["run_dir"] = f.parent.name
        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def main() -> None:
    reports_dir = Path("reports")
    out_dir = reports_dir / "validation"
    out_dir.mkdir(parents=True, exist_ok=True)

    df = load_all_summaries(reports_dir)

    required = {"delta_lap_time_s", "straight_time_loss_s"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    # Save merged validation table
    out_csv = out_dir / "physics_validation.csv"
    df.to_csv(out_csv, index=False)
    print(f"Wrote: {out_csv}")

    # Scatter plot
    plt.figure()
    plt.scatter(df["straight_time_loss_s"], df["delta_lap_time_s"])
    plt.xlabel("Straight time loss (s)")
    plt.ylabel("Delta lap time (s)")
    plt.title("Straight-loss metric vs lap delta")

    out_png = out_dir / "physics_validation_scatter.png"
    plt.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close()
    print(f"Wrote: {out_png}")

    # Correlation
    corr = df["straight_time_loss_s"].corr(df["delta_lap_time_s"])
    out_txt = out_dir / "physics_validation_summary.txt"
    out_txt.write_text(f"correlation={corr}\n", encoding="utf-8")
    print(f"Wrote: {out_txt}")


if __name__ == "__main__":
    main()
