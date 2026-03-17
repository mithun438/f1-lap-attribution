from __future__ import annotations

from pathlib import Path

import yaml


def test_experiment_config_schema(tmp_path: Path):
    cfg = {
        "year": 2023,
        "gp": "Italy",
        "session": "Q",
        "drivers": ["VER", "LEC", "SAI"],
        "jobs": 2,
        "write_plots": False,
        "experiments": {
            "distance_step_m": [0.5, 1.0],
            "fuel_coeff": [0.02, 0.03],
        },
    }

    p = tmp_path / "exp.yaml"
    p.write_text(yaml.safe_dump(cfg), encoding="utf-8")

    loaded = yaml.safe_load(p.read_text(encoding="utf-8"))
    assert loaded["year"] == 2023
    assert loaded["experiments"]["distance_step_m"] == [0.5, 1.0]
    assert loaded["experiments"]["fuel_coeff"] == [0.02, 0.03]
