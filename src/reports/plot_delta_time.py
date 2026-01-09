from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from src.telemetry.delta import compute_delta_on_distance_grid


def run_delta_plot(
    ref_path: Path,
    tgt_path: Path,
    *,
    out_tag: str = "run",
    distance_step_m: float = 1.0,
    out_dir: Path = Path("reports"),
) -> Path:
    """
    Generate Δtime vs distance plot for target − reference laps.
    Returns the written PNG path.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    ref = pd.read_parquet(ref_path)
    tgt = pd.read_parquet(tgt_path)

    delta = compute_delta_on_distance_grid(ref, tgt, distance_step_m=distance_step_m)

    out_png = out_dir / f"{out_tag}_delta_time_vs_distance.png"

    plt.figure()
    plt.plot(delta["distance_m"], delta["delta_time_s"])
    plt.xlabel("Distance (m)")
    plt.ylabel("ΔTime (s) = target − reference")
    plt.title("Lap ΔTime vs Distance")
    plt.tight_layout()
    plt.savefig(out_png, dpi=200)

    # Print useful summary (keeps prior behavior)
    final_dt = float(delta["delta_time_s"].iloc[-1])
    print("Wrote:", out_png)
    print("Final Δlap time (s):", final_dt)

    return out_png


def main() -> None:
    processed = Path("data/processed")
    ref_path = processed / "sample_2023_Monza_Q_VER_fastest.parquet"
    tgt_path = processed / "sample_2023_Monza_Q_LEC_fastest.parquet"

    # Backward-compatible default output name (matches earlier file)
    # If you want it tagged, call run_delta_plot from CLI.
    out = run_delta_plot(ref_path, tgt_path, out_tag="delta_time", distance_step_m=1.0)

    # Preserve your legacy filename for README stability
    legacy = Path("reports/delta_time_vs_distance.png")
    if out != legacy:
        legacy.write_bytes(out.read_bytes())


if __name__ == "__main__":
    main()
