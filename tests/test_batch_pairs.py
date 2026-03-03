from __future__ import annotations

from src.cli.batch_compare import _pairs


def test_pairs_upper_triangle():
    assert _pairs(["A", "B", "C"]) == [("A", "B"), ("A", "C"), ("B", "C")]
