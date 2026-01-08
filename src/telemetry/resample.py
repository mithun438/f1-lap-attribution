from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class CanonicalSchema:
    """
    Canonical telemetry schema after distance resampling.
    - distance_m: monotonically increasing, uniform step.
    - time_s: monotonic, interpolated (seconds from lap start).
    - speed_kph: interpolated.
    - throttle_pct: interpolated and clipped [0,100].
    - brake: boolean (nearest).
    - gear: integer (nearest).
    - drs: integer state (nearest).
    """

    distance_col: str = "distance_m"
    time_col: str = "time_s"
    speed_col: str = "speed_kph"
    throttle_col: str = "throttle_pct"
    brake_col: str = "brake"
    gear_col: str = "gear"
    drs_col: str = "drs"


def _to_seconds(t: pd.Series) -> np.ndarray:
    # FastF1 provides pandas Timedelta in 'Time'
    if np.issubdtype(t.dtype, np.timedelta64):
        return (t / np.timedelta64(1, "s")).to_numpy(dtype=float)
    # allow already-seconds input
    return t.to_numpy(dtype=float)


def resample_by_distance(
    df: pd.DataFrame,
    distance_step_m: float = 1.0,
    method_continuous: Literal["linear"] = "linear",
) -> pd.DataFrame:
    """
    Resample telemetry to a uniform distance grid.

    Required input columns (FastF1-like):
      - Distance (meters)
      - Time (Timedelta or seconds)
      - Speed (kph)
      - Throttle (0..100)
      - Brake (bool)
      - nGear (int)
      - DRS (int)

    Output columns (canonical):
      distance_m, time_s, speed_kph, throttle_pct, brake, gear, drs
    """
    required = ["Distance", "Time", "Speed", "Throttle", "Brake", "nGear", "DRS"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Sort & de-dup by Distance (interpolation needs strict monotonic x)
    x = df["Distance"].astype(float).to_numpy()
    order = np.argsort(x)
    df = df.iloc[order].copy()
    df = df.drop_duplicates(subset=["Distance"], keep="first").reset_index(drop=True)

    x = df["Distance"].astype(float).to_numpy()
    if len(x) < 2:
        raise ValueError("Need at least 2 samples to resample.")

    # Build uniform grid
    start = float(x[0])
    end = float(x[-1])
    grid = np.arange(start, end + 1e-9, distance_step_m, dtype=float)

    # Continuous signals: interpolate linearly
    t_s = _to_seconds(df["Time"])
    speed = df["Speed"].astype(float).to_numpy()
    throttle = df["Throttle"].astype(float).to_numpy()

    time_i = np.interp(grid, x, t_s)
    speed_i = np.interp(grid, x, speed)
    throttle_i = np.interp(grid, x, throttle)
    throttle_i = np.clip(throttle_i, 0.0, 100.0)

    # Discrete signals: nearest-neighbor by distance
    # (We map each grid point to nearest original sample index)
    idx = np.searchsorted(x, grid, side="left")
    idx = np.clip(idx, 0, len(x) - 1)
    # compare left neighbor vs current to pick truly nearest
    left = np.clip(idx - 1, 0, len(x) - 1)
    choose_left = np.abs(grid - x[left]) <= np.abs(x[idx] - grid)
    nn = np.where(choose_left, left, idx)

    brake_i = df["Brake"].to_numpy()[nn].astype(bool)
    gear_i = df["nGear"].to_numpy()[nn].astype(int)
    drs_i = df["DRS"].to_numpy()[nn].astype(int)

    out = pd.DataFrame(
        {
            "distance_m": grid,
            "time_s": time_i,
            "speed_kph": speed_i,
            "throttle_pct": throttle_i,
            "brake": brake_i,
            "gear": gear_i,
            "drs": drs_i,
        }
    )

    # Final sanity: monotonicity
    if not np.all(np.diff(out["distance_m"].to_numpy()) > 0):
        raise RuntimeError("distance_m is not strictly increasing after resampling.")
    if not np.all(np.diff(out["time_s"].to_numpy()) >= 0):
        raise RuntimeError("time_s is not monotonic after resampling.")

    return out
