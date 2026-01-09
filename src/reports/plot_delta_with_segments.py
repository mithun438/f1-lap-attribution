from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from src.telemetry.delta import compute_delta_on_distance_grid
from src.telemetry.phases import detect_braking_zones
from src.telemetry.resample import resample_by_distance
from src.telemetry.segments import build_corner_segments


def _nearest_delta_at(delta_df: pd.DataFrame, dist_m: float) -> float:
    d = delta_df["distance_m"].to_numpy(dtype=float)
    y = delta_df["delta_time_s"].to_numpy(dtype=float)
    idx = int(np.argmin(np.abs(d - float(dist_m))))
    return float(y[idx])


def run_delta_with_segments_plot(
    ref_path: Path,
    tgt_path: Path,
    *,
    out_tag: str = "run",
    distance_step_m: float = 1.0,
    exit_len_m: float = 120.0,
    out_dir: Path = Path("reports"),
) -> Path:
    """
    Plot Δtime(s) with vertical markers at brake_start/apex/throttle_on/exit_end for each corner.
    Returns the written PNG path.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    ref_raw = pd.read_parquet(ref_path)
    tgt_raw = pd.read_parquet(tgt_path)

    delta = compute_delta_on_distance_grid(ref_raw, tgt_raw, distance_step_m=distance_step_m)

    ref_rs = resample_by_distance(ref_raw, distance_step_m=distance_step_m)
    labeled, zones = detect_braking_zones(ref_rs)
    segments = build_corner_segments(labeled, zones, exit_len_m=exit_len_m)

    out_png = out_dir / f"{out_tag}_delta_time_with_segments.png"

    plt.figure()
    plt.plot(delta["distance_m"], delta["delta_time_s"])
    plt.xlabel("Distance (m)")
    plt.ylabel("ΔTime (s) = target − reference")
    plt.title("Lap ΔTime vs Distance with Corner Segmentation")

    for s in segments:
        plt.axvline(x=s.brake_start_m, linewidth=0.8)
        plt.axvline(x=s.apex_m, linewidth=0.8)
        plt.axvline(x=s.throttle_on_m, linewidth=0.8)
        plt.axvline(x=s.exit_end_m, linewidth=0.8)

        y = _nearest_delta_at(delta, s.apex_m)
        plt.text(s.apex_m, y, f"C{s.corner_id}", fontsize=8)

    plt.tight_layout()
    plt.savefig(out_png, dpi=200)
    print("Wrote:", out_png)
    return out_png


def main() -> None:
    processed = Path("data/processed")
    ref_path = processed / "sample_2023_Monza_Q_VER_fastest.parquet"
    tgt_path = processed / "sample_2023_Monza_Q_LEC_fastest.parquet"

    out = run_delta_with_segments_plot(
        ref_path, tgt_path, out_tag="delta", distance_step_m=1.0, exit_len_m=120.0
    )

    # Preserve legacy filename for README stability
    legacy = Path("reports/delta_time_with_segments.png")
    if out != legacy:
        legacy.write_bytes(out.read_bytes())


if __name__ == "__main__":
    main()
