from __future__ import annotations

import pandas as pd


def estimate_straight_time_loss(
    comparison_df: pd.DataFrame,
    *,
    min_speed_kph: float = 250.0,
) -> float:
    """
    Estimate time loss on high-speed straight sections.

    Expects columns:
      - distance_m
      - ref_time_s
      - tgt_time_s
      - ref_speed_kph
      - tgt_speed_kph

    We define a straight-like region as one where either car is above min_speed_kph.
    Returns the final accumulated delta over those regions.
    """
    required = {
        "distance_m",
        "ref_time_s",
        "tgt_time_s",
        "ref_speed_kph",
        "tgt_speed_kph",
    }
    missing = sorted(required - set(comparison_df.columns))
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = comparison_df.copy()

    mask = (df["ref_speed_kph"] >= min_speed_kph) | (df["tgt_speed_kph"] >= min_speed_kph)
    if not mask.any():
        return 0.0

    straight_df = df.loc[mask].copy()
    straight_df["delta_time_s"] = straight_df["tgt_time_s"] - straight_df["ref_time_s"]

    return float(straight_df["delta_time_s"].iloc[-1] - straight_df["delta_time_s"].iloc[0])
