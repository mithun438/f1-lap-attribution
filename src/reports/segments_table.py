from __future__ import annotations

from pathlib import Path

import pandas as pd
from src.telemetry.phases import detect_braking_zones
from src.telemetry.resample import resample_by_distance
from src.telemetry.segments import build_corner_segments


def main() -> None:
    raw_path = Path("data/processed/sample_2023_Monza_Q_VER_fastest.parquet")
    df = pd.read_parquet(raw_path)

    lap = resample_by_distance(df, distance_step_m=1.0)
    labeled, zones = detect_braking_zones(lap)

    segments = build_corner_segments(labeled, zones, exit_len_m=120.0)

    out = pd.DataFrame([s.__dict__ for s in segments])
    out_path = Path("reports/monza_2023q_ver_segments.csv")
    out.to_csv(out_path, index=False)

    print("Braking zones:", len(zones))
    print("Segments:", len(segments))
    print("Wrote:", out_path)
    print(out)


if __name__ == "__main__":
    main()
