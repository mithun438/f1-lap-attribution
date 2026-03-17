from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FuelCorrectionModel:
    """
    Simple linear fuel correction model.

    Assumption (rule-of-thumb):
      lap_time_penalty_seconds ≈ coeff_s_per_kg * fuel_kg

    Typical heuristic: ~0.03 s/kg (varies by track/car/era).
    """

    coeff_s_per_kg: float = 0.03

    def penalty_seconds(self, fuel_kg: float) -> float:
        if fuel_kg < 0:
            raise ValueError("fuel_kg must be >= 0")
        return self.coeff_s_per_kg * fuel_kg

    def normalize_lap_time(self, lap_time_s: float, *, fuel_kg: float) -> float:
        """
        Normalize (remove) the fuel penalty from a lap time.
        Returns: lap_time_s - penalty(fuel_kg)
        """
        if lap_time_s <= 0:
            raise ValueError("lap_time_s must be > 0")
        return lap_time_s - self.penalty_seconds(fuel_kg)


def normalize_delta_for_fuel(
    delta_lap_time_s: float,
    *,
    ref_fuel_kg: float,
    tgt_fuel_kg: float,
    coeff_s_per_kg: float = 0.03,
) -> float:
    """
    Fuel-correct a lap delta:
      delta = tgt - ref

    If target has more fuel than reference, part of delta may be due to fuel.
    We subtract the differential fuel penalty:

      corrected_delta = (tgt - ref) - coeff*(tgt_fuel - ref_fuel)

    Note: This is only meaningful when ref/tgt laps are comparable (same track state etc.)
    """
    if ref_fuel_kg < 0 or tgt_fuel_kg < 0:
        raise ValueError("fuel values must be >= 0")
    fuel_diff = tgt_fuel_kg - ref_fuel_kg
    return float(delta_lap_time_s) - float(coeff_s_per_kg) * float(fuel_diff)
