from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd
from src.config import load_pipeline_config
from src.data.fastf1_utils import pull_fastest_lap_pair
from src.reports.export_comparison_table import export_comparison_table
from src.reports.html_report import write_html_report
from src.reports.plot_delta_time import run_delta_plot
from src.telemetry.physics import estimate_straight_time_loss


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
    ap.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="Override output directory (defaults to config value)",
    )
    ap.add_argument(
        "--write-plots",
        dest="write_plots",
        action="store_true",
        default=None,
        help="Force plot writing on",
    )
    ap.add_argument(
        "--no-plots",
        dest="write_plots",
        action="store_false",
        help="Disable plot writing",
    )

    return ap.parse_args()


def _extract_lap_time_seconds(path: Path) -> float | None:
    """
    Best-effort extraction of lap time from a parquet telemetry trace.

    Expected preference:
      - 'lap_time_s' column
      - 'time_s' column

    Returns the final value in seconds, or None if unavailable.
    """
    df = pd.read_parquet(path)

    if "lap_time_s" in df.columns and len(df) > 0:
        return float(df["lap_time_s"].iloc[-1])

    if "time_s" in df.columns and len(df) > 0:
        return float(df["time_s"].iloc[-1])

    return None


def run_one(
    *,
    year: int,
    gp: str,
    session: str,
    ref: str,
    tgt: str,
    out_tag: str,
    config_path: Path,
    ref_fuel_kg: float | None = None,
    tgt_fuel_kg: float | None = None,
    distance_step_m: float | None = None,
    fuel_coeff: float | None = None,
    out_dir: Path | None = None,
    write_plots: bool | None = None,
    cache_dir: Path | None = None,
) -> dict:
    cfg = load_pipeline_config(config_path)

    distance_step_m = distance_step_m if distance_step_m is not None else cfg.distance_step_m
    fuel_coeff = fuel_coeff if fuel_coeff is not None else cfg.fuel_coeff
    out_dir = out_dir if out_dir is not None else cfg.out_dir
    write_plots = write_plots if write_plots is not None else cfg.write_plots

    ref_path, tgt_path = pull_fastest_lap_pair(
        year=year,
        gp=gp,
        session=session,
        ref_driver=ref,
        tgt_driver=tgt,
        out_dir=out_dir,
        out_tag=out_tag,
        cache_dir=cache_dir,
    )

    ref_lap_s = _extract_lap_time_seconds(ref_path)
    tgt_lap_s = _extract_lap_time_seconds(tgt_path)

    applied_correction_s = None
    fuel_penalty_delta_s = None
    if ref_fuel_kg is not None and tgt_fuel_kg is not None:
        fuel_delta = tgt_fuel_kg - ref_fuel_kg
        fuel_penalty_delta_s = fuel_delta * fuel_coeff
        applied_correction_s = -fuel_penalty_delta_s

    final_delta_s = run_delta_plot(
        ref_path,
        tgt_path,
        out_tag=out_tag,
        distance_step_m=distance_step_m,
        out_dir=out_dir,
        applied_correction_s=applied_correction_s,
        write_plots=write_plots,
    )

    comparison_table_path = export_comparison_table(
        ref_path,
        tgt_path,
        out_dir=out_dir,
        out_tag=out_tag,
        distance_step_m=distance_step_m,
    )

    comparison_df = pd.read_csv(comparison_table_path)
    straight_time_loss_s = estimate_straight_time_loss(comparison_df)

    fuel_corrected_delta_s = (
        float(final_delta_s + applied_correction_s) if applied_correction_s is not None else None
    )

    report_path = write_html_report(
        out_dir=out_dir,
        out_tag=out_tag,
        delta_s=final_delta_s,
        ref=ref,
        tgt=tgt,
        ref_lap_s=ref_lap_s,
        tgt_lap_s=tgt_lap_s,
        fuel_corrected_delta_s=fuel_corrected_delta_s,
    )

    return {
        "year": year,
        "gp": gp,
        "session": session,
        "ref": ref,
        "tgt": tgt,
        "delta_lap_time_s": float(final_delta_s),
        "ref_lap_time_s": ref_lap_s,
        "tgt_lap_time_s": tgt_lap_s,
        "fuel_corrected_delta_s": fuel_corrected_delta_s,
        "out_tag": out_tag,
        "final_delta_s": float(final_delta_s),
        "fuel_penalty_delta_s": (
            float(fuel_penalty_delta_s) if fuel_penalty_delta_s is not None else None
        ),
        "applied_correction_s": (
            float(applied_correction_s) if applied_correction_s is not None else None
        ),
        "comparison_table_csv": str(comparison_table_path),
        "html_report": str(report_path),
        "straight_time_loss_s": straight_time_loss_s,
    }


def main() -> None:
    args = parse_args()

    result = run_one(
        year=args.year,
        gp=args.gp,
        session=args.session,
        ref=args.ref,
        tgt=args.tgt,
        out_tag=args.out_tag,
        config_path=args.config,
        ref_fuel_kg=args.ref_fuel_kg,
        tgt_fuel_kg=args.tgt_fuel_kg,
        distance_step_m=args.distance_step_m,
        fuel_coeff=args.fuel_coeff,
        out_dir=args.out_dir,
        write_plots=args.write_plots,
    )
    print(f"Final Δlap time (s): {result['final_delta_s']}")


if __name__ == "__main__":
    main()
