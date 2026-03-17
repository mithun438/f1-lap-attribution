from __future__ import annotations

from pathlib import Path

import yaml


def test_config_file_can_be_written_and_loaded(tmp_path: Path):
    cfg = {
        "year": 2023,
        "gp": "Italy",
        "session": "Q",
        "drivers": ["VER", "LEC", "SAI"],
        "jobs": 2,
        "write_plots": False,
        "fuel_coeff": 0.03,
        "distance_step_m": 1.0,
        "config": "config/default.yaml",
    }

    p = tmp_path / "run.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    loaded = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert loaded["year"] == 2023
    assert loaded["gp"] == "Italy"
    assert loaded["session"] == "Q"
    assert loaded["drivers"] == ["VER", "LEC", "SAI"]
