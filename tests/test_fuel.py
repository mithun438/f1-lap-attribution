import pytest
from src.telemetry.fuel import FuelCorrectionModel, normalize_delta_for_fuel


def test_penalty_seconds_linear():
    m = FuelCorrectionModel(coeff_s_per_kg=0.03)
    assert abs(m.penalty_seconds(10.0) - 0.3) < 1e-12


def test_normalize_lap_time_removes_penalty():
    m = FuelCorrectionModel(coeff_s_per_kg=0.03)
    # Lap time with 20kg fuel includes +0.6s penalty -> normalized should subtract it
    assert abs(m.normalize_lap_time(80.6, fuel_kg=20.0) - 80.0) < 1e-12


def test_delta_fuel_correction_sign():
    # delta = tgt - ref
    # If tgt carries +10kg more fuel, expected fuel penalty in delta = +0.3s
    corrected = normalize_delta_for_fuel(
        0.5, ref_fuel_kg=5.0, tgt_fuel_kg=15.0, coeff_s_per_kg=0.03
    )
    assert abs(corrected - 0.2) < 1e-12


def test_invalid_inputs():
    m = FuelCorrectionModel()
    with pytest.raises(ValueError):
        m.penalty_seconds(-1.0)
    with pytest.raises(ValueError):
        m.normalize_lap_time(-10.0, fuel_kg=5.0)
    with pytest.raises(ValueError):
        normalize_delta_for_fuel(0.1, ref_fuel_kg=-1.0, tgt_fuel_kg=10.0)
