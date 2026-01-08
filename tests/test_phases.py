import numpy as np
import pandas as pd
from src.telemetry.phases import detect_braking_zones


def test_detect_braking_zones_finds_one_zone():
    # Construct a simple lap with a single braking segment
    d = np.arange(0, 101, 1, dtype=float)
    t = np.linspace(0, 10, len(d))
    v = np.linspace(300, 250, len(d))
    brake = np.zeros(len(d), dtype=bool)
    brake[30:61] = True  # 31m zone

    lap = pd.DataFrame({"distance_m": d, "time_s": t, "speed_kph": v, "brake": brake})

    labeled, zones = detect_braking_zones(
        lap,
        min_zone_len_m=20.0,
        merge_gap_m=5.0,
        smooth_window=1,
    )

    assert "phase_brake" in labeled.columns
    assert labeled["phase_brake"].sum() > 0
    assert len(zones) == 1
    assert zones[0].length_m >= 20.0
