from __future__ import annotations

from pathlib import Path

import pandas as pd
from src.analysis.validate_physics_metrics import load_all_summaries


def test_load_all_summaries(tmp_path: Path):
    run1 = tmp_path / "run1"
    run1.mkdir()
    pd.DataFrame(
        [
            {
                "ref": "VER",
                "tgt": "LEC",
                "delta_lap_time_s": 0.1,
                "straight_time_loss_s": 0.05,
            }
        ]
    ).to_csv(run1 / "batch_summary_ranked.csv", index=False)

    df = load_all_summaries(tmp_path)
    assert len(df) == 1
    assert "run_dir" in df.columns
    assert df.iloc[0]["run_dir"] == "run1"
