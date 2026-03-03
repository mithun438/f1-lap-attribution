# tests/test_delta_trace.py
from __future__ import annotations

import numpy as np
import pandas as pd
import pytest
from src.telemetry.delta_trace import compute_delta_trace_from_traces


def test_compute_delta_trace_from_traces_basic_shift():
    # Ref: time increases linearly with distance: 0.01 s per meter
    d = np.array([0.0, 50.0, 100.0], dtype=float)
    ref_t = 0.01 * d

    # Tgt: same but +0.2s everywhere (uniform shift)
    tgt_t = ref_t + 0.2

    ref = pd.DataFrame({"distance_m": d, "time_s": ref_t})
    tgt = pd.DataFrame({"distance_m": d, "time_s": tgt_t})

    out = compute_delta_trace_from_traces(ref, tgt, distance_step_m=50.0)

    assert list(out.columns) == ["distance_m", "delta_time_s"]
    assert np.allclose(out["distance_m"].to_numpy(), np.array([0.0, 50.0, 100.0]))
    assert np.allclose(out["delta_time_s"].to_numpy(), np.array([0.2, 0.2, 0.2]))


def test_compute_delta_trace_requires_columns():
    ref = pd.DataFrame({"distance_m": [0.0, 1.0], "oops": [0.0, 0.1]})
    tgt = pd.DataFrame({"distance_m": [0.0, 1.0], "time_s": [0.0, 0.1]})

    with pytest.raises(ValueError):
        compute_delta_trace_from_traces(ref, tgt, distance_step_m=1.0)


def test_compute_delta_trace_requires_monotonic_distance():
    ref = pd.DataFrame({"distance_m": [0.0, 2.0, 1.0], "time_s": [0.0, 0.2, 0.3]})
    tgt = pd.DataFrame({"distance_m": [0.0, 1.0, 2.0], "time_s": [0.0, 0.1, 0.2]})

    with pytest.raises(ValueError):
        compute_delta_trace_from_traces(ref, tgt, distance_step_m=1.0)
