from __future__ import annotations

from pathlib import Path

import pandas as pd
import streamlit as st

REPORTS_DIR = Path("reports")


def list_runs() -> list[Path]:
    if not REPORTS_DIR.exists():
        return []
    return sorted([p for p in REPORTS_DIR.iterdir() if p.is_dir()])


def load_summary(run_dir: Path) -> pd.DataFrame | None:
    ranked = run_dir / "batch_summary_ranked.csv"
    plain = run_dir / "batch_summary.csv"

    if ranked.exists():
        return pd.read_csv(ranked)
    if plain.exists():
        return pd.read_csv(plain)
    return None


def main() -> None:
    st.set_page_config(page_title="F1 Lap Attribution Dashboard", layout="wide")
    st.title("F1 Lap Attribution Dashboard")

    runs = list_runs()
    if not runs:
        st.warning("No report runs found under ./reports")
        return

    run_names = [r.name for r in runs]
    selected_run_name = st.sidebar.selectbox("Run", run_names)
    run_dir = REPORTS_DIR / selected_run_name

    st.sidebar.markdown(f"**Folder:** `{run_dir}`")

    df = load_summary(run_dir)
    if df is None:
        st.warning("No batch summary CSV found in selected run.")
        return

    st.subheader("Batch summary")
    st.dataframe(df, use_container_width=True)

    if "out_tag" not in df.columns:
        st.warning("Summary CSV is missing 'out_tag' column.")
        return

    comparison_tags = df["out_tag"].dropna().astype(str).tolist()
    selected_tag = st.selectbox("Comparison", comparison_tags)

    selected_row = df[df["out_tag"] == selected_tag].iloc[0]

    col1, col2, col3 = st.columns(3)
    with col1:
        if "ref" in selected_row:
            st.metric("Reference", selected_row["ref"])
    with col2:
        if "tgt" in selected_row:
            st.metric("Target", selected_row["tgt"])
    with col3:
        if "delta_lap_time_s" in selected_row:
            st.metric("Delta lap time (s)", f"{selected_row['delta_lap_time_s']:.6f}")

    raw_plot = run_dir / f"{selected_tag}_delta_time_vs_distance.png"
    fuel_plot = run_dir / f"{selected_tag}_delta_time_vs_distance_fuel_corrected.png"
    html_report = run_dir / f"{selected_tag}_report.html"
    comparison_csv = run_dir / f"{selected_tag}_comparison_table.csv"

    st.subheader("Plots")

    if raw_plot.exists():
        st.image(str(raw_plot), caption=raw_plot.name)
    else:
        st.info("Raw delta plot not found.")

    if fuel_plot.exists():
        st.image(str(fuel_plot), caption=fuel_plot.name)

    st.subheader("Comparison table")

    if comparison_csv.exists():
        comp_df = pd.read_csv(comparison_csv)
        st.dataframe(comp_df.head(200), use_container_width=True)
        st.caption(f"Showing first 200 rows from {comparison_csv.name}")
    else:
        st.info("Comparison CSV not found.")

    st.subheader("Artifacts")

    st.write(f"Run folder: `{run_dir}`")
    if html_report.exists():
        st.write(f"HTML report: `{html_report.name}`")
    if comparison_csv.exists():
        st.write(f"Comparison CSV: `{comparison_csv.name}`")


if __name__ == "__main__":
    main()
