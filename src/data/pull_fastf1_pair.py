from __future__ import annotations

from pathlib import Path

import fastf1
import pandas as pd

DATA_DIR = Path("data")
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"


def pull_fastest_lap(year: int, gp: str, session_name: str, driver: str) -> pd.DataFrame:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    cache_dir = RAW_DIR / "fastf1_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_dir))

    session = fastf1.get_session(year, gp, session_name)
    session.load()

    drivers_available = sorted(session.laps["Driver"].dropna().unique().tolist())
    if driver not in drivers_available:
        raise ValueError(f"Driver '{driver}' not in session. Available: {drivers_available}")

    lap = session.laps.pick_drivers([driver]).pick_fastest()
    if lap is None:
        raise RuntimeError(f"No valid fastest lap found for driver '{driver}'")

    tel = lap.get_telemetry()[
        ["Time", "Distance", "Speed", "Throttle", "Brake", "nGear", "DRS"]
    ].copy()
    tel = tel.dropna(subset=["Distance", "Speed"]).reset_index(drop=True)

    return tel


def main() -> None:
    print("fastf1 version:", fastf1.__version__)

    year, gp, session_name = 2023, "Monza", "Q"
    ref_driver = "VER"
    tgt_driver = "LEC"  # change if you want

    ref = pull_fastest_lap(year, gp, session_name, ref_driver)
    tgt = pull_fastest_lap(year, gp, session_name, tgt_driver)

    ref_path = PROCESSED_DIR / f"sample_{year}_{gp}_{session_name}_{ref_driver}_fastest.parquet"
    tgt_path = PROCESSED_DIR / f"sample_{year}_{gp}_{session_name}_{tgt_driver}_fastest.parquet"

    ref.to_parquet(ref_path, index=False)
    tgt.to_parquet(tgt_path, index=False)

    print("Wrote:", ref_path)
    print("Wrote:", tgt_path)
    print("Ref rows:", len(ref), "Tgt rows:", len(tgt))


if __name__ == "__main__":
    main()
