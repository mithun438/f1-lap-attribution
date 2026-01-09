import numpy as np
import pandas as pd
from src.telemetry.attribution import attribute_corner_losses_v2


def make_simple_lap(speed_scale=1.0):
    # Simple synthetic "lap" where slower speed increases time monotonically
    dist = np.arange(0, 501, 1, dtype=float)
    # base speed profile
    speed = np.full_like(dist, 300.0) * speed_scale
    speed[100:151] = np.linspace(300, 120, 51) * speed_scale
    speed[151:221] = np.linspace(120, 260, 70) * speed_scale
    # integrate time approximately: dt = dd / v (convert kph to m/s)
    v_ms = speed * (1000 / 3600)
    dt = np.diff(dist, prepend=dist[0]) / np.clip(v_ms, 1e-6, None)
    time_s = np.cumsum(dt)

    # Build FastF1-like raw df columns used by pipeline
    df = pd.DataFrame(
        {
            "Distance": dist,
            "Time": time_s,
            "Speed": speed,
            "Throttle": np.full_like(dist, 50.0),
            "Brake": (dist >= 100) & (dist <= 150),
            "nGear": np.full_like(dist, 6),
            "DRS": np.full_like(dist, 0),
        }
    )
    return df


def test_attribution_conservation_nonnegative():
    ref = make_simple_lap(speed_scale=1.0)
    tgt = make_simple_lap(speed_scale=0.98)  # slightly slower everywhere

    attrs = attribute_corner_losses_v2(ref, tgt, distance_step_m=1.0, exit_len_m=100.0)
    assert len(attrs) >= 1

    # losses should be >= 0 in this synthetic scenario
    for a in attrs:
        assert a.loss_total_s >= -1e-6
        # v2: braking + mid-corner + traction should sum to total
        assert (
            abs((a.loss_braking_s + a.loss_midcorner_s + a.loss_traction_s) - a.loss_total_s) < 1e-6
        )
