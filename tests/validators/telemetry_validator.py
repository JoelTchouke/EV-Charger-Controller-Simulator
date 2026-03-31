"""
Physics and control-logic invariant checks for EV charger telemetry.

All public check_* functions return a list of error strings (empty == valid).
The summarize() function returns a human-readable dict for quick inspection.
"""

from __future__ import annotations

import pandas as pd
from typing import Dict, List


# ---------------------------------------------------------------------------
# Current-flow invariant
# ---------------------------------------------------------------------------

def check_current_flow_invariant(df: pd.DataFrame) -> List[str]:
    """
    env_current > 0 if and only if ALL five conditions are true:
        enable_charging == 1
        relay_feedback_closed == 1
        plug_inserted == 1
        ev_ready == 1
        ground_fault == 0

    This mirrors the Environment::applyControllerCommands logic in C++.
    """
    conditions_met = (
        (df["enable_charging"] == 1)
        & (df["relay_feedback_closed"] == 1)
        & (df["plug_inserted"] == 1)
        & (df["ev_ready"] == 1)
        & (df["ground_fault"] == 0)
    )
    errors = []

    flowing_when_should_not = df[~conditions_met & (df["env_current"] > 0)]
    if not flowing_when_should_not.empty:
        errors.append(
            f"env_current > 0 despite conditions not met at ticks: "
            f"{list(flowing_when_should_not['tick'])}"
        )

    not_flowing_when_should = df[conditions_met & (df["env_current"] == 0)]
    if not not_flowing_when_should.empty:
        errors.append(
            f"env_current == 0 despite all conditions met at ticks: "
            f"{list(not_flowing_when_should['tick'])}"
        )

    return errors


# ---------------------------------------------------------------------------
# Voltage
# ---------------------------------------------------------------------------

def check_voltage_constant(df: pd.DataFrame, expected: float = 240.0) -> List[str]:
    """Voltage must remain at the nominal supply level throughout the simulation."""
    wrong = df[df["voltage"] != expected]
    if wrong.empty:
        return []
    return [
        f"Voltage != {expected}V at ticks {list(wrong['tick'])}: "
        f"{list(wrong['voltage'])}"
    ]


# ---------------------------------------------------------------------------
# Current limit
# ---------------------------------------------------------------------------

def check_current_limit_in_charging(df: pd.DataFrame, expected_limit: float = 32.0) -> List[str]:
    """Whenever enable_charging is asserted, current_limit must equal 32 A."""
    charging_rows = df[df["enable_charging"] == 1]
    wrong = charging_rows[charging_rows["current_limit"] != expected_limit]
    if wrong.empty:
        return []
    return [
        f"current_limit != {expected_limit} A while enable_charging=1 at ticks: "
        f"{list(wrong['tick'])}"
    ]


def check_current_limit_zero_when_not_charging(df: pd.DataFrame) -> List[str]:
    """When enable_charging is de-asserted, current_limit must be 0."""
    not_charging = df[df["enable_charging"] == 0]
    wrong = not_charging[not_charging["current_limit"] != 0]
    if wrong.empty:
        return []
    return [
        f"current_limit != 0 while enable_charging=0 at ticks: {list(wrong['tick'])}"
    ]


# ---------------------------------------------------------------------------
# Actuator safety invariants
# ---------------------------------------------------------------------------

def check_actuators_off_in_idle(df: pd.DataFrame) -> List[str]:
    """In Idle state all actuator outputs must be de-asserted."""
    idle = df[df["state"] == "Idle"]
    errors = []
    for col in ("close_contactor", "enable_charging"):
        wrong = idle[idle[col] != 0]
        if not wrong.empty:
            errors.append(f"'{col}' asserted during Idle at ticks: {list(wrong['tick'])}")
    wrong_limit = idle[idle["current_limit"] != 0]
    if not wrong_limit.empty:
        errors.append(f"'current_limit' != 0 during Idle at ticks: {list(wrong_limit['tick'])}")
    return errors


def check_actuators_off_in_fault(df: pd.DataFrame) -> List[str]:
    """In Fault state all actuator outputs must be de-asserted (safety shut-off)."""
    fault = df[df["state"] == "Fault"]
    if fault.empty:
        return []
    errors = []
    for col in ("close_contactor", "enable_charging"):
        wrong = fault[fault[col] != 0]
        if not wrong.empty:
            errors.append(f"'{col}' asserted during Fault at ticks: {list(wrong['tick'])}")
    wrong_limit = fault[fault["current_limit"] != 0]
    if not wrong_limit.empty:
        errors.append(
            f"'current_limit' != 0 during Fault at ticks: {list(wrong_limit['tick'])}"
        )
    return errors


# ---------------------------------------------------------------------------
# Relay feedback timing
# ---------------------------------------------------------------------------

def check_relay_feedback_equals_command(df: pd.DataFrame) -> List[str]:
    """
    env_relay_feedback_closed is logged AFTER commands are applied in the same tick,
    so it must equal close_contactor on the same tick.
    """
    wrong = df[df["env_relay_feedback_closed"] != df["close_contactor"]]
    if wrong.empty:
        return []
    return [
        f"env_relay_feedback_closed != close_contactor at ticks: {list(wrong['tick'])}"
    ]


def check_sensor_relay_lags_command(df: pd.DataFrame) -> List[str]:
    """
    relay_feedback_closed (sensor read at the START of a tick) must equal
    close_contactor from the PREVIOUS tick — a one-tick propagation delay.
    """
    errors = []
    for i in range(1, len(df)):
        prev = df.iloc[i - 1]
        curr = df.iloc[i]
        if curr["relay_feedback_closed"] != prev["close_contactor"]:
            errors.append(
                f"relay_feedback_closed mismatch at tick {curr['tick']}: "
                f"expected {int(prev['close_contactor'])} "
                f"(prev close_contactor), got {int(curr['relay_feedback_closed'])}"
            )
    return errors


# ---------------------------------------------------------------------------
# Fault-transition invariants
# ---------------------------------------------------------------------------

def check_overtemperature_triggers_fault(
    df: pd.DataFrame, threshold: float = 80.0
) -> List[str]:
    """
    Any tick where temperature > threshold should be followed by a transition
    to Fault state on the next tick.

    NOTE: The current implementation does NOT populate FaultStatus from sensor
    readings, so this check is expected to fail. It is used as an xfail marker
    to document the design gap.
    """
    errors = []
    for i in range(len(df) - 1):
        row = df.iloc[i]
        next_row = df.iloc[i + 1]
        if row["temperature"] > threshold and next_row["state"] != "Fault":
            errors.append(
                f"Overtemperature at tick {row['tick']} (temp={row['temperature']}°C) "
                f"did not transition to Fault — state at tick {next_row['tick']} "
                f"is '{next_row['state']}'"
            )
    return errors


def check_ground_fault_triggers_fault(df: pd.DataFrame) -> List[str]:
    """
    Any tick where ground_fault == 1 should be followed by a transition to
    Fault state on the next tick.

    NOTE: The current implementation does NOT detect ground_fault in the state
    machine logic, so this check is expected to fail. Used as an xfail marker.
    """
    errors = []
    for i in range(len(df) - 1):
        row = df.iloc[i]
        next_row = df.iloc[i + 1]
        if row["ground_fault"] == 1 and next_row["state"] != "Fault":
            errors.append(
                f"Ground fault at tick {row['tick']} did not trigger Fault — "
                f"state at tick {next_row['tick']} is '{next_row['state']}'"
            )
    return errors


# ---------------------------------------------------------------------------
# Summary helper
# ---------------------------------------------------------------------------

def summarize(df: pd.DataFrame) -> Dict:
    """Return a compact summary dict useful for debugging and reports."""
    state_counts = df["state"].value_counts().to_dict()
    return {
        "total_ticks": len(df),
        "states_visited": state_counts,
        "max_env_current_A": float(df["env_current"].max()),
        "max_temperature_C": float(df["env_temperature"].max()),
        "ticks_charging": int((df["state"] == "Charging").sum()),
        "ticks_in_fault": int((df["state"] == "Fault").sum()),
        "ground_fault_ticks": int((df["ground_fault"] == 1).sum()),
        "overtemp_ticks": int((df["temperature"] > 80.0).sum()),
    }
