from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class TelemetrySchema:
    distance: str
    time_s: str
    speed: str
    throttle: str
    brake: str
    gear: str
    drs: str


RAW_FASTF1 = TelemetrySchema(
    distance="Distance",
    time_s="Time",
    speed="Speed",
    throttle="Throttle",
    brake="Brake",
    gear="nGear",
    drs="DRS",
)

NORMALIZED = TelemetrySchema(
    distance="distance_m",
    time_s="time_s",
    speed="speed_kph",
    throttle="throttle_pct",
    brake="brake",
    gear="gear",
    drs="drs",
)


def _pick_schema(df: pd.DataFrame) -> TelemetrySchema:
    cols = set(df.columns)
    raw_ok = {RAW_FASTF1.distance, RAW_FASTF1.time_s, RAW_FASTF1.speed}.issubset(cols)
    norm_ok = {NORMALIZED.distance, NORMALIZED.time_s, NORMALIZED.speed}.issubset(cols)

    if norm_ok:
        return NORMALIZED
    if raw_ok:
        return RAW_FASTF1

    # Helpful error
    needed_raw = [RAW_FASTF1.distance, RAW_FASTF1.time_s, RAW_FASTF1.speed]
    needed_norm = [NORMALIZED.distance, NORMALIZED.time_s, NORMALIZED.speed]
    raise ValueError(
        "Unsupported telemetry schema. Expected either raw FastF1 columns "
        f"{needed_raw} or normalized columns {needed_norm}. Got columns: {sorted(cols)[:20]}..."
    )


def _ensure_time_seconds(df: pd.DataFrame, schema: TelemetrySchema) -> pd.DataFrame:
    """
    Ensure we have a float time column in seconds.
    - For raw FastF1, Time may be a Timedelta OR already seconds float (e.g., unit tests).
    - For normalized schema, time_s is already seconds.
    """
    if schema is NORMALIZED:
        return df

    if schema.time_s not in df.columns:
        raise ValueError(f"Missing time column: {schema.time_s}")

    out = df.copy()
    s = out[schema.time_s]

    # FastF1 telemetry: Time is usually Timedelta -> .dt.total_seconds()
    # Unit tests / synthetic: Time may already be float seconds.
    if hasattr(s, "dt"):
        try:
            out["time_s"] = s.dt.total_seconds()
            return out
        except Exception:
            # fall through to numeric conversion
            pass

    out["time_s"] = pd.to_numeric(s, errors="raise").astype(float)
    return out


def resample_by_distance(df: pd.DataFrame, *, distance_step_m: float = 1.0) -> pd.DataFrame:
    """
    Resample telemetry onto a uniform distance grid.
    Supports:
      - Raw FastF1 telemetry columns (Distance, Time, Speed, Throttle, Brake, nGear, DRS)
      - Normalized columns (distance_m, time_s, speed_kph, throttle_pct, brake, gear, drs)

    Returns a DataFrame with normalized output columns:
      distance_m, time_s, speed_kph, throttle_pct, brake, gear, drs
    """
    schema = _pick_schema(df)
    work = _ensure_time_seconds(df, schema)

    # Required columns (raw or normalized)
    required = [schema.distance, "time_s" if schema is RAW_FASTF1 else schema.time_s, schema.speed]
    missing = [c for c in required if c not in work.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    # Build normalized working frame
    if schema is RAW_FASTF1:
        dist = work[schema.distance].astype(float).to_numpy()
        time_s = work["time_s"].astype(float).to_numpy()
        speed = work[schema.speed].astype(float).to_numpy()
        throttle = (
            work[schema.throttle].astype(float).to_numpy()
            if schema.throttle in work.columns
            else None
        )
        brake = work[schema.brake].to_numpy() if schema.brake in work.columns else None
        gear = work[schema.gear].astype(float).to_numpy() if schema.gear in work.columns else None
        drs = work[schema.drs].astype(float).to_numpy() if schema.drs in work.columns else None
    else:
        dist = work[schema.distance].astype(float).to_numpy()
        time_s = work[schema.time_s].astype(float).to_numpy()
        speed = work[schema.speed].astype(float).to_numpy()
        throttle = (
            work[schema.throttle].astype(float).to_numpy()
            if schema.throttle in work.columns
            else None
        )
        brake = work[schema.brake].to_numpy() if schema.brake in work.columns else None
        gear = work[schema.gear].astype(float).to_numpy() if schema.gear in work.columns else None
        drs = work[schema.drs].astype(float).to_numpy() if schema.drs in work.columns else None

    # Ensure monotonic distance for interpolation
    order = np.argsort(dist)
    dist = dist[order]
    time_s = time_s[order]
    speed = speed[order]
    if throttle is not None:
        throttle = throttle[order]
    if brake is not None:
        brake = brake[order]
    if gear is not None:
        gear = gear[order]
    if drs is not None:
        drs = drs[order]

    # Uniform distance grid
    start = float(dist[0])
    end = float(dist[-1])
    grid = np.arange(start, end + distance_step_m, distance_step_m, dtype=float)

    # Interpolate continuous channels
    time_i = np.interp(grid, dist, time_s)
    speed_i = np.interp(grid, dist, speed)

    out = pd.DataFrame(
        {
            "distance_m": grid,
            "time_s": time_i,
            "speed_kph": speed_i,
        }
    )

    if throttle is not None:
        out["throttle_pct"] = np.interp(grid, dist, throttle)
    else:
        out["throttle_pct"] = 0.0

    # Discrete-ish channels: nearest neighbor via interpolation on indices
    def _nearest(arr: np.ndarray, fill) -> np.ndarray:
        if arr is None:
            return np.full(len(grid), fill)
        # nearest by interpolating index
        idx = np.interp(grid, dist, np.arange(len(arr)))
        idx = np.clip(np.rint(idx).astype(int), 0, len(arr) - 1)
        return arr[idx]

    out["brake"] = _nearest(brake, False).astype(bool)
    out["gear"] = _nearest(gear, 0).astype(int)
    out["drs"] = _nearest(drs, 0).astype(int)

    return out
