from pathlib import Path

import yaml


def test_runs_yaml_can_be_loaded(tmp_path: Path):
    data = {
        "runs": [
            "config/run_italy_q.yaml",
            "config/run_italy_q.yaml",
        ]
    }

    p = tmp_path / "runs.yaml"
    p.write_text(yaml.safe_dump(data), encoding="utf-8")

    loaded = yaml.safe_load(p.read_text(encoding="utf-8"))

    assert "runs" in loaded
    assert isinstance(loaded["runs"], list)
