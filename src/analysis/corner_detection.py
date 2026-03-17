from __future__ import annotations

import pandas as pd


def detect_segments(
    df: pd.DataFrame,
    *,
    speed_threshold_kph: float = 220.0,
) -> pd.DataFrame:
    """
    Detect straight vs corner segments based on speed.
    """

    required = {"distance_m", "ref_speed_kph", "tgt_speed_kph"}

    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df.copy()

    mean_speed = (df["ref_speed_kph"] + df["tgt_speed_kph"]) / 2

    df["is_straight"] = mean_speed > speed_threshold_kph

    seg_id = 0
    seg_ids = []

    prev = None

    for v in df["is_straight"]:
        if prev is None:
            seg_ids.append(seg_id)
        elif v != prev:
            seg_id += 1
            seg_ids.append(seg_id)
        else:
            seg_ids.append(seg_id)

        prev = v

    df["segment_id"] = seg_ids

    return df
