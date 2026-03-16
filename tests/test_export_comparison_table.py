from __future__ import annotations

from pathlib import Path

import pandas as pd
from src.reports.export_comparison_table import export_comparison_table


def test_export_comparison_table_basic(tmp_path: Path):
    ref = pd.DataFrame(
        {
            "distance_m": [0.0, 50.0, 100.0],
            "time_s": [0.0, 1.0, 2.0],
            "speed_kph": [100.0, 110.0, 120.0],
            "throttle": [0.2, 0.5, 1.0],
            "brake": [1.0, 0.0, 0.0],
        }
    )
    tgt = pd.DataFrame(
        {
            "distance_m": [0.0, 50.0, 100.0],
            "time_s": [0.0, 1.1, 2.2],
            "speed_kph": [98.0, 108.0, 118.0],
            "throttle": [0.1, 0.4, 0.9],
            "brake": [1.0, 0.1, 0.0],
        }
    )

    ref_path = tmp_path / "ref.parquet"
    tgt_path = tmp_path / "tgt.parquet"
    ref.to_parquet(ref_path, index=False)
    tgt.to_parquet(tgt_path, index=False)

    out_path = export_comparison_table(
        ref_path,
        tgt_path,
        out_dir=tmp_path,
        out_tag="demo",
        distance_step_m=50.0,
    )

    assert out_path.exists()

    out = pd.read_csv(out_path)
    assert "distance_m" in out.columns
    assert "ref_time_s" in out.columns
    assert "tgt_time_s" in out.columns
    assert "delta_time_s" in out.columns
    assert "ref_speed_kph" in out.columns
    assert "tgt_speed_kph" in out.columns

    assert len(out) == 3
