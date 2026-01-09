from __future__ import annotations

from pathlib import Path

import pandas as pd
from src.telemetry.attribution import attribute_corner_losses_v2


def run_attribution_report(
    ref_path: Path,
    tgt_path: Path,
    *,
    out_tag: str = "run",
    distance_step_m: float = 1.0,
    exit_len_m: float = 120.0,
    out_dir: Path = Path("reports"),
) -> Path:
    """
    Run v2 corner attribution (braking / mid-corner / traction) and write CSV.
    Returns the written CSV path.
    """
    out_dir.mkdir(parents=True, exist_ok=True)

    ref = pd.read_parquet(ref_path)
    tgt = pd.read_parquet(tgt_path)

    attrs = attribute_corner_losses_v2(
        ref,
        tgt,
        distance_step_m=distance_step_m,
        exit_len_m=exit_len_m,
    )

    rows = []
    for a in attrs:
        rows.append(
            {
                "corner_id": a.corner_id,
                "loss_braking_s": a.loss_braking_s,
                "loss_midcorner_s": a.loss_midcorner_s,
                "loss_traction_s": a.loss_traction_s,
                "loss_total_s": a.loss_total_s,
            }
        )

    df = pd.DataFrame(rows).sort_values("corner_id").reset_index(drop=True)
    out_csv = out_dir / f"{out_tag}_attribution_v2.csv"
    df.to_csv(out_csv, index=False)

    print("Wrote:", out_csv)
    print(df)

    print("\nTotals:")
    print("Braking loss total (s):  ", float(df["loss_braking_s"].sum()))
    print("Mid-corner loss total(s):", float(df["loss_midcorner_s"].sum()))
    print("Traction loss total (s): ", float(df["loss_traction_s"].sum()))
    print("Corner total (s):        ", float(df["loss_total_s"].sum()))

    return out_csv


def main() -> None:
    processed = Path("data/processed")
    ref_path = processed / "sample_2023_Monza_Q_VER_fastest.parquet"
    tgt_path = processed / "sample_2023_Monza_Q_LEC_fastest.parquet"

    out = run_attribution_report(
        ref_path,
        tgt_path,
        out_tag="monza_2023q_ver_vs_lec",
        distance_step_m=1.0,
        exit_len_m=120.0,
    )

    # Preserve legacy filename for README stability
    legacy = Path("reports/monza_2023q_attribution_v2_ver_vs_lec.csv")
    if out != legacy:
        legacy.write_bytes(out.read_bytes())


if __name__ == "__main__":
    main()
