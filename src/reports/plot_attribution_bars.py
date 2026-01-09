from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def run_attribution_bar_plot(
    *,
    out_tag: str = "run",
    in_dir: Path = Path("reports"),
    out_dir: Path = Path("reports"),
) -> Path:
    """
    Create stacked bars per corner for braking/mid-corner/traction losses.
    Reads:  {in_dir}/{out_tag}_attribution_v2.csv
    Writes: {out_dir}/{out_tag}_attribution_stacked_bars.png
    """
    in_csv = in_dir / f"{out_tag}_attribution_v2.csv"
    if not in_csv.exists():
        raise FileNotFoundError(f"Missing expected file: {in_csv}. Run attribution_table.py first.")

    df = pd.read_csv(in_csv)
    required = ["corner_id", "loss_braking_s", "loss_midcorner_s", "loss_traction_s"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"CSV missing required columns: {missing}")

    df = df.sort_values("corner_id").reset_index(drop=True)

    corners = [f"C{int(x)}" for x in df["corner_id"].tolist()]
    braking = df["loss_braking_s"].to_numpy(dtype=float)
    mid = df["loss_midcorner_s"].to_numpy(dtype=float)
    traction = df["loss_traction_s"].to_numpy(dtype=float)

    x = np.arange(len(corners))

    out_dir.mkdir(parents=True, exist_ok=True)
    out_png = out_dir / f"{out_tag}_attribution_stacked_bars.png"

    plt.figure()
    plt.bar(x, braking, label="Braking")
    plt.bar(x, mid, bottom=braking, label="Mid-corner")
    plt.bar(x, traction, bottom=braking + mid, label="Traction/exit")
    plt.xticks(x, corners)
    plt.ylabel("ΔTime contribution (s)")
    plt.title("Corner Loss Breakdown (Target − Reference)")
    plt.axhline(0.0, linewidth=0.8)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)

    print("Wrote:", out_png)
    return out_png


def main() -> None:
    # Backward-compatible behavior for your Monza example:
    out = run_attribution_bar_plot(out_tag="monza_2023q_ver_vs_lec")

    # Preserve legacy filename for README stability
    legacy = Path("reports/attribution_stacked_bars.png")
    if out != legacy:
        legacy.write_bytes(out.read_bytes())


if __name__ == "__main__":
    main()
