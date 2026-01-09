from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
from src.telemetry.delta import compute_delta_on_distance_grid
from src.telemetry.resample import resample_by_distance


def run_delta_plot(
    ref_path: Path,
    tgt_path: Path,
    *,
    out_tag: str = "run",
    distance_step_m: float = 1.0,
    out_dir: Path = Path("reports"),
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

    delta = compute_delta_on_distance_grid(ref, tgt)

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

    print(f"Wrote: {out_path}")
    print(f"Final Δlap time (s): {final_delta_s}")

    return final_delta_s


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


# NOTE: run_delta_plot should return final_delta_s as float.
