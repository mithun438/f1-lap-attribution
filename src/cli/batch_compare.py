# src/cli/batch_compare.py
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from src.cli.run_pipeline import run_one
from src.reports.html_index import write_batch_index


def _pairs(drivers: list[str]) -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for i in range(len(drivers)):
        for j in range(i + 1, len(drivers)):
            out.append((drivers[i], drivers[j]))
    return out


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser()
    p.add_argument("--config", type=Path, default=Path("config/default.yaml"))
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--gp", type=str, required=True)
    p.add_argument("--session", type=str, required=True)
    p.add_argument("--drivers", type=str, required=True, help="Comma-separated, e.g. VER,LEC,SAI")
    p.add_argument("--jobs", type=int, default=1)
    p.add_argument("--out-dir", type=Path, default=None)
    p.add_argument("--distance-step-m", type=float, default=None)
    p.add_argument("--fuel-coeff", type=float, default=None)
    p.add_argument("--write-plots", dest="write_plots", action="store_true", default=None)
    p.add_argument("--no-plots", dest="write_plots", action="store_false")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    safe_gp = args.gp.replace(" ", "_")
    run_dir = Path("reports") / f"{args.year}_{safe_gp}_{args.session}"
    final_out_dir = args.out_dir if args.out_dir is not None else run_dir
    final_out_dir.mkdir(parents=True, exist_ok=True)

    drivers = [d.strip() for d in args.drivers.split(",") if d.strip()]
    pairs = _pairs(drivers)

    rows: list[dict] = []

    if args.jobs <= 1:
        for k, (ref, tgt) in enumerate(pairs, start=1):
            out_tag = f"batch_{ref}_vs_{tgt}"
            print(f"[{k}/{len(pairs)}] {ref} vs {tgt}")
            rows.append(
                run_one(
                    year=args.year,
                    gp=args.gp,
                    session=args.session,
                    ref=ref,
                    tgt=tgt,
                    out_tag=out_tag,
                    config_path=args.config,
                    distance_step_m=args.distance_step_m,
                    fuel_coeff=args.fuel_coeff,
                    out_dir=final_out_dir,
                    write_plots=args.write_plots,
                )
            )
    else:
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            futs = []
            cache_root = final_out_dir / "_cache"
            cache_root.mkdir(parents=True, exist_ok=True)

            for ref, tgt in pairs:
                out_tag = f"batch_{ref}_vs_{tgt}"
                pair_cache = cache_root / f"{ref}_vs_{tgt}"
                futs.append(
                    ex.submit(
                        run_one,
                        year=args.year,
                        gp=args.gp,
                        session=args.session,
                        ref=ref,
                        tgt=tgt,
                        out_tag=out_tag,
                        config_path=args.config,
                        distance_step_m=args.distance_step_m,
                        fuel_coeff=args.fuel_coeff,
                        out_dir=final_out_dir,
                        write_plots=args.write_plots,
                        cache_dir=pair_cache,
                    )
                )

            done = 0
            for f in as_completed(futs):
                rows.append(f.result())
                done += 1
                print(f"[{done}/{len(futs)}] done")

    df = pd.DataFrame(rows)

    preferred_cols = [
        "ref",
        "tgt",
        "ref_lap_time_s",
        "tgt_lap_time_s",
        "delta_lap_time_s",
        "straight_time_loss_s",
        "fuel_corrected_delta_s",
        "fuel_penalty_delta_s",
        "year",
        "gp",
        "session",
        "out_tag",
    ]
    existing_cols = [c for c in preferred_cols if c in df.columns]
    remaining_cols = [c for c in df.columns if c not in existing_cols]
    df = df[existing_cols + remaining_cols]

    if "delta_lap_time_s" in df.columns:
        df["abs_delta_lap_time_s"] = df["delta_lap_time_s"].abs()

    out_csv = final_out_dir / "batch_summary.csv"
    df.sort_values(["ref", "tgt"]).to_csv(out_csv, index=False)
    print(f"Wrote: {out_csv}")

    ranked_csv = None
    if "abs_delta_lap_time_s" in df.columns:
        ranked_csv = final_out_dir / "batch_summary_ranked.csv"
        df.sort_values("abs_delta_lap_time_s", ascending=False).to_csv(ranked_csv, index=False)
        print(f"Wrote: {ranked_csv}")

    write_batch_index(
        out_dir=final_out_dir,
        summary_csv=out_csv,
        ranked_csv=ranked_csv,
    )


if __name__ == "__main__":
    main()
