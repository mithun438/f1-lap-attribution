from __future__ import annotations

from pathlib import Path

import fastf1
import pandas as pd


def _ensure_cache(cache_dir: Path) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_dir))


def _pick_fastest_lap(session, driver_code: str):
    laps = session.laps.pick_drivers([driver_code])
    if laps.empty:
        raise ValueError(f"No laps available for driver {driver_code}")
    fastest = laps.pick_fastest()
    if fastest is None:
        raise ValueError(f"Could not pick fastest lap for driver {driver_code}")
    return fastest


def _lap_telemetry_to_df(lap) -> pd.DataFrame:
    tel = lap.get_telemetry()
    # Keep only columns used by the pipeline; add stable naming
    keep = {
        "Time": "time",
        "Distance": "distance_m",
        "Speed": "speed_kph",
        "Throttle": "throttle_pct",
        "Brake": "brake",
        "nGear": "gear",
        "DRS": "drs",
    }
    cols = [c for c in keep.keys() if c in tel.columns]
    df = tel[cols].rename(columns=keep).copy()

    # Convert pandas Timedelta to seconds float for easier handling downstream
    if "time" in df.columns:
        df["time_s"] = df["time"].dt.total_seconds()
        df = df.drop(columns=["time"])

    # Ensure required columns exist
    required = ["distance_m", "time_s", "speed_kph"]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Telemetry missing required columns: {missing}")

    # Some sessions may not provide throttle/brake; keep columns if present
    if "throttle_pct" not in df.columns:
        df["throttle_pct"] = 0.0
    if "brake" not in df.columns:
        df["brake"] = False

    return df


def pull_fastest_lap_pair(
    *,
    year: int,
    gp: str,
    session: str,
    ref_driver: str,
    tgt_driver: str,
    out_dir: Path,
    out_tag: str,
    cache_dir: Path | None = None,
) -> tuple[Path, Path]:
    """
    Pull the fastest lap telemetry for two drivers from a given session, write to parquet,
    and return (ref_path, tgt_path).
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    if cache_dir is None:
        cache_dir = out_dir / "fastf1_cache"

    _ensure_cache(cache_dir)

    sess = fastf1.get_session(year, gp, session)
    sess.load()

    ref_lap = _pick_fastest_lap(sess, ref_driver)
    tgt_lap = _pick_fastest_lap(sess, tgt_driver)

    ref_df = _lap_telemetry_to_df(ref_lap)
    tgt_df = _lap_telemetry_to_df(tgt_lap)

    # Add metadata columns (helpful for debugging and later aggregation)
    for df, drv in [(ref_df, ref_driver), (tgt_df, tgt_driver)]:
        df["year"] = year
        df["gp"] = gp
        df["session"] = session
        df["driver"] = drv

    ref_path = out_dir / f"{out_tag}_{year}_{gp}_{session}_{ref_driver}_fastest.parquet"
    tgt_path = out_dir / f"{out_tag}_{year}_{gp}_{session}_{tgt_driver}_fastest.parquet"

    ref_df.to_parquet(ref_path, index=False)
    tgt_df.to_parquet(tgt_path, index=False)

    return ref_path, tgt_path
