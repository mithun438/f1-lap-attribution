from __future__ import annotations

import pandas as pd


def summarize_segments(
    df: pd.DataFrame,
    *,
    segment_length_m: float = 100.0,
) -> pd.DataFrame:
    """
    Split lap into fixed-length segments and summarize delta.
    """

    required = {
        "distance_m",
        "delta_time_s",
        "ref_speed_kph",
        "tgt_speed_kph",
    }

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df.copy()

    df["segment_id"] = (df["distance_m"] // segment_length_m).astype(int)

    rows = []

    for seg, g in df.groupby("segment_id"):
        row = {
            "segment_id": int(seg),
            "distance_start": float(g["distance_m"].iloc[0]),
            "distance_end": float(g["distance_m"].iloc[-1]),
            "delta_time_s": float(g["delta_time_s"].iloc[-1] - g["delta_time_s"].iloc[0]),
            "mean_speed_diff_kph": float((g["tgt_speed_kph"] - g["ref_speed_kph"]).mean()),
        }

        rows.append(row)

    return pd.DataFrame(rows)
