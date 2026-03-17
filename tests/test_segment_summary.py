import pandas as pd
from src.analysis.segment_summary import summarize_segments


def test_segment_summary_basic():
    df = pd.DataFrame(
        {
            "distance_m": [0, 50, 100, 150, 200],
            "delta_time_s": [0, 0.01, 0.02, 0.03, 0.04],
            "ref_speed_kph": [200, 210, 220, 230, 240],
            "tgt_speed_kph": [205, 215, 225, 235, 245],
        }
    )

    out = summarize_segments(df, segment_length_m=100)

    assert len(out) > 0
    assert "delta_time_s" in out.columns
