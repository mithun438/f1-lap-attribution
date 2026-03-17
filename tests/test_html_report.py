from __future__ import annotations

from pathlib import Path

import pandas as pd
from src.reports.html_report import write_html_report


def test_write_html_report(tmp_path: Path):
    csv_path = tmp_path / "demo_comparison_table.csv"
    pd.DataFrame(
        [
            {"distance_m": 0.0, "ref_time_s": 0.0, "tgt_time_s": 0.0, "delta_time_s": 0.0},
            {"distance_m": 10.0, "ref_time_s": 0.1, "tgt_time_s": 0.2, "delta_time_s": 0.1},
        ]
    ).to_csv(csv_path, index=False)

    (tmp_path / "demo_delta_time_vs_distance.png").write_bytes(b"fakepng")

    out = write_html_report(
        out_dir=tmp_path,
        out_tag="demo",
        delta_s=0.123,
        ref="VER",
        tgt="LEC",
        ref_lap_s=80.3,
        tgt_lap_s=80.4,
        fuel_corrected_delta_s=0.100,
    )

    assert out.exists()
    html = out.read_text(encoding="utf-8")
    assert "VER vs LEC" in html
    assert "Fuel-corrected delta" in html
    assert "demo_comparison_table.csv" in html
    assert "index.html" in html
