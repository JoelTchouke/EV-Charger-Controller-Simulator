"""
Tests for the normal EV charging cycle (normal_scenario.csv).

Expected flow:
  Tick 0-1  : Idle            (no vehicle)
  Tick 2    : VehicleConnected (plug inserted)
  Tick 3-4  : PreSafeChecks   (relay closing)
  Tick 5-9  : Charging        (user_stop at tick 10)
  Tick 10-11: Stopping        (relay opening)
  Tick 12   : Idle            (relay open, returns to idle)
  Tick 13   : VehicleConnected (plug still present)
  Tick 14   : PreSafeChecks   (simulation ends before completing cycle)
"""

import pytest
from conftest import VALID_STATES
from validators.csv_validator import full_schema_report
from validators.telemetry_validator import (
    check_current_flow_invariant,
    check_voltage_constant,
    check_current_limit_in_charging,
    check_current_limit_zero_when_not_charging,
    check_actuators_off_in_idle,
    check_relay_feedback_equals_command,
    check_sensor_relay_lags_command,
    summarize,
)

EXPECTED_STATE_SEQUENCE = [
    "Idle",             # tick 0
    "Idle",             # tick 1
    "VehicleConnected", # tick 2
    "PreSafeChecks",    # tick 3
    "PreSafeChecks",    # tick 4
    "Charging",         # tick 5
    "Charging",         # tick 6
    "Charging",         # tick 7
    "Charging",         # tick 8
    "Charging",         # tick 9
    "Stopping",         # tick 10
    "Stopping",         # tick 11
    "Idle",             # tick 12
    "VehicleConnected", # tick 13
    "PreSafeChecks",    # tick 14
]


# ---------------------------------------------------------------------------
# Schema / structural integrity
# ---------------------------------------------------------------------------

class TestSchema:
    def test_full_schema_valid(self, normal_df):
        errors = full_schema_report(normal_df, VALID_STATES)
        assert errors == [], "\n".join(errors)

    def test_row_count(self, normal_df):
        assert len(normal_df) == 15, (
            f"Expected 15 ticks, got {len(normal_df)}"
        )


# ---------------------------------------------------------------------------
# State-machine transitions
# ---------------------------------------------------------------------------

class TestStateTransitions:
    def test_exact_state_sequence(self, normal_df):
        actual = list(normal_df["state"])
        assert actual == EXPECTED_STATE_SEQUENCE, (
            f"State sequence mismatch.\n"
            f"Expected: {EXPECTED_STATE_SEQUENCE}\n"
            f"Actual  : {actual}"
        )

    def test_starts_in_idle(self, normal_df):
        assert normal_df["state"].iloc[0] == "Idle"

    def test_vehicle_connected_triggered_by_plug(self, normal_df):
        tick2 = normal_df[normal_df["tick"] == 2].iloc[0]
        assert tick2["state"] == "VehicleConnected"
        assert tick2["plug_inserted"] == 1

    def test_presafe_checks_entered(self, normal_df):
        assert "PreSafeChecks" in normal_df["state"].values

    def test_charging_state_reached(self, normal_df):
        assert "Charging" in normal_df["state"].values

    def test_stopping_triggered_by_stop_request(self, normal_df):
        tick10 = normal_df[normal_df["tick"] == 10].iloc[0]
        assert tick10["state"] == "Stopping"
        assert tick10["user_stop_request"] == 1

    def test_no_fault_state_in_normal_scenario(self, normal_df):
        assert "Fault" not in normal_df["state"].values, (
            "Fault state should not appear in a fault-free scenario"
        )

    def test_idle_before_plug_insert(self, normal_df):
        pre_plug = normal_df[normal_df["tick"] < 2]
        assert all(pre_plug["state"] == "Idle")


# ---------------------------------------------------------------------------
# Telemetry / physical invariants
# ---------------------------------------------------------------------------

class TestTelemetry:
    def test_voltage_constant_240v(self, normal_df):
        errors = check_voltage_constant(normal_df)
        assert errors == [], "\n".join(errors)

    def test_current_flow_invariant(self, normal_df):
        errors = check_current_flow_invariant(normal_df)
        assert errors == [], "\n".join(errors)

    def test_current_limit_32a_while_charging(self, normal_df):
        errors = check_current_limit_in_charging(normal_df)
        assert errors == [], "\n".join(errors)

    def test_current_limit_zero_when_not_charging(self, normal_df):
        errors = check_current_limit_zero_when_not_charging(normal_df)
        assert errors == [], "\n".join(errors)

    def test_actuators_off_in_idle(self, normal_df):
        errors = check_actuators_off_in_idle(normal_df)
        assert errors == [], "\n".join(errors)

    def test_enable_charging_only_in_charging_and_first_stopping_tick(self, normal_df):
        """
        enable_charging must be 0 in Idle, VehicleConnected, and PreSafeChecks.
        In Stopping it may be 1 on the first tick (carry-over before the SM
        de-asserts it once relay_feedback_closed goes low).
        """
        safe_off_states = {"Idle", "VehicleConnected", "PreSafeChecks"}
        bad = normal_df[
            normal_df["state"].isin(safe_off_states) & (normal_df["enable_charging"] == 1)
        ]
        assert bad.empty, (
            f"enable_charging=1 in a state where it must be 0: "
            f"{list(bad[['tick', 'state']].to_dict('records'))}"
        )

    def test_peak_current_reaches_32a(self, normal_df):
        assert normal_df["env_current"].max() == 32.0, (
            "Simulated current never reached 32 A in normal scenario"
        )

    def test_no_ground_fault_in_normal_scenario(self, normal_df):
        assert normal_df["ground_fault"].sum() == 0, (
            "Unexpected ground_fault signals in normal scenario"
        )

    def test_temperature_stable(self, normal_df):
        assert normal_df["env_temperature"].max() == 25.0, (
            "Temperature should stay at 25°C in normal scenario"
        )


# ---------------------------------------------------------------------------
# Relay timing
# ---------------------------------------------------------------------------

class TestRelayTiming:
    def test_relay_feedback_matches_command_same_tick(self, normal_df):
        errors = check_relay_feedback_equals_command(normal_df)
        assert errors == [], "\n".join(errors)

    def test_sensor_relay_lags_command_by_one_tick(self, normal_df):
        errors = check_sensor_relay_lags_command(normal_df)
        assert errors == [], "\n".join(errors)

    def test_contactor_closed_during_charging(self, normal_df):
        charging = normal_df[normal_df["state"] == "Charging"]
        assert all(charging["close_contactor"] == 1), (
            "close_contactor must be 1 throughout Charging state"
        )

    def test_contactor_opens_in_stopping(self, normal_df):
        stopping = normal_df[normal_df["state"] == "Stopping"]
        # By the second Stopping tick the contactor command should be 0
        last_stopping = stopping.iloc[-1]
        assert last_stopping["close_contactor"] == 0, (
            "close_contactor must eventually be de-asserted in Stopping state"
        )


# ---------------------------------------------------------------------------
# Diagnostic output (not an assertion — useful for manual review)
# ---------------------------------------------------------------------------

def test_print_telemetry_summary(normal_df, capsys):
    summary = summarize(normal_df)
    print("\n--- Normal Scenario Telemetry Summary ---")
    for key, val in summary.items():
        print(f"  {key}: {val}")
    assert summary["ticks_in_fault"] == 0
    assert summary["max_env_current_A"] == 32.0
