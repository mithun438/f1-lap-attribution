from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class BrakingZone:
    start_m: float
    end_m: float
    length_m: float
    peak_decel_kph_per_s: float


def _rolling_mean(x: np.ndarray, win: int) -> np.ndarray:
    if win <= 1:
        return x
    # simple centered-ish smoothing using convolution
    k = np.ones(win, dtype=float) / win
    return np.convolve(x, k, mode="same")


def detect_braking_zones(
    lap_df: pd.DataFrame,
    *,
    distance_col: str = "distance_m",
    speed_col: str = "speed_kph",
    brake_col: str = "brake",
    time_col: str = "time_s",
    smooth_window: int = 5,
    min_zone_len_m: float = 20.0,
    merge_gap_m: float = 10.0,
) -> tuple[pd.DataFrame, list[BrakingZone]]:
    """
    Input expects canonical resampled schema:
      distance_m, time_s, speed_kph, brake (bool)

    Strategy (v1):
      - Use brake boolean as primary indicator
      - Compute deceleration proxy from speed vs time for zone stats
      - Merge short gaps (driver may release brake briefly)
      - Drop zones shorter than min_zone_len_m
    """
    for c in [distance_col, speed_col, brake_col, time_col]:
        if c not in lap_df.columns:
            raise ValueError(f"Missing required column '{c}'")

    d = lap_df[distance_col].to_numpy(dtype=float)
    v = lap_df[speed_col].to_numpy(dtype=float)
    t = lap_df[time_col].to_numpy(dtype=float)
    brake = lap_df[brake_col].to_numpy(dtype=bool)

    # Smooth speed slightly to avoid noisy derivative spikes
    v_s = _rolling_mean(v, smooth_window)

    # dv/dt in kph/s (proxy; good enough for relative stats)
    dt = np.diff(t, prepend=t[0])
    dt[dt <= 1e-6] = 1e-6
    dv = np.diff(v_s, prepend=v_s[0])
    dvdt = dv / dt

    # Identify raw braking segments from brake flag
    idx = np.where(brake)[0]
    zones: list[tuple[int, int]] = []
    if len(idx) > 0:
        start = idx[0]
        prev = idx[0]
        for i in idx[1:]:
            # new segment if not contiguous
            if i != prev + 1:
                zones.append((start, prev))
                start = i
            prev = i
        zones.append((start, prev))

    # Merge zones separated by small gaps in distance
    merged: list[tuple[int, int]] = []
    for s, e in zones:
        if not merged:
            merged.append((s, e))
            continue
        ps, pe = merged[-1]
        gap = d[s] - d[pe]
        if gap <= merge_gap_m:
            merged[-1] = (ps, e)
        else:
            merged.append((s, e))

    # Filter and compute stats
    out_zones: list[BrakingZone] = []
    mask_brake = np.zeros(len(lap_df), dtype=bool)

    for s, e in merged:
        start_m = float(d[s])
        end_m = float(d[e])
        length_m = end_m - start_m
        if length_m < min_zone_len_m:
            continue

        # peak decel is the most negative dv/dt within zone
        peak_decel = float(np.min(dvdt[s : e + 1]))  # negative
        out_zones.append(
            BrakingZone(
                start_m=start_m,
                end_m=end_m,
                length_m=float(length_m),
                peak_decel_kph_per_s=float(peak_decel),
            )
        )
        mask_brake[s : e + 1] = True

    labeled = lap_df.copy()
    labeled["phase_brake"] = mask_brake
    labeled["decel_kph_per_s"] = dvdt

    return labeled, out_zones
