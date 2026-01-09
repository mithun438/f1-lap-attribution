import numpy as np
import pandas as pd
from src.telemetry.resample import resample_by_distance


def make_dummy_df():
    # Irregular distance samples
    dist = np.array([0.0, 0.7, 20.6, 21.2, 50.0], dtype=float)
    # Time as seconds (allowed)
    time = np.array([0.0, 0.01, 0.23, 0.24, 0.60], dtype=float)
    speed = np.array([300, 301, 318, 317, 290], dtype=float)
    throttle = np.array([100, 100, 100, 80, 50], dtype=float)
    brake = np.array([False, False, False, True, True])
    gear = np.array([8, 8, 8, 7, 6], dtype=int)
    drs = np.array([8, 8, 8, 0, 0], dtype=int)

    return pd.DataFrame(
        {
            "Distance": dist,
            "Time": time,
            "Speed": speed,
            "Throttle": throttle,
            "Brake": brake,
            "nGear": gear,
            "DRS": drs,
        }
    )


def test_resample_monotonic_and_schema():
    df = make_dummy_df()
    out = resample_by_distance(df, distance_step_m=1.0)

    assert list(out.columns) == [
        "distance_m",
        "time_s",
        "speed_kph",
        "throttle_pct",
        "brake",
        "gear",
        "drs",
    ]
    assert np.all(np.diff(out["distance_m"].to_numpy()) > 0)
    assert np.all(np.diff(out["time_s"].to_numpy()) >= 0)
    assert out["throttle_pct"].between(0, 100).all()


def test_missing_columns_raises():
    # Only distance/time/speed are required. Optional channels should default.
    df = make_dummy_df().drop(columns=["DRS"])
    out = resample_by_distance(df, distance_step_m=1.0)
    assert "drs" in out.columns
    assert (out["drs"] == 0).all()
