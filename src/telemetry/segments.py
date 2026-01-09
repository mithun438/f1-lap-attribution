from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.telemetry.phases import BrakingZone


@dataclass(frozen=True)
class CornerSegment:
    corner_id: int
    brake_start_m: float
    brake_end_m: float
    apex_m: float
    exit_end_m: float
    entry_speed_kph: float
    min_speed_kph: float
    exit_speed_kph: float
    segment_time_s: float


def build_corner_segments(
    lap: pd.DataFrame,
    zones: list[BrakingZone],
    *,
    exit_len_m: float = 120.0,
    distance_col: str = "distance_m",
    time_col: str = "time_s",
    speed_col: str = "speed_kph",
) -> list[CornerSegment]:
    """
    v1 heuristic:
      - Each braking zone corresponds to one corner/complex.
      - Apex is the minimum speed point between brake_start and (brake_end + small buffer).
      - Exit ends at brake_end + exit_len_m (clipped to lap end).
    """
    d = lap[distance_col].to_numpy(dtype=float)
    t = lap[time_col].to_numpy(dtype=float)
    v = lap[speed_col].to_numpy(dtype=float)

    segments: list[CornerSegment] = []
    n = len(lap)

    def idx_at_dist(x: float) -> int:
        i = int(np.searchsorted(d, x, side="left"))
        return int(np.clip(i, 0, n - 1))

    # Precompute zone start/end distances in sorted order
    zone_starts = [float(z.start_m) for z in zones]
    # zone_ends = [float(z.end_m) for z in zones]

    for i, z in enumerate(zones, start=1):
        s_i = idx_at_dist(z.start_m)
        e_i = idx_at_dist(z.end_m)

        # Search for apex slightly after braking ends as well
        apex_search_end = idx_at_dist(min(z.end_m + 50.0, float(d[-1])))
        if apex_search_end <= s_i:
            apex_search_end = e_i

        window = slice(s_i, apex_search_end + 1)
        apex_i_rel = int(np.argmin(v[window]))
        apex_i = s_i + apex_i_rel

        # --- IMPORTANT: cap exit so segments do NOT overlap ---
        proposed_exit_end = z.end_m + exit_len_m

        if i < len(zones):
            # next braking start (leave a small buffer so we don’t include next braking onset)
            next_brake_start = zone_starts[i]  # because i is 1-based index into zones
            cap = max(z.end_m, next_brake_start - 5.0)
            exit_end_m = min(proposed_exit_end, cap)
        else:
            exit_end_m = min(proposed_exit_end, float(d[-1]))

        x_i = idx_at_dist(exit_end_m)

        entry_speed = float(v[s_i])
        min_speed = float(v[apex_i])
        exit_speed = float(v[x_i])

        seg_time = float(t[x_i] - t[s_i])
        segments.append(
            CornerSegment(
                corner_id=i,
                brake_start_m=float(d[s_i]),
                brake_end_m=float(d[e_i]),
                apex_m=float(d[apex_i]),
                exit_end_m=float(d[x_i]),
                entry_speed_kph=entry_speed,
                min_speed_kph=min_speed,
                exit_speed_kph=exit_speed,
                segment_time_s=seg_time,
            )
        )

    return segments
