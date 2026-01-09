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
    throttle = np.zeros(len(d), dtype=float)
    throttle[160:] = 30.0  # throttle-on after apex region (roughly)
    lap = pd.DataFrame({"distance_m": d, "time_s": t, "speed_kph": v, "throttle_pct": throttle})

    zones = [BrakingZone(start_m=100.0, end_m=150.0, length_m=50.0, peak_decel_kph_per_s=-200.0)]
    segs = build_corner_segments(lap, zones, exit_len_m=100.0)

    assert len(segs) == 1
    s = segs[0]
    assert s.brake_start_m <= s.apex_m <= s.exit_end_m
    assert s.segment_time_s > 0
    assert s.min_speed_kph <= s.entry_speed_kph


def test_segments_do_not_overlap():
    # Two zones with a small gap; exit_len should be capped to avoid overlap.
    d = np.arange(0, 1001, 1, dtype=float)
    t = np.linspace(0, 100, len(d))
    v = np.full(len(d), 300.0)
    throttle = np.full(len(d), 50.0, dtype=float)  # always on-throttle (simplifies)
    lap = pd.DataFrame({"distance_m": d, "time_s": t, "speed_kph": v, "throttle_pct": throttle})

    zones = [
        BrakingZone(start_m=200.0, end_m=260.0, length_m=60.0, peak_decel_kph_per_s=-200.0),
        BrakingZone(start_m=330.0, end_m=380.0, length_m=50.0, peak_decel_kph_per_s=-180.0),
    ]

    segs = build_corner_segments(lap, zones, exit_len_m=200.0)

    assert len(segs) == 2
    assert segs[0].exit_end_m <= segs[1].brake_start_m
