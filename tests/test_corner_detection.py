import pandas as pd
from src.analysis.corner_detection import detect_segments


def test_detect_segments():
    df = pd.DataFrame(
        {
            "distance_m": [0, 50, 100, 150, 200],
            "ref_speed_kph": [300, 290, 150, 140, 310],
            "tgt_speed_kph": [305, 295, 155, 145, 315],
        }
    )

    out = detect_segments(df)

    assert "segment_id" in out.columns
    assert out["segment_id"].nunique() > 1
