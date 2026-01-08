#!/usr/bin/env python3
"""
Pull a single sample lap telemetry from FastF1 and write:
- raw session cache handled by FastF1 (local cache)
- processed telemetry parquet/csv in data/processed/

We start with ONE known event to prove the pipeline end-to-end.
"""

from __future__ import annotations

from pathlib import Path

import fastf1

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"


def main() -> None:
    print("fastf1 version:", fastf1.__version__)
    # Ensure directories exist (they are gitignored)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    # Use a deterministic cache location inside the repo
    cache_dir = RAW_DIR / "fastf1_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_dir))

    # Pick a stable, well-known session
    year = 2023
    gp = "Monza"
    session_name = "Q"  # Qualifying

    # Choose a high-likelihood driver code (if this fails, we’ll adjust next step)
    driver = "VER"

    session = fastf1.get_session(year, gp, session_name)
    session.load()

    # Prefer a specific driver if available; otherwise fall back to overall fastest lap.
    # This avoids NoneType failures when a driver has no valid laps/telemetry in that session.
    drivers_available = sorted(session.laps["Driver"].dropna().unique().tolist())
    print("Drivers available:", drivers_available)

    lap = None
    if driver in drivers_available:
        laps = session.laps.pick_drivers([driver])
        lap = laps.pick_fastest()

    if lap is None:
        print(
            f"Warning: No valid fastest lap found for driver='{driver}'. Falling back to session fastest lap."
        )
        lap = session.laps.pick_fastest()

    if lap is None:
        raise RuntimeError(
            "Could not find any valid lap in this session (pick_fastest returned None)."
        )

    print("Selected lap:", dict(Driver=lap["Driver"], LapNumber=int(lap["LapNumber"])))
    tel = lap.get_telemetry()

    # Keep only columns we care about now; more later if needed
    keep = ["Time", "Distance", "Speed", "Throttle", "Brake", "nGear", "DRS"]
    tel = tel[keep].copy()

    # Basic cleaning
    tel = tel.dropna(subset=["Distance", "Speed"]).reset_index(drop=True)

    # Enforce types
    tel["Distance"] = tel["Distance"].astype(float)
    tel["Speed"] = tel["Speed"].astype(float)

    # Save a "raw-ish" processed file for reproducibility
    stem = f"sample_{year}_{gp}_{session_name}_{driver}_fastest"
    out_parquet = PROCESSED_DIR / f"{stem}.parquet"
    out_csv = PROCESSED_DIR / f"{stem}.csv"

    try:
        tel.to_parquet(out_parquet, index=False)
        print(f"Wrote: {out_parquet}")
    except Exception as e:
        tel.to_csv(out_csv, index=False)
        print(f"Parquet unavailable ({type(e).__name__}: {e}). Wrote CSV instead: {out_csv}")
    print(tel.head(3))
    print("Rows:", len(tel), "| Distance max:", float(tel["Distance"].max()))


if __name__ == "__main__":
    main()
