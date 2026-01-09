from __future__ import annotations

from pathlib import Path

import pandas as pd
from src.telemetry.attribution import attribute_corner_losses_v1


def main() -> None:
    processed = Path("data/processed")

    ref_path = processed / "sample_2023_Monza_Q_VER_fastest.parquet"
    tgt_path = processed / "sample_2023_Monza_Q_LEC_fastest.parquet"

    ref = pd.read_parquet(ref_path)
    tgt = pd.read_parquet(tgt_path)

    attrs = attribute_corner_losses_v1(ref, tgt, distance_step_m=1.0, exit_len_m=120.0)
    df = pd.DataFrame([a.__dict__ for a in attrs])

    out_csv = Path("reports/monza_2023q_attribution_ver_vs_lec.csv")
    df.to_csv(out_csv, index=False)

    print("Wrote:", out_csv)
    print(
        df[
            [
                "corner_id",
                "loss_braking_s",
                "loss_exit_s",
                "loss_total_s",
            ]
        ]
    )

    print("\nTotals:")
    print("Braking loss total (s):", float(df["loss_braking_s"].sum()))
    print("Exit loss total (s):   ", float(df["loss_exit_s"].sum()))
    print("Corner total (s):      ", float(df["loss_total_s"].sum()))


if __name__ == "__main__":
    main()
