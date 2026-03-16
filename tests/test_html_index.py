from __future__ import annotations

from pathlib import Path

import pandas as pd
from src.reports.html_index import write_batch_index


def test_write_batch_index(tmp_path: Path):
    summary = tmp_path / "batch_summary.csv"
    pd.DataFrame(
        [
            {
                "ref": "VER",
                "tgt": "LEC",
                "delta_lap_time_s": 0.123,
                "out_tag": "batch_VER_vs_LEC",
            }
        ]
    ).to_csv(summary, index=False)

    out = write_batch_index(out_dir=tmp_path, summary_csv=summary)
    assert out.exists()

    html = out.read_text(encoding="utf-8")
    assert "VER" in html
    assert "LEC" in html
    assert "batch_VER_vs_LEC_report.html" in html
