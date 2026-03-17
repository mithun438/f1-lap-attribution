# src/telemetry/fuel_curve.py
from __future__ import annotations

import pandas as pd


def apply_fuel_correction_ramp(
    delta_df: pd.DataFrame, *, applied_correction_s: float
) -> pd.DataFrame:
    """
    Apply a simple distance-ramped fuel correction to a delta trace.

    We treat fuel correction as a uniform lap-time effect and distribute it
    linearly over distance:

        delta_corrected(d) = delta_raw(d) + applied_correction_s * (d / lap_distance)

    This keeps the delta *shape* unchanged while ensuring the final lap delta
    is shifted by `applied_correction_s`.

    Requirements:
      - delta_df has columns: ['distance_m', 'delta_time_s']
      - distance_m is non-decreasing

    Returns a copy with extra column:
      - delta_time_s_corrected
    """
    required = {"distance_m", "delta_time_s"}
    missing = sorted(required - set(delta_df.columns))
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    out = delta_df.copy()
    lap_distance = float(out["distance_m"].max())
    if lap_distance <= 0:
        raise ValueError("lap_distance must be > 0")

    ramp = out["distance_m"] / lap_distance
    out["delta_time_s_corrected"] = out["delta_time_s"] + applied_correction_s * ramp
    return out
