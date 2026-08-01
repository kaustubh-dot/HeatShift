"""Pure time-grid, heat-band, and directed-matrix helpers."""

from __future__ import annotations

import math
import re
from collections.abc import Mapping, Sequence
from enum import Enum
from numbers import Real

from .models import HeatBand, HeatSlot


_TIME_PATTERN = re.compile(r"^(?P<hour>[01]\d|2[0-3]):(?P<minute>[0-5]\d)$")
_THRESHOLD_NAMES = ("elevated", "severe", "extreme")


def parse_time(value: str) -> int:
    """Return minutes after midnight for an exact ``HH:MM`` value."""

    if not isinstance(value, str):
        raise TypeError("time must be a string in HH:MM format")
    match = _TIME_PATTERN.fullmatch(value)
    if match is None:
        raise ValueError(f"invalid time: {value!r}; expected HH:MM")
    return int(match.group("hour")) * 60 + int(match.group("minute"))


def format_time(minutes_after_midnight: int) -> str:
    """Format minutes after midnight as an exact ``HH:MM`` value."""

    _require_int(minutes_after_midnight, "minutes_after_midnight")
    if not 0 <= minutes_after_midnight < 24 * 60:
        raise ValueError("minutes_after_midnight must be between 0 and 1439")
    hour, minute = divmod(minutes_after_midnight, 60)
    return f"{hour:02d}:{minute:02d}"


def time_to_slot(time: str, day_start: str, slot_minutes: int) -> int:
    """Convert an aligned time to a slot index relative to ``day_start``."""

    _require_positive_int(slot_minutes, "slot_minutes")
    elapsed = parse_time(time) - parse_time(day_start)
    if elapsed < 0:
        raise ValueError("time must not be before day_start")
    if elapsed % slot_minutes:
        raise ValueError("time is not aligned to slot_minutes")
    return elapsed // slot_minutes


def slot_to_time(slot: int, day_start: str, slot_minutes: int) -> str:
    """Convert a non-negative slot index to its local ``HH:MM`` start."""

    _require_int(slot, "slot")
    if slot < 0:
        raise ValueError("slot must be non-negative")
    _require_positive_int(slot_minutes, "slot_minutes")
    return format_time(parse_time(day_start) + slot * slot_minutes)


def duration_to_slots(duration_minutes: int, slot_minutes: int) -> int:
    """Convert an aligned duration to a slot count."""

    _require_int(duration_minutes, "duration_minutes")
    if duration_minutes < 0:
        raise ValueError("duration_minutes must be non-negative")
    _require_positive_int(slot_minutes, "slot_minutes")
    if duration_minutes % slot_minutes:
        raise ValueError("duration_minutes is not aligned to slot_minutes")
    return duration_minutes // slot_minutes


def travel_to_slots(travel_minutes: int, slot_minutes: int) -> int:
    """Reserve ceiling-rounded slots for a directed travel duration."""

    _require_int(travel_minutes, "travel_minutes")
    if travel_minutes < 0:
        raise ValueError("travel_minutes must be non-negative")
    _require_positive_int(slot_minutes, "slot_minutes")
    return (travel_minutes + slot_minutes - 1) // slot_minutes


def build_matrix_index(location_ids: Sequence[str]) -> dict[str, int]:
    """Map each declared matrix location ID to its row/column index."""

    return {location_id: index for index, location_id in enumerate(location_ids)}


def read_travel_minutes(
    from_location_id: str,
    to_location_id: str,
    travel_matrix_location_ids: Sequence[str],
    travel_matrix_minutes: Sequence[Sequence[int]],
) -> int:
    """Read the directed matrix value for ``from_location_id -> to_location_id``."""

    matrix_index = build_matrix_index(travel_matrix_location_ids)
    from_index = matrix_index[from_location_id]
    to_index = matrix_index[to_location_id]
    return travel_matrix_minutes[from_index][to_index]


def remap_temperature(
    temperature_c: Real,
    band_thresholds_c: Mapping[object, Real],
) -> HeatBand:
    """Map a temperature to the greatest inclusive configured heat threshold."""

    _require_real(temperature_c, "temperature_c")
    thresholds = _normalize_thresholds(band_thresholds_c)
    if temperature_c < thresholds["elevated"]:
        return HeatBand.NORMAL

    selected_band = HeatBand.NORMAL
    for band_name in _THRESHOLD_NAMES:
        if temperature_c >= thresholds[band_name]:
            selected_band = HeatBand(band_name)
    return selected_band


def adjust_heat_series(
    heat_series: Sequence[HeatSlot],
    heat_adjustment_c: Real,
    band_thresholds_c: Mapping[object, Real],
) -> list[HeatSlot]:
    """Return an adjusted heat series without mutating its input objects."""

    _require_real(heat_adjustment_c, "heat_adjustment_c")
    adjusted: list[HeatSlot] = []
    for heat_slot in heat_series:
        adjusted_temperature = heat_slot.temperature_c + heat_adjustment_c
        adjusted.append(
            heat_slot.model_copy(
                deep=True,
                update={
                    "temperature_c": adjusted_temperature,
                    "band": remap_temperature(adjusted_temperature, band_thresholds_c),
                },
            )
        )
    return adjusted


def _normalize_thresholds(band_thresholds_c: Mapping[object, Real]) -> dict[str, Real]:
    normalized: dict[str, Real] = {}
    for key, value in band_thresholds_c.items():
        name = key.value if isinstance(key, Enum) else key
        if isinstance(name, str):
            normalized[name] = value
    return {name: normalized[name] for name in _THRESHOLD_NAMES}


def _require_int(value: object, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")


def _require_positive_int(value: object, field_name: str) -> None:
    _require_int(value, field_name)
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")


def _require_real(value: object, field_name: str) -> None:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{field_name} must be a finite number")
    if not math.isfinite(float(value)):
        raise ValueError(f"{field_name} must be finite")
