from __future__ import annotations

from pathlib import Path

import pandas as pd
from src.telemetry.phases import detect_braking_zones
from src.telemetry.resample import resample_by_distance


def main() -> None:
    p = Path("data/processed/sample_2023_Monza_Q_VER_fastest.parquet")
    df = pd.read_parquet(p)

    lap = resample_by_distance(df, distance_step_m=1.0)
    labeled, zones = detect_braking_zones(lap)

    print("Detected braking zones:", len(zones))
    for i, z in enumerate(zones, start=1):
        print(
            f"{i:02d}: {z.start_m:8.1f} m -> {z.end_m:8.1f} m | "
            f"len={z.length_m:6.1f} m | peak dv/dt={z.peak_decel_kph_per_s:8.2f} kph/s"
        )

    out_path = Path("data/processed/monza_2023q_ver_brake_labeled_1m.parquet")
    labeled.to_parquet(out_path, index=False)
    print("Wrote:", out_path)


if __name__ == "__main__":
    main()
