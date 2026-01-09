from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from src.telemetry.delta import compute_delta_on_distance_grid
from src.telemetry.phases import detect_braking_zones
from src.telemetry.resample import resample_by_distance
from src.telemetry.segments import build_corner_segments


def nearest_delta_at(delta_df: pd.DataFrame, dist_m: float) -> float:
    d = delta_df["distance_m"].to_numpy(dtype=float)
    y = delta_df["delta_time_s"].to_numpy(dtype=float)
    idx = int(np.argmin(np.abs(d - float(dist_m))))
    return float(y[idx])


def main() -> None:
    processed = Path("data/processed")
    out_dir = Path("reports")
    out_dir.mkdir(parents=True, exist_ok=True)

    ref_path = processed / "sample_2023_Monza_Q_VER_fastest.parquet"
    tgt_path = processed / "sample_2023_Monza_Q_LEC_fastest.parquet"

    ref_raw = pd.read_parquet(ref_path)
    tgt_raw = pd.read_parquet(tgt_path)

    # 1) Delta curve (target - reference)
    delta = compute_delta_on_distance_grid(ref_raw, tgt_raw, distance_step_m=1.0)

    # 2) Build segments from reference lap
    ref_rs = resample_by_distance(ref_raw, distance_step_m=1.0)
    labeled, zones = detect_braking_zones(ref_rs)
    segments = build_corner_segments(labeled, zones, exit_len_m=120.0)

    fig_path = out_dir / "delta_time_with_segments.png"

    plt.figure()
    plt.plot(delta["distance_m"], delta["delta_time_s"])
    plt.xlabel("Distance (m)")
    plt.ylabel("ΔTime (s) = target − reference")
    plt.title("Lap ΔTime vs Distance with Corner Segmentation (Monza 2023 Q)")

    for s in segments:
        # Marker lines
        plt.axvline(x=s.brake_start_m, linewidth=0.8)
        plt.axvline(x=s.apex_m, linewidth=0.8)
        plt.axvline(x=s.throttle_on_m, linewidth=0.8)
        plt.axvline(x=s.exit_end_m, linewidth=0.8)

        # Corner label near apex (placed at delta value around apex)
        y = nearest_delta_at(delta, s.apex_m)
        plt.text(s.apex_m, y, f"C{s.corner_id}", fontsize=8)

    plt.tight_layout()
    plt.savefig(fig_path, dpi=200)
    print("Wrote:", fig_path)


if __name__ == "__main__":
    main()
