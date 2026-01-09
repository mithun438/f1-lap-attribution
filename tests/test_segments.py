import numpy as np
import pandas as pd
from src.telemetry.phases import BrakingZone
from src.telemetry.segments import build_corner_segments


def test_build_corner_segments_basic():
    d = np.arange(0, 501, 1, dtype=float)
    t = np.linspace(0, 50, len(d))
    # speed drops then rises around a braking zone
    v = np.full(len(d), 300.0)
    v[100:151] = np.linspace(300, 120, 51)
    v[151:221] = np.linspace(120, 260, 70)
    lap = pd.DataFrame({"distance_m": d, "time_s": t, "speed_kph": v})

    zones = [BrakingZone(start_m=100.0, end_m=150.0, length_m=50.0, peak_decel_kph_per_s=-200.0)]
    segs = build_corner_segments(lap, zones, exit_len_m=100.0)

    assert len(segs) == 1
    s = segs[0]
    assert s.brake_start_m <= s.apex_m <= s.exit_end_m
    assert s.segment_time_s > 0
    assert s.min_speed_kph <= s.entry_speed_kph
