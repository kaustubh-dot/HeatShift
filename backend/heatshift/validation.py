"""Cross-reference and semantic validation for scenario and policy inputs."""

from __future__ import annotations

import math
from collections.abc import Callable, Iterable, Mapping, Sequence
from numbers import Real

from .models import ApiErrorDetail, HeatBand, Policy, Scenario
from .timegrid import parse_time


_THRESHOLD_NAMES = ("elevated", "severe", "extreme")
_HEAT_BANDS = tuple(band.value for band in HeatBand)
_EXERTIONS = ("heavy", "moderate")


class ScenarioValidationError(ValueError):
    """Domain error used by an API boundary after collecting validation issues."""

    def __init__(self, issues: Sequence[ApiErrorDetail]) -> None:
        self.issues = tuple(issues)
        summary = "; ".join(f"{issue.path}: {issue.message}" for issue in self.issues)
        super().__init__(summary or "scenario and policy validation failed")


def validate_scenario(scenario: Scenario, policy: Policy) -> list[ApiErrorDetail]:
    """Return every discovered issue in deterministic path order.

    Pydantic owns shape and vocabulary validation. This function owns the
    relationships and semantic constraints that require both inputs. It is
    intentionally solver-free so invalid input can be rejected before any
    CP-SAT model is built.
    """

    issues: list[ApiErrorDetail] = []

    def add(path: str, code: str, message: str) -> None:
        issues.append(ApiErrorDetail(path=path, code=code, message=message))

    _check_unique_ids(scenario.crews, "crews", "id", add)
    _check_unique_ids(scenario.jobs, "jobs", "id", add)
    location_ids = _check_unique_ids(scenario.locations, "locations", "id", add)
    _check_unique_ids(scenario.heat_series, "heat_series", "slot", add)
    _check_unique_ids(policy.rules, "rules", "id", add)

    if scenario.policy_id != policy.id:
        add(
            "policy_id",
            "POLICY_MISMATCH",
            f"scenario policy_id {scenario.policy_id!r} does not match policy id {policy.id!r}",
        )

    day_start = _safe_parse_time(scenario.day_start)
    day_end = _safe_parse_time(scenario.day_end)
    valid_slot_minutes = _is_positive_int(scenario.slot_minutes)
    horizon_minutes: int | None = None
    if day_start is not None and day_end is not None:
        if day_start >= day_end:
            add("day_start", "INVALID_TIME_WINDOW", "day_start must be before day_end")
        else:
            horizon_minutes = day_end - day_start
            if not valid_slot_minutes:
                add("slot_minutes", "INVALID_TIME_GRID", "slot_minutes must be a positive integer")
            elif horizon_minutes % scenario.slot_minutes:
                add(
                    "day_end",
                    "NOT_SLOT_ALIGNED",
                    "the planning horizon must divide evenly into slot_minutes",
                )
    elif not valid_slot_minutes:
        add("slot_minutes", "INVALID_TIME_GRID", "slot_minutes must be a positive integer")

    _check_time_bounds_and_alignment(
        scenario,
        day_start,
        day_end,
        valid_slot_minutes,
        add,
    )

    crew_by_id = _first_by_id(scenario.crews, "id")
    location_id_set = set(location_ids)
    for index, crew in enumerate(scenario.crews):
        for field_name in ("start_depot_id", "end_depot_id"):
            depot_id = getattr(crew, field_name, None)
            if depot_id not in location_id_set:
                add(
                    f"crews[{index}].{field_name}",
                    "UNKNOWN_REFERENCE",
                    f"unknown location ID {depot_id!r}",
                )

    for index, job in enumerate(scenario.jobs):
        if job.location_id not in location_id_set:
            add(
                f"jobs[{index}].location_id",
                "UNKNOWN_REFERENCE",
                f"unknown location ID {job.location_id!r}",
            )

        if job.locked_crew_id is not None and job.locked_crew_id not in crew_by_id:
            add(
                f"jobs[{index}].locked_crew_id",
                "UNKNOWN_REFERENCE",
                f"unknown crew ID {job.locked_crew_id!r}",
            )

    _check_job_eligibility_and_references(scenario, crew_by_id, add)
    _check_heat_series(scenario, policy, day_start, day_end, horizon_minutes, add)
    _check_thresholds(policy, add)
    _check_policy_rules(scenario, policy, add)
    _check_rule_values(policy, add)
    _check_matrix(scenario, location_ids, add)

    # Sorting by path makes errors stable even when validation loops are
    # refactored or input lists contain errors in different rule categories.
    issues.sort(key=lambda issue: (issue.path, issue.code, issue.message))
    return issues


def require_valid_scenario(scenario: Scenario, policy: Policy) -> None:
    """Raise one domain exception if the supplied inputs are not valid."""

    issues = validate_scenario(scenario, policy)
    if issues:
        raise ScenarioValidationError(issues)


def _check_unique_ids(
    values: Sequence[object],
    collection_path: str,
    field_name: str,
    add: Callable[[str, str, str], None],
) -> list[object]:
    seen: dict[object, int] = {}
    ids: list[object] = []
    for index, value in enumerate(values):
        identifier = getattr(value, field_name, None)
        ids.append(identifier)
        if identifier in seen:
            add(
                f"{collection_path}[{index}].{field_name}",
                "DUPLICATE_ID",
                f"duplicate ID {identifier!r}; first seen at {collection_path}[{seen[identifier]}].{field_name}",
            )
        else:
            seen[identifier] = index
    return ids


def _first_by_id(values: Iterable[object], field_name: str) -> dict[object, object]:
    result: dict[object, object] = {}
    for value in values:
        identifier = getattr(value, field_name, None)
        result.setdefault(identifier, value)
    return result


def _safe_parse_time(value: object) -> int | None:
    if not isinstance(value, str):
        return None
    try:
        return parse_time(value)
    except (TypeError, ValueError):
        return None


def _is_positive_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_finite_number(value: object) -> bool:
    return isinstance(value, Real) and not isinstance(value, bool) and math.isfinite(float(value))


def _check_time_bounds_and_alignment(
    scenario: Scenario,
    day_start: int | None,
    day_end: int | None,
    valid_slot_minutes: bool,
    add: Callable[[str, str, str], None],
) -> None:
    if day_start is None or day_end is None or not valid_slot_minutes:
        return

    def check_time(path: str, value: object, *, allow_end: bool = True) -> int | None:
        parsed = _safe_parse_time(value)
        if parsed is None:
            return None
        if parsed < day_start or parsed > day_end or (not allow_end and parsed == day_end):
            add(path, "OUT_OF_HORIZON", "time must lie inside the planning horizon")
        elif (parsed - day_start) % scenario.slot_minutes:
            add(path, "NOT_SLOT_ALIGNED", "time must align to slot_minutes from day_start")
        return parsed

    for index, crew in enumerate(scenario.crews):
        start_path = f"crews[{index}].shift_start"
        end_path = f"crews[{index}].shift_end"
        start = check_time(start_path, crew.shift_start)
        end = check_time(end_path, crew.shift_end)
        if start is not None and end is not None and start >= end:
            add(start_path, "INVALID_TIME_WINDOW", "crew shift_start must be before shift_end")

    for index, job in enumerate(scenario.jobs):
        start_path = f"jobs[{index}].window_start"
        end_path = f"jobs[{index}].window_end"
        start = check_time(start_path, job.window_start)
        end = check_time(end_path, job.window_end)
        if start is not None and end is not None and start >= end:
            add(start_path, "INVALID_TIME_WINDOW", "job window_start must be before window_end")

        if not _is_positive_or_zero_int(job.active_minutes):
            add(
                f"jobs[{index}].active_minutes",
                "INVALID_DURATION",
                "active_minutes must be a non-negative integer",
            )
        elif job.active_minutes % scenario.slot_minutes:
            add(
                f"jobs[{index}].active_minutes",
                "NOT_SLOT_ALIGNED",
                "active_minutes must align to slot_minutes",
            )

        if job.locked_start is not None:
            locked_path = f"jobs[{index}].locked_start"
            locked = check_time(locked_path, job.locked_start, allow_end=False)
            if locked is not None and start is not None and end is not None and not (start <= locked < end):
                add(locked_path, "INVALID_LOCK", "locked_start must lie inside the job window")


def _is_positive_or_zero_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _check_job_eligibility_and_references(
    scenario: Scenario,
    crew_by_id: Mapping[object, object],
    add: Callable[[str, str, str], None],
) -> None:
    crews = list(crew_by_id.values())
    all_capabilities = {
        tag
        for crew in crews
        for tag in getattr(crew, "capabilities", ())
    }
    all_equipment = {
        tag
        for crew in crews
        for tag in getattr(crew, "equipment", ())
    }

    for job_index, job in enumerate(scenario.jobs):
        for tag_index, capability in enumerate(job.required_capabilities):
            if capability not in all_capabilities:
                add(
                    f"jobs[{job_index}].required_capabilities[{tag_index}]",
                    "UNKNOWN_REFERENCE",
                    f"no crew declares capability {capability!r}",
                )
        for tag_index, equipment in enumerate(job.required_equipment):
            if equipment not in all_equipment:
                add(
                    f"jobs[{job_index}].required_equipment[{tag_index}]",
                    "UNKNOWN_REFERENCE",
                    f"no crew declares equipment {equipment!r}",
                )

        eligible = [
            crew
            for crew in crews
            if set(job.required_capabilities).issubset(set(getattr(crew, "capabilities", ())))
            and set(job.required_equipment).issubset(set(getattr(crew, "equipment", ())))
        ]

        if job.locked_crew_id is not None:
            locked_crew = crew_by_id.get(job.locked_crew_id)
            if locked_crew is not None and locked_crew not in eligible:
                add(
                    f"jobs[{job_index}].locked_crew_id",
                    "INELIGIBLE_CREW",
                    "locked crew does not satisfy every required capability and equipment tag",
                )

        if job.locked and not eligible:
            add(
                f"jobs[{job_index}].id",
                "NO_ELIGIBLE_CREW",
                "locked job has no eligible crew",
            )


def _check_heat_series(
    scenario: Scenario,
    policy: Policy,
    day_start: int | None,
    day_end: int | None,
    horizon_minutes: int | None,
    add: Callable[[str, str, str], None],
) -> None:
    slot_values = [getattr(slot, "slot", None) for slot in scenario.heat_series]
    has_duplicate_slots = len(slot_values) != len(set(slot_values))

    expected_count: int | None = None
    if (
        day_start is not None
        and day_end is not None
        and horizon_minutes is not None
        and _is_positive_int(scenario.slot_minutes)
        and horizon_minutes % scenario.slot_minutes == 0
    ):
        expected_count = horizon_minutes // scenario.slot_minutes
        if len(scenario.heat_series) != expected_count:
            add(
                "heat_series",
                "INVALID_HEAT_SERIES",
                f"heat_series must contain exactly {expected_count} slots",
            )

    if not has_duplicate_slots:
        for index, slot in enumerate(scenario.heat_series):
            if getattr(slot, "slot", None) != index:
                add(
                    f"heat_series[{index}].slot",
                    "INVALID_HEAT_SERIES",
                    "heat slots must be contiguous and ordered from slot 0",
                )

    thresholds = _normalized_thresholds(policy.band_thresholds_c)
    thresholds_valid = _thresholds_are_strict(thresholds)
    for index, slot in enumerate(scenario.heat_series):
        slot_number = getattr(slot, "slot", None)
        if (
            day_start is not None
            and _is_positive_int(scenario.slot_minutes)
            and isinstance(slot_number, int)
            and not isinstance(slot_number, bool)
        ):
            expected_start = day_start + slot_number * scenario.slot_minutes
            actual_start = _safe_parse_time(getattr(slot, "start", None))
            if actual_start != expected_start:
                add(
                    f"heat_series[{index}].start",
                    "NOT_SLOT_ALIGNED",
                    "heat slot start does not match its slot index",
                )

        if thresholds_valid and _is_finite_number(getattr(slot, "temperature_c", None)):
            expected_band = _band_for_temperature(float(slot.temperature_c), thresholds)
            actual_band = _enum_value(getattr(slot, "band", None))
            if actual_band != expected_band:
                add(
                    f"heat_series[{index}].band",
                    "INVALID_HEAT_BAND",
                    f"temperature maps to heat band {expected_band!r}, not {actual_band!r}",
                )


def _normalized_thresholds(values: Mapping[object, object]) -> dict[str, object]:
    normalized: dict[str, object] = {}
    for key, value in values.items():
        name = _enum_value(key)
        if isinstance(name, str):
            normalized[name] = value
    return normalized


def _thresholds_are_strict(thresholds: Mapping[str, object]) -> bool:
    if set(thresholds) != set(_THRESHOLD_NAMES):
        return False
    values = [thresholds[name] for name in _THRESHOLD_NAMES]
    return all(_is_finite_number(value) for value in values) and all(
        values[index] < values[index + 1] for index in range(len(values) - 1)
    )


def _check_thresholds(policy: Policy, add: Callable[[str, str, str], None]) -> bool:
    thresholds = _normalized_thresholds(policy.band_thresholds_c)
    if set(thresholds) != set(_THRESHOLD_NAMES):
        add(
            "band_thresholds_c",
            "INVALID_THRESHOLD",
            "threshold keys must be exactly elevated, severe, and extreme",
        )
        return False

    values = [thresholds[name] for name in _THRESHOLD_NAMES]
    if not all(_is_finite_number(value) for value in values):
        add(
            "band_thresholds_c",
            "INVALID_THRESHOLD",
            "threshold values must be finite numbers",
        )
        return False
    if not all(values[index] < values[index + 1] for index in range(len(values) - 1)):
        add(
            "band_thresholds_c",
            "INVALID_THRESHOLD",
            "threshold values must be strictly increasing",
        )
        return False
    return True


def _band_for_temperature(temperature_c: float, thresholds: Mapping[str, object]) -> str:
    if temperature_c < float(thresholds["elevated"]):
        return HeatBand.NORMAL.value
    selected = HeatBand.NORMAL.value
    for band_name in _THRESHOLD_NAMES:
        if temperature_c >= float(thresholds[band_name]):
            selected = band_name
    return selected


def _check_policy_rules(
    scenario: Scenario,
    policy: Policy,
    add: Callable[[str, str, str], None],
) -> None:
    used_bands = {
        _enum_value(slot.band)
        for slot in scenario.heat_series
        if _enum_value(slot.band) in _HEAT_BANDS
    }
    used_exertions = {
        _enum_value(job.exertion)
        for job in scenario.jobs
        if _enum_value(job.exertion) in _EXERTIONS
    }
    pair_counts: dict[tuple[str, str], int] = {}
    for rule in policy.rules:
        pair = (_enum_value(rule.band), _enum_value(rule.exertion))
        pair_counts[pair] = pair_counts.get(pair, 0) + 1

    for band in _HEAT_BANDS:
        for exertion in _EXERTIONS:
            if band not in used_bands or exertion not in used_exertions:
                continue
            count = pair_counts.get((band, exertion), 0)
            if count == 0:
                add(
                    "rules",
                    "MISSING_POLICY_RULE",
                    f"missing policy rule for heat band {band!r} and exertion {exertion!r}",
                )
            elif count > 1:
                add(
                    "rules",
                    "DUPLICATE_POLICY_RULE",
                    f"expected exactly one policy rule for heat band {band!r} and exertion {exertion!r}",
                )


def _check_rule_values(policy: Policy, add: Callable[[str, str, str], None]) -> None:
    rolling_window = policy.rolling_window_slots
    if not _is_positive_int(rolling_window):
        add(
            "rolling_window_slots",
            "INVALID_POLICY_RULE",
            "rolling_window_slots must be a positive integer",
        )
        return

    for index, rule in enumerate(policy.rules):
        max_path = f"rules[{index}].max_active_slots"
        min_path = f"rules[{index}].min_recovery_slots"
        maximum = getattr(rule, "max_active_slots", None)
        minimum = getattr(rule, "min_recovery_slots", None)
        if not _is_non_negative_int(maximum) or maximum > rolling_window:
            add(
                max_path,
                "INVALID_POLICY_RULE",
                "max_active_slots must be between 0 and rolling_window_slots",
            )
        if not _is_non_negative_int(minimum) or minimum > rolling_window:
            add(
                min_path,
                "INVALID_POLICY_RULE",
                "min_recovery_slots must be between 0 and rolling_window_slots",
            )
        if _enum_value(getattr(rule, "stop_work", None)) is True and maximum != 0:
            add(
                max_path,
                "INVALID_POLICY_RULE",
                "stop_work rules must set max_active_slots to zero",
            )


def _is_non_negative_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _check_matrix(
    scenario: Scenario,
    location_ids: Sequence[object],
    add: Callable[[str, str, str], None],
) -> None:
    matrix_ids = list(scenario.travel_matrix_location_ids)
    seen: dict[object, int] = {}
    duplicate_matrix_ids = False
    for index, location_id in enumerate(matrix_ids):
        if location_id in seen:
            duplicate_matrix_ids = True
            add(
                f"travel_matrix_location_ids[{index}]",
                "DUPLICATE_ID",
                f"duplicate matrix location ID {location_id!r}; first seen at travel_matrix_location_ids[{seen[location_id]}]",
            )
        else:
            seen[location_id] = index

    if not duplicate_matrix_ids and set(matrix_ids) != set(location_ids):
        add(
            "travel_matrix_location_ids",
            "INVALID_MATRIX",
            "matrix location IDs must equal the scenario location ID set exactly",
        )

    matrix = scenario.travel_matrix_minutes
    expected_size = len(matrix_ids)
    if len(matrix) != expected_size or any(len(row) != expected_size for row in matrix):
        add(
            "travel_matrix_minutes",
            "INVALID_MATRIX",
            "travel matrix must be square with one row and column per matrix location ID",
        )

    for row_index, row in enumerate(matrix):
        for column_index, value in enumerate(row):
            path = f"travel_matrix_minutes[{row_index}][{column_index}]"
            if row_index == column_index:
                if value != 0:
                    add(path, "INVALID_MATRIX", "travel matrix diagonal values must be zero")
            elif not _is_positive_int(value):
                add(path, "INVALID_MATRIX", "off-diagonal travel values must be positive integers")


def _enum_value(value: object) -> object:
    return getattr(value, "value", value)
