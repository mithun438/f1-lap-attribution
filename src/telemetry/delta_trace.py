# src/telemetry/delta_trace.py
from __future__ import annotations

import numpy as np
import pandas as pd

_REQUIRED_TRACE_COLS = ("distance_m", "time_s")


def _validate_trace_df(df: pd.DataFrame) -> None:
    missing = [c for c in _REQUIRED_TRACE_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Trace missing columns: {missing}")

    if len(df) < 2:
        raise ValueError("Trace must have at least 2 rows")

    dist = df["distance_m"].to_numpy(dtype=float)
    if not np.all(np.isfinite(dist)):
        raise ValueError("distance_m must be finite")
    if np.any(np.diff(dist) < 0):
        raise ValueError("distance_m must be non-decreasing")

    t = df["time_s"].to_numpy(dtype=float)
    if not np.all(np.isfinite(t)):
        raise ValueError("time_s must be finite")


def _make_distance_grid(
    ref: pd.DataFrame, tgt: pd.DataFrame, *, distance_step_m: float
) -> np.ndarray:
    if distance_step_m <= 0:
        raise ValueError("distance_step_m must be > 0")

    dmax = float(min(ref["distance_m"].max(), tgt["distance_m"].max()))
    if dmax <= 0:
        raise ValueError("Common lap distance must be > 0")

    # Include end point (within float tolerance)
    n = int(np.floor(dmax / distance_step_m)) + 1
    grid = np.arange(n, dtype=float) * float(distance_step_m)
    # Ensure last grid point does not exceed dmax due to float error
    grid = grid[grid <= dmax + 1e-9]
    return grid


def _interp_time(trace: pd.DataFrame, grid: np.ndarray) -> np.ndarray:
    d = trace["distance_m"].to_numpy(dtype=float)
    t = trace["time_s"].to_numpy(dtype=float)
    # np.interp expects increasing x; we validated non-decreasing.
    # If there are duplicate distances, np.interp is still okay but effectively uses
    # the last occurrence behavior; upstream should ideally avoid duplicates.
    return np.interp(grid, d, t)


def compute_delta_trace_from_traces(
    ref_trace: pd.DataFrame,
    tgt_trace: pd.DataFrame,
    *,
    distance_step_m: float = 1.0,
) -> pd.DataFrame:
    """
    Compute delta time trace between two laps as a function of distance.

    Inputs:
      ref_trace: columns ['distance_m', 'time_s']
      tgt_trace: columns ['distance_m', 'time_s']

    Output:
      DataFrame columns ['distance_m', 'delta_time_s'] where:
        delta_time_s = tgt_time_s(distance) - ref_time_s(distance)
    """
    _validate_trace_df(ref_trace)
    _validate_trace_df(tgt_trace)

    grid = _make_distance_grid(ref_trace, tgt_trace, distance_step_m=distance_step_m)

    ref_t = _interp_time(ref_trace, grid)
    tgt_t = _interp_time(tgt_trace, grid)

    delta = tgt_t - ref_t
    return pd.DataFrame({"distance_m": grid, "delta_time_s": delta})
