"""
Structural validation for EV charger telemetry CSV files.

All public functions return a list of error strings (empty == valid).
"""

from __future__ import annotations

import pandas as pd
from typing import List, Set


EXPECTED_COLUMNS = [
    "tick", "state",
    "plug_inserted", "ev_ready", "user_start_request", "user_stop_request",
    "voltage", "current", "temperature", "ground_fault", "relay_feedback_closed",
    "close_contactor", "enable_charging", "current_limit",
    "env_current", "env_temperature", "env_relay_feedback_closed",
]

BOOL_COLUMNS = [
    "plug_inserted", "ev_ready", "user_start_request", "user_stop_request",
    "ground_fault", "relay_feedback_closed",
    "close_contactor", "enable_charging",
    "env_relay_feedback_closed",
]


def validate_schema(df: pd.DataFrame) -> List[str]:
    """Verify all 17 expected columns are present."""
    errors = []
    missing = [col for col in EXPECTED_COLUMNS if col not in df.columns]
    if missing:
        errors.append(f"Missing columns: {missing}")
    extra = [col for col in df.columns if col not in EXPECTED_COLUMNS]
    if extra:
        errors.append(f"Unexpected extra columns: {extra}")
    return errors


def validate_tick_sequence(df: pd.DataFrame) -> List[str]:
    """Ticks must start at 0 and increment by 1 with no gaps."""
    errors = []
    if df.empty:
        errors.append("DataFrame is empty")
        return errors
    if df["tick"].iloc[0] != 0:
        errors.append(f"Tick does not start at 0 (starts at {df['tick'].iloc[0]})")
    expected = list(range(len(df)))
    actual = list(df["tick"])
    if actual != expected:
        errors.append(
            f"Tick sequence has gaps or duplicates. Expected {expected[:5]}…, got {actual[:5]}…"
        )
    return errors


def validate_bool_columns(df: pd.DataFrame) -> List[str]:
    """Boolean signal columns must only contain 0 or 1."""
    errors = []
    for col in BOOL_COLUMNS:
        if col not in df.columns:
            continue
        invalid_mask = ~df[col].isin([0, 1])
        if invalid_mask.any():
            bad_ticks = list(df.loc[invalid_mask, "tick"])
            bad_vals = list(df.loc[invalid_mask, col])
            errors.append(
                f"Column '{col}' has non-boolean values at ticks {bad_ticks}: {bad_vals}"
            )
    return errors


def validate_state_values(df: pd.DataFrame, valid_states: Set[str]) -> List[str]:
    """State column must only contain recognised state names."""
    errors = []
    invalid_mask = ~df["state"].isin(valid_states)
    if invalid_mask.any():
        bad = df.loc[invalid_mask, ["tick", "state"]].to_dict("records")
        errors.append(f"Unrecognised state values: {bad}")
    return errors


def validate_numeric_ranges(df: pd.DataFrame) -> List[str]:
    """Coarse sanity-check on continuous signal ranges."""
    errors = []
    checks = {
        "voltage":         (0.0,   300.0),
        "current":         (0.0,   100.0),
        "temperature":     (-40.0, 150.0),
        "current_limit":   (0.0,   32.0),
        "env_current":     (0.0,   100.0),
        "env_temperature": (-40.0, 150.0),
    }
    for col, (lo, hi) in checks.items():
        if col not in df.columns:
            continue
        out_of_range = df[(df[col] < lo) | (df[col] > hi)]
        if not out_of_range.empty:
            errors.append(
                f"Column '{col}' out of range [{lo}, {hi}] at ticks: "
                f"{list(out_of_range['tick'])}"
            )
    return errors


def full_schema_report(df: pd.DataFrame, valid_states: Set[str]) -> List[str]:
    """Run all structural checks and return combined error list."""
    return (
        validate_schema(df)
        + validate_tick_sequence(df)
        + validate_bool_columns(df)
        + validate_state_values(df, valid_states)
        + validate_numeric_ranges(df)
    )
