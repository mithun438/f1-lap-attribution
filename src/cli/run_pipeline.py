from __future__ import annotations

import argparse
from pathlib import Path

from src.config import load_pipeline_config
from src.data.fastf1_utils import pull_fastest_lap_pair
from src.reports.plot_delta_time import run_delta_plot


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
    )

    applied_correction_s = None
    fuel_penalty_delta = None
    if ref_fuel_kg is not None and tgt_fuel_kg is not None:
        fuel_delta = tgt_fuel_kg - ref_fuel_kg
        fuel_penalty_delta = fuel_delta * fuel_coeff
        applied_correction_s = -fuel_penalty_delta

    final_delta_s = run_delta_plot(
        ref_path,
        tgt_path,
        out_tag=out_tag,
        distance_step_m=distance_step_m,
        out_dir=out_dir,
        applied_correction_s=applied_correction_s,
        write_plots=write_plots,
    )

    # keep your existing segments/attribution calls unchanged but use out_dir/write_plots as needed

    return {
        "year": year,
        "gp": gp,
        "session": session,
        "ref": ref,
        "tgt": tgt,
        "out_tag": out_tag,
        "final_delta_s": float(final_delta_s),
        "fuel_penalty_delta_s": (
            float(fuel_penalty_delta) if fuel_penalty_delta is not None else None
        ),
        "applied_correction_s": (
            float(applied_correction_s) if applied_correction_s is not None else None
        ),
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
        out_dir=Path(args.out_dir) if args.out_dir is not None else None,
        write_plots=args.write_plots,
    )
    print(f"Final Δlap time (s): {result['final_delta_s']}")
