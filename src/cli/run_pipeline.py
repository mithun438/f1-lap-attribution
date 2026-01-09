from __future__ import annotations

import argparse
from pathlib import Path

from src.data.fastf1_utils import pull_fastest_lap_pair
from src.reports.attribution_table import run_attribution_report
from src.reports.plot_attribution_bars import run_attribution_bar_plot
from src.reports.plot_delta_time import run_delta_plot
from src.reports.plot_delta_with_segments import run_delta_with_segments_plot
from src.reports.segments_table import run_segments_report


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(
        description="Run lap delta + corner segmentation + phase attribution for two drivers."
    )
    ap.add_argument("--year", type=int, required=True, help="Season year, e.g., 2023")
    ap.add_argument("--gp", type=str, required=True, help="Grand Prix name, e.g., Italy")
    ap.add_argument(
        "--session", type=str, required=True, help="Session code: FP1/FP2/FP3/Q/R/SQ/SR"
    )
    ap.add_argument("--ref", type=str, required=True, help="Reference driver code, e.g., VER")
    ap.add_argument("--tgt", type=str, required=True, help="Target driver code, e.g., LEC")

    ap.add_argument(
        "--distance-step-m", type=float, default=1.0, help="Distance grid step in meters"
    )
    ap.add_argument("--exit-len-m", type=float, default=120.0, help="Exit window length in meters")
    ap.add_argument(
        "--out-tag", type=str, default="run", help="Prefix tag for report/plot filenames"
    )

    return ap.parse_args()


def main() -> None:
    args = parse_args()

    processed = Path("data/processed")
    processed.mkdir(parents=True, exist_ok=True)

    # 1) Pull fastest laps
    ref_path, tgt_path = pull_fastest_lap_pair(
        year=args.year,
        gp=args.gp,
        session=args.session,
        ref_driver=args.ref,
        tgt_driver=args.tgt,
        out_dir=processed,
        out_tag=args.out_tag,
    )

    # 2) Generate plots and tables
    run_delta_plot(ref_path, tgt_path, out_tag=args.out_tag, distance_step_m=args.distance_step_m)
    run_delta_with_segments_plot(
        ref_path,
        tgt_path,
        out_tag=args.out_tag,
        distance_step_m=args.distance_step_m,
        exit_len_m=args.exit_len_m,
    )
    run_segments_report(
        ref_path,
        out_tag=args.out_tag,
        exit_len_m=args.exit_len_m,
        distance_step_m=args.distance_step_m,
    )
    run_attribution_report(
        ref_path,
        tgt_path,
        out_tag=args.out_tag,
        distance_step_m=args.distance_step_m,
        exit_len_m=args.exit_len_m,
    )
    run_attribution_bar_plot(out_tag=args.out_tag)

    print("\nDone.")
    print("Reports:   ./reports")
    print("Telemetry: ./data/processed")


if __name__ == "__main__":
    main()
