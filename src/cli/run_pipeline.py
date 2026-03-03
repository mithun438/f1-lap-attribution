from __future__ import annotations

import argparse
from pathlib import Path

from src.config import load_pipeline_config
from src.data.fastf1_utils import pull_fastest_lap_pair
from src.reports.attribution_table import run_attribution_report
from src.reports.plot_attribution_bars import run_attribution_bar_plot
from src.reports.plot_delta_time import run_delta_plot
from src.reports.plot_delta_with_segments import run_delta_with_segments_plot
from src.reports.segments_table import run_segments_report
from src.telemetry.fuel import normalize_delta_for_fuel


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
    ap.add_argument(
        "--ref-fuel-kg", type=float, default=None, help="Reference fuel mass in kg (optional)"
    )
    ap.add_argument(
        "--tgt-fuel-kg", type=float, default=None, help="Target fuel mass in kg (optional)"
    )
    ap.add_argument(
        "--fuel-coeff",
        type=float,
        default=0.03,
        help="Fuel time coefficient in s/kg (default: 0.03)",
    )
    ap.add_argument(
        "--config",
        type=Path,
        default=Path("config/default.yaml"),
        help="Path to YAML config (defaults to config/default.yaml)",
    )

    return ap.parse_args()


def main() -> None:
    args = parse_args()

    cfg = load_pipeline_config(args.config)

    distance_step_m = (
        args.distance_step_m if args.distance_step_m is not None else cfg.distance_step_m
    )
    fuel_coeff = args.fuel_coeff if args.fuel_coeff is not None else cfg.fuel_coeff
    out_dir = Path(args.out_dir) if getattr(args, "out_dir", None) is not None else cfg.out_dir
    write_plots = (
        args.write_plots if getattr(args, "write_plots", None) is not None else cfg.write_plots
    )

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
    applied_correction_s = None

    if args.ref_fuel_kg is not None and args.tgt_fuel_kg is not None:
        fuel_delta = args.tgt_fuel_kg - args.ref_fuel_kg
        fuel_penalty_delta = fuel_delta * fuel_coeff
        applied_correction_s = -fuel_penalty_delta

    final_delta_s = run_delta_plot(
        ref_path,
        tgt_path,
        out_tag=args.out_tag,
        distance_step_m=distance_step_m,
        out_dir=out_dir,
        applied_correction_s=applied_correction_s,
        write_plots=write_plots,
    )
    if final_delta_s is None:
        raise RuntimeError("run_delta_plot returned None; expected float final delta")

    run_delta_with_segments_plot(
        ref_path,
        tgt_path,
        out_tag=args.out_tag,
        distance_step_m=distance_step_m,
        exit_len_m=args.exit_len_m,
    )
    run_segments_report(
        ref_path,
        out_tag=args.out_tag,
        exit_len_m=args.exit_len_m,
        distance_step_m=distance_step_m,
    )
    run_attribution_report(
        ref_path,
        tgt_path,
        out_tag=args.out_tag,
        distance_step_m=distance_step_m,
        exit_len_m=args.exit_len_m,
    )
    run_attribution_bar_plot(out_tag=args.out_tag)

    # Optional: fuel correction on final lap delta (heuristic).
    # Note: This corrects only the *net* lap delta, not per-corner phase losses.
    # (Per-corner fuel scaling can be added later if desired.)
    summary_lines = []
    summary_lines.append(f"out_tag: {args.out_tag}")
    summary_lines.append(f"raw_delta_lap_time_s: {final_delta_s:.6f}")

    if args.ref_fuel_kg is not None and args.tgt_fuel_kg is not None:
        corrected = normalize_delta_for_fuel(
            final_delta_s,
            ref_fuel_kg=args.ref_fuel_kg,
            tgt_fuel_kg=args.tgt_fuel_kg,
            coeff_s_per_kg=fuel_coeff,
        )
        fuel_delta = args.tgt_fuel_kg - args.ref_fuel_kg
        fuel_penalty_delta = fuel_delta * args.fuel_coeff
        applied_correction = -fuel_penalty_delta  # what we apply to raw delta

        print("Fuel correction:")
        print(f"  ref_fuel_kg:             {args.ref_fuel_kg}")
        print(f"  tgt_fuel_kg:             {args.tgt_fuel_kg}")
        print(f"  fuel_delta_kg (tgt-ref): {fuel_delta:+.1f}")
        print(f"  fuel_penalty_delta_s (tgt-ref): {fuel_penalty_delta:+.4f}")
        print(f"  applied_correction_s (add to raw): {applied_correction:+.4f}")
        print(f"Fuel-corrected Δlap time (s): {corrected:+.6f}")

        summary_lines.append(f"ref_fuel_kg: {args.ref_fuel_kg}")
        summary_lines.append(f"tgt_fuel_kg: {args.tgt_fuel_kg}")
        summary_lines.append(f"fuel_coeff_s_per_kg: {fuel_coeff}")
        summary_lines.append(f"fuel_corrected_delta_lap_time_s: {corrected:.6f}")
    else:
        summary_lines.append("fuel_correction: disabled (provide --ref-fuel-kg and --tgt-fuel-kg)")

    reports_dir = Path("reports")
    reports_dir.mkdir(parents=True, exist_ok=True)
    summary_path = reports_dir / f"{args.out_tag}_summary.txt"
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    print(f"Wrote: {summary_path}")

    print("\nDone.")
    print("Reports:   ./reports")
    print("Telemetry: ./data/processed")


if __name__ == "__main__":
    main()
