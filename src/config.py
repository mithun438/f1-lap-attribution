# src/config.py
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class PipelineConfig:
    distance_step_m: float = 1.0
    fuel_coeff: float = 0.03
    out_dir: Path = Path("reports")
    write_plots: bool = True


def _as_bool(x: Any) -> bool:
    if isinstance(x, bool):
        return x
    if isinstance(x, str):
        v = x.strip().lower()
        if v in {"true", "1", "yes", "y", "on"}:
            return True
        if v in {"false", "0", "no", "n", "off"}:
            return False
    raise ValueError(f"Invalid bool value: {x!r}")


def load_pipeline_config(path: Path) -> PipelineConfig:
    if not path.exists():
        raise FileNotFoundError(path)

    data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise ValueError("Config must be a YAML mapping/dict")

    kwargs: dict[str, Any] = {}

    if "distance_step_m" in data:
        kwargs["distance_step_m"] = float(data["distance_step_m"])

    if "fuel_coeff" in data:
        kwargs["fuel_coeff"] = float(data["fuel_coeff"])

    if "out_dir" in data:
        kwargs["out_dir"] = Path(str(data["out_dir"]))

    if "write_plots" in data:
        kwargs["write_plots"] = _as_bool(data["write_plots"])

    return PipelineConfig(**kwargs)
