from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from src.telemetry.delta_trace import compute_delta_trace_from_traces
from src.telemetry.fuel_curve import apply_fuel_correction_ramp
from src.telemetry.resample import resample_by_distance


def run_delta_plot(
    ref_path: Path,
    tgt_path: Path,
    *,
    out_tag: str = "run",
    distance_step_m: float = 1.0,
    out_dir: Path = Path("reports"),
    applied_correction_s: float | None = None,
) -> float:
    """
    Compute and plot lap delta time vs distance.
    Returns the final lap delta (seconds): target - reference.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    ref_raw = pd.read_parquet(ref_path)
    tgt_raw = pd.read_parquet(tgt_path)

    ref = resample_by_distance(ref_raw, distance_step_m=distance_step_m)
    tgt = resample_by_distance(tgt_raw, distance_step_m=distance_step_m)

    # compute layer expects traces with ['distance_m', 'time_s']
    # Your resampled frames likely have lap_time_s, so normalize.
    ref2 = ref.rename(columns={"lap_time_s": "time_s"}) if "time_s" not in ref.columns else ref
    tgt2 = tgt.rename(columns={"lap_time_s": "time_s"}) if "time_s" not in tgt.columns else tgt

    required = {"distance_m", "time_s"}
    missing_ref = sorted(required - set(ref2.columns))
    missing_tgt = sorted(required - set(tgt2.columns))
    if missing_ref:
        raise ValueError(f"ref trace missing columns: {missing_ref}")
    if missing_tgt:
        raise ValueError(f"tgt trace missing columns: {missing_tgt}")

    delta = compute_delta_trace_from_traces(
        ref2[["distance_m", "time_s"]],
        tgt2[["distance_m", "time_s"]],
        distance_step_m=distance_step_m,
    )

    final_delta_s = float(delta["delta_time_s"].iloc[-1])

    # Plot
    plt.figure(figsize=(10, 4))
    plt.plot(delta["distance_m"], delta["delta_time_s"], label="Δtime (tgt - ref)")
    plt.axhline(0.0, color="black", linewidth=0.8)
    plt.xlabel("Distance (m)")
    plt.ylabel("Δtime (s)")
    plt.title("Lap delta vs distance")
    plt.legend()
    plt.tight_layout()

    out_path = out_dir / f"{out_tag}_delta_time_vs_distance.png"
    plt.savefig(out_path, dpi=150)
    plt.close()

    # Optional: write a second plot with a distance-ramped fuel correction.
    if applied_correction_s is not None:
        delta_fc = apply_fuel_correction_ramp(delta, applied_correction_s=applied_correction_s)

        plt.figure()
        plt.plot(delta_fc["distance_m"], delta_fc["delta_time_s"], label="raw")
        plt.plot(delta_fc["distance_m"], delta_fc["delta_time_s_corrected"], label="fuel-corrected")
        plt.xlabel("Distance (m)")
        plt.ylabel("Δtime (s) [tgt - ref]")
        plt.title(f"Δtime vs distance (fuel-corrected ramp) | {out_tag}")
        plt.legend()

        out_path_fc = out_dir / f"{out_tag}_delta_time_vs_distance_fuel_corrected.png"
        plt.savefig(out_path_fc, dpi=200, bbox_inches="tight")
        print(f"Wrote: {out_path_fc}")

    print(f"Wrote: {out_path}")
    print(f"Final Δlap time (s): {final_delta_s}")

    return final_delta_s


def main() -> None:
    processed = Path("data/processed")
    ref_path = processed / "sample_2023_Monza_Q_VER_fastest.parquet"
    tgt_path = processed / "sample_2023_Monza_Q_LEC_fastest.parquet"

    # Backward-compatible default output name (matches earlier file)
    # If you want it tagged, call run_delta_plot from CLI.
    # run_delta_plot now returns the final lap delta (float), not the
    # path of the generated plot.
    final_delta = run_delta_plot(ref_path, tgt_path, out_tag="delta_time", distance_step_m=1.0)

    # Preserve your legacy filename for README stability.  The generated
    # plot is written inside `run_delta_plot` using the same logic, so
    # reconstruct the path here rather than trying to reuse the return
    # value.
    legacy = Path("reports/delta_time_vs_distance.png")
    new_plot = Path("reports") / "delta_time_delta_time_vs_distance.png"
    if new_plot != legacy:
        legacy.write_bytes(new_plot.read_bytes())

    # optional logging of the returned delta
    print(f"run_delta_plot returned final delta: {final_delta}")


if __name__ == "__main__":
    main()


# NOTE: run_delta_plot should return final_delta_s as float.
