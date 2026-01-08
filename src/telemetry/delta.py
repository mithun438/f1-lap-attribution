from __future__ import annotations

import numpy as np
import pandas as pd

from src.telemetry.resample import resample_by_distance


def compute_delta_on_distance_grid(
    ref_df: pd.DataFrame,
    tgt_df: pd.DataFrame,
    distance_step_m: float = 1.0,
) -> pd.DataFrame:
    """
    Resample both laps to a uniform distance grid and compute deltas.
    delta_time_s = tgt_time_s - ref_time_s  (positive means target is slower)
    """
    ref = resample_by_distance(ref_df, distance_step_m=distance_step_m)
    tgt = resample_by_distance(tgt_df, distance_step_m=distance_step_m)

    # Align by common distance range (intersection)
    d0 = max(ref["distance_m"].min(), tgt["distance_m"].min())
    d1 = min(ref["distance_m"].max(), tgt["distance_m"].max())

    ref = ref[(ref["distance_m"] >= d0) & (ref["distance_m"] <= d1)].reset_index(drop=True)
    tgt = tgt[(tgt["distance_m"] >= d0) & (tgt["distance_m"] <= d1)].reset_index(drop=True)

    if len(ref) != len(tgt):
        # distance grids should match if step is same; if not, reindex by merge
        merged = pd.merge(ref, tgt, on="distance_m", suffixes=("_ref", "_tgt"))
        ref_time = merged["time_s_ref"].to_numpy()
        tgt_time = merged["time_s_tgt"].to_numpy()
        out = pd.DataFrame({"distance_m": merged["distance_m"].to_numpy()})
        out["ref_time_s"] = ref_time
        out["tgt_time_s"] = tgt_time
        out["delta_time_s"] = tgt_time - ref_time
        out["delta_speed_kph"] = merged["speed_kph_tgt"] - merged["speed_kph_ref"]
        out["ref_speed_kph"] = merged["speed_kph_ref"]
        out["tgt_speed_kph"] = merged["speed_kph_tgt"]
        return out

    out = pd.DataFrame({"distance_m": ref["distance_m"]})
    out["ref_time_s"] = ref["time_s"]
    out["tgt_time_s"] = tgt["time_s"]
    out["ref_speed_kph"] = ref["speed_kph"]
    out["tgt_speed_kph"] = tgt["speed_kph"]
    out["delta_time_s"] = out["tgt_time_s"] - out["ref_time_s"]
    out["delta_speed_kph"] = out["tgt_speed_kph"] - out["ref_speed_kph"]

    # sanity: delta_time should start ~0 at beginning
    out["delta_time_s"] = out["delta_time_s"] - float(out["delta_time_s"].iloc[0])

    # monotonic distance check
    if not np.all(np.diff(out["distance_m"].to_numpy()) > 0):
        raise RuntimeError("distance_m is not strictly increasing in delta output.")

    return out
