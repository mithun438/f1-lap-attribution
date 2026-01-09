from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from src.telemetry.delta import compute_delta_on_distance_grid
from src.telemetry.phases import detect_braking_zones
from src.telemetry.resample import resample_by_distance
from src.telemetry.segments import CornerSegment, build_corner_segments


@dataclass(frozen=True)
class CornerAttribution:
    corner_id: int
    brake_start_m: float
    apex_m: float
    exit_end_m: float
    delta_at_brake_start_s: float
    delta_at_apex_s: float
    delta_at_exit_s: float
    loss_braking_s: float
    loss_exit_s: float
    loss_total_s: float


def _interp_delta(delta_df: pd.DataFrame, dist_m: float) -> float:
    """Linear interpolation of delta_time_s on distance_m."""
    d = delta_df["distance_m"].to_numpy(dtype=float)
    y = delta_df["delta_time_s"].to_numpy(dtype=float)
    dist_m = float(np.clip(dist_m, d[0], d[-1]))
    return float(np.interp(dist_m, d, y))


def attribute_corner_losses_v1(
    ref_raw: pd.DataFrame,
    tgt_raw: pd.DataFrame,
    *,
    distance_step_m: float = 1.0,
    exit_len_m: float = 120.0,
) -> list[CornerAttribution]:
    """
    v1 attribution using reference (ref) corner segments.

    ref = faster lap typically (e.g., VER)
    tgt = comparison lap (e.g., LEC)

    Output losses are positive if target is slower.
    """
    # Resample both for segmentation consistency
    ref = resample_by_distance(ref_raw, distance_step_m=distance_step_m)

    # Build braking zones + segments on reference lap
    labeled_ref, zones = detect_braking_zones(ref)
    segments: list[CornerSegment] = build_corner_segments(labeled_ref, zones, exit_len_m=exit_len_m)

    # Compute delta curve on same step
    delta = compute_delta_on_distance_grid(ref_raw, tgt_raw, distance_step_m=distance_step_m)

    out: list[CornerAttribution] = []
    for s in segments:
        db = _interp_delta(delta, s.brake_start_m)
        da = _interp_delta(delta, s.apex_m)
        dx = _interp_delta(delta, s.exit_end_m)

        loss_brake = da - db
        loss_exit = dx - da
        loss_total = dx - db

        out.append(
            CornerAttribution(
                corner_id=s.corner_id,
                brake_start_m=s.brake_start_m,
                apex_m=s.apex_m,
                exit_end_m=s.exit_end_m,
                delta_at_brake_start_s=db,
                delta_at_apex_s=da,
                delta_at_exit_s=dx,
                loss_braking_s=loss_brake,
                loss_exit_s=loss_exit,
                loss_total_s=loss_total,
            )
        )

    return out
