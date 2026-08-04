from __future__ import annotations

import pytest

from backend.heatshift.models import HeatBand, HeatSlot
from backend.heatshift.timegrid import (
    adjust_heat_series,
    build_matrix_index,
    duration_to_slots,
    format_time,
    parse_time,
    read_travel_minutes,
    remap_temperature,
    slot_to_time,
    time_to_slot,
    travel_to_slots,
)


THRESHOLDS = {"elevated": 32, "severe": 38, "extreme": 42}


def test_parse_and_format_hhmm() -> None:
    assert parse_time("07:00") == 420
    assert parse_time("17:00") == 1020
    assert format_time(420) == "07:00"
    assert format_time(1020) == "17:00"


def test_demo_times_map_to_expected_slots() -> None:
    assert time_to_slot("07:00", "07:00", 15) == 0
    assert time_to_slot("09:15", "07:00", 15) == 9
    assert time_to_slot("17:00", "07:00", 15) == 40
    assert slot_to_time(0, "07:00", 15) == "07:00"
    assert slot_to_time(40, "07:00", 15) == "17:00"


def test_aligned_duration_and_ceiling_travel_conversion() -> None:
    assert duration_to_slots(90, 15) == 6
    assert travel_to_slots(14, 15) == 1
    assert travel_to_slots(16, 15) == 2

    with pytest.raises(ValueError):
        duration_to_slots(10, 15)


def test_inclusive_temperature_thresholds() -> None:
    assert remap_temperature(31.9, THRESHOLDS) == HeatBand.NORMAL
    assert remap_temperature(32, THRESHOLDS) == HeatBand.ELEVATED
    assert remap_temperature(38, THRESHOLDS) == HeatBand.SEVERE
    assert remap_temperature(42, THRESHOLDS) == HeatBand.EXTREME


def test_adjustment_does_not_mutate_original_heat_series() -> None:
    original = [
        HeatSlot(slot=0, start="07:00", temperature_c=31, band="normal"),
        HeatSlot(slot=1, start="07:15", temperature_c=32, band="elevated"),
    ]

    adjusted = adjust_heat_series(original, 2, THRESHOLDS)

    assert [slot.temperature_c for slot in original] == [31, 32]
    assert [slot.band for slot in original] == [HeatBand.NORMAL, HeatBand.ELEVATED]
    assert [slot.temperature_c for slot in adjusted] == [33, 34]
    assert [slot.band for slot in adjusted] == [HeatBand.ELEVATED, HeatBand.ELEVATED]
    assert adjusted[0] is not original[0]


def test_directed_matrix_lookup_preserves_row_column_direction() -> None:
    location_ids = ["depot-central", "loc-d107"]
    matrix = [[0, 14], [13, 0]]

    assert build_matrix_index(location_ids) == {
        "depot-central": 0,
        "loc-d107": 1,
    }
    assert read_travel_minutes("depot-central", "loc-d107", location_ids, matrix) == 14
    assert read_travel_minutes("loc-d107", "depot-central", location_ids, matrix) == 13


@pytest.mark.parametrize("value", ["7:00", "25:00", "07:60", "noon"])
def test_invalid_time_text_is_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        parse_time(value)
