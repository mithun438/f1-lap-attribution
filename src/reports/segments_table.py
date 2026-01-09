from __future__ import annotations

from pathlib import Path

import pandas as pd
from src.telemetry.phases import detect_braking_zones
from src.telemetry.resample import resample_by_distance
from src.telemetry.segments import build_corner_segments


def run_segments_report(
    ref_path: Path,
    *,
    out_tag: str = "run",
    exit_len_m: float = 120.0,
    distance_step_m: float = 1.0,
    out_dir: Path = Path("reports"),
) -> Path:
    """
    Build corner segments from the reference lap and write a CSV table.
    Returns the written CSV path.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    ref_raw = pd.read_parquet(ref_path)
    ref_rs = resample_by_distance(ref_raw, distance_step_m=distance_step_m)
    labeled, zones = detect_braking_zones(ref_rs)
    segments = build_corner_segments(labeled, zones, exit_len_m=exit_len_m)

    rows = []
    for s in segments:
        rows.append(
            {
                "corner_id": s.corner_id,
                "brake_start_m": s.brake_start_m,
                "brake_end_m": s.brake_end_m,
                "apex_m": s.apex_m,
                "throttle_on_m": s.throttle_on_m,
                "exit_end_m": s.exit_end_m,
                "entry_speed_kph": s.entry_speed_kph,
                "min_speed_kph": s.min_speed_kph,
                "exit_speed_kph": s.exit_speed_kph,
                "segment_time_s": s.segment_time_s,
            }
        )

    df = pd.DataFrame(rows).sort_values("corner_id").reset_index(drop=True)

    out_csv = out_dir / f"{out_tag}_segments.csv"
    df.to_csv(out_csv, index=False)

    print(f"Braking zones: {len(zones)}")
    print(f"Segments: {len(df)}")
    print("Wrote:", out_csv)
    print(df)

    return out_csv


def main() -> None:
    processed = Path("data/processed")
    ref_path = processed / "sample_2023_Monza_Q_VER_fastest.parquet"

    out = run_segments_report(
        ref_path, out_tag="monza_2023q_ver", exit_len_m=120.0, distance_step_m=1.0
    )

    # Preserve legacy filename for README stability
    legacy = Path("reports/monza_2023q_ver_segments.csv")
    if out != legacy:
        legacy.write_bytes(out.read_bytes())


if __name__ == "__main__":
    main()
