from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from src.telemetry.delta import compute_delta_on_distance_grid


def main() -> None:
    processed = Path("data/processed")
    ref_path = processed / "sample_2023_Monza_Q_VER_fastest.parquet"
    tgt_path = processed / "sample_2023_Monza_Q_LEC_fastest.parquet"  # change if needed

    ref = pd.read_parquet(ref_path)
    tgt = pd.read_parquet(tgt_path)

    delta = compute_delta_on_distance_grid(ref, tgt, distance_step_m=1.0)

    out_dir = Path("reports")
    out_dir.mkdir(exist_ok=True)
    fig_path = out_dir / "delta_time_vs_distance.png"

    plt.figure()
    plt.plot(delta["distance_m"], delta["delta_time_s"])
    plt.xlabel("Distance (m)")
    plt.ylabel("ΔTime (s) = target - reference")
    plt.title("Lap Delta Time vs Distance (Monza 2023 Q)")
    plt.tight_layout()
    plt.savefig(fig_path, dpi=200)
    print("Wrote:", fig_path)

    # Print final lap delta (end of lap)
    print("Final Δlap time (s):", float(delta["delta_time_s"].iloc[-1]))


if __name__ == "__main__":
    main()
