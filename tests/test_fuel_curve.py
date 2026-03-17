# tests/test_fuel_curve.py
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from src.telemetry.fuel_curve import apply_fuel_correction_ramp


def test_apply_fuel_correction_ramp_shifts_end_by_applied_amount():
    d = np.array([0.0, 50.0, 100.0], dtype=float)
    delta = np.array([0.0, 0.05, 0.10], dtype=float)
    df = pd.DataFrame({"distance_m": d, "delta_time_s": delta})

    applied = -0.18
    out = apply_fuel_correction_ramp(df, applied_correction_s=applied)

    # Start should be unchanged (ramp=0)
    assert abs(out.loc[0, "delta_time_s_corrected"] - out.loc[0, "delta_time_s"]) < 1e-12

    # End should be shifted by applied correction (ramp=1)
    assert (
        abs(out.loc[2, "delta_time_s_corrected"] - (out.loc[2, "delta_time_s"] + applied)) < 1e-12
    )

    # Midpoint should be shifted by half the applied correction
    assert (
        abs(out.loc[1, "delta_time_s_corrected"] - (out.loc[1, "delta_time_s"] + 0.5 * applied))
        < 1e-12
    )


def test_apply_fuel_correction_requires_columns():
    df = pd.DataFrame({"distance_m": [0.0, 1.0], "oops": [0.0, 0.1]})
    with pytest.raises(ValueError):
        apply_fuel_correction_ramp(df, applied_correction_s=0.1)
