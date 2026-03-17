from __future__ import annotations

import pandas as pd
from src.telemetry.physics import estimate_straight_time_loss


def test_estimate_straight_time_loss_basic():
    df = pd.DataFrame(
        {
            "distance_m": [0, 50, 100, 150],
            "ref_time_s": [0.0, 0.5, 1.0, 1.5],
            "tgt_time_s": [0.0, 0.55, 1.10, 1.60],
            "ref_speed_kph": [200, 260, 270, 220],
            "tgt_speed_kph": [210, 255, 265, 230],
        }
    )

    out = estimate_straight_time_loss(df, min_speed_kph=250.0)
    assert abs(out - 0.05) < 1e-12
