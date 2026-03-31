"""
Tests for the overtemperature fault scenario (overtemperature_scenario.csv).

Scenario profile:
  Ticks 0-6 : Same as normal scenario (Idle → VehicleConnected → PreSafeChecks → Charging)
  Tick 7+   : Temperature spikes to 95°C — should trigger Fault state

KNOWN DESIGN GAP
----------------
FaultStatus is constructed but never populated from sensor readings in main.cpp.
The state machine therefore never detects overtemperature and stays in Charging.

Tests that verify the EXPECTED (safe) behaviour are marked @pytest.mark.xfail.
When the design gap is fixed those tests will become xpass and the team will
be alerted to remove the xfail markers.
"""

import pytest
from conftest import VALID_STATES, OVERTEMPERATURE_THRESHOLD
from validators.csv_validator import full_schema_report
from validators.telemetry_validator import (
    check_current_flow_invariant,
    check_voltage_constant,
    check_actuators_off_in_fault,
    check_overtemperature_triggers_fault,
    summarize,
)


# ---------------------------------------------------------------------------
# Schema / structural integrity
# ---------------------------------------------------------------------------

class TestSchema:
    def test_full_schema_valid(self, overtemperature_df):
        errors = full_schema_report(overtemperature_df, VALID_STATES)
        assert errors == [], "\n".join(errors)


# ---------------------------------------------------------------------------
# Telemetry recording  (these should always pass — the logger is correct)
# ---------------------------------------------------------------------------

class TestTelemetryRecording:
    def test_temperature_spike_is_logged(self, overtemperature_df):
        """The logger must faithfully record the 95°C spike from tick 7 onwards."""
        high_temp = overtemperature_df[overtemperature_df["env_temperature"] >= 95.0]
        assert not high_temp.empty, (
            "Temperature spike to 95°C was never recorded in telemetry"
        )

    def test_temperature_spike_starts_at_tick_7(self, overtemperature_df):
        spike_ticks = overtemperature_df[
            overtemperature_df["env_temperature"] >= 95.0
        ]["tick"]
        assert spike_ticks.min() == 7, (
            f"Temperature spike expected to start at tick 7, started at {spike_ticks.min()}"
        )

    def test_temperature_normal_before_spike(self, overtemperature_df):
        pre_spike = overtemperature_df[overtemperature_df["tick"] < 7]
        assert all(pre_spike["env_temperature"] == 25.0), (
            "Temperature should be 25°C before tick 7"
        )

    def test_voltage_constant(self, overtemperature_df):
        errors = check_voltage_constant(overtemperature_df)
        assert errors == [], "\n".join(errors)

    def test_current_flow_invariant(self, overtemperature_df):
        """The Environment model's physics are correct regardless of SM fault detection."""
        errors = check_current_flow_invariant(overtemperature_df)
        assert errors == [], "\n".join(errors)


# ---------------------------------------------------------------------------
# Observed (current broken) behaviour — documents the design gap
# ---------------------------------------------------------------------------

class TestObservedBehaviour:
    def test_state_machine_does_not_detect_overtemperature(self, overtemperature_df):
        """
        DOCUMENTS KNOWN ISSUE: The state machine stays in Charging despite 95°C.
        This test asserts the CURRENT (broken) behaviour so CI does not regress it.
        """
        post_spike = overtemperature_df[overtemperature_df["tick"] >= 7]
        assert all(post_spike["state"] == "Charging"), (
            "Unexpected: state machine reacted to overtemperature. "
            "Update this test and remove xfail from the safety test below."
        )

    def test_charging_continues_at_high_temp(self, overtemperature_df):
        """
        DOCUMENTS KNOWN ISSUE: enable_charging stays asserted at 95°C.
        The controller keeps commanding 32 A even while overtemperature.
        """
        post_spike = overtemperature_df[overtemperature_df["tick"] >= 7]
        assert all(post_spike["enable_charging"] == 1), (
            "Unexpected: enable_charging was de-asserted after temperature spike. "
            "Update this test and remove xfail from the safety test below."
        )

    def test_current_flows_at_high_temp(self, overtemperature_df):
        """
        DOCUMENTS KNOWN ISSUE: The environment model does NOT block current for
        overtemperature (only ground_fault blocks it). Current keeps flowing at 32 A.
        """
        post_spike = overtemperature_df[overtemperature_df["tick"] >= 8]
        assert all(post_spike["env_current"] == 32.0), (
            "env_current stopped flowing after temperature spike — unexpected given "
            "that the environment model has no overtemperature current-cutoff."
        )


# ---------------------------------------------------------------------------
# Expected (safe) behaviour — xfail until design gap is fixed
# ---------------------------------------------------------------------------

class TestExpectedSafetyBehaviour:
    @pytest.mark.xfail(
        strict=True,
        reason=(
            "DESIGN GAP: FaultStatus is never populated from sensor readings. "
            "State machine does not react to overtemperature. "
            "Fix: compute FaultStatus.overtemperature from temperature > threshold "
            "and pass it to state handlers."
        ),
    )
    def test_overtemperature_triggers_fault_state(self, overtemperature_df):
        """Overtemperature should transition the SM to Fault within one tick."""
        errors = check_overtemperature_triggers_fault(
            overtemperature_df, threshold=OVERTEMPERATURE_THRESHOLD
        )
        assert errors == [], "\n".join(errors)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "DESIGN GAP: Fault state is never entered so actuator-off check "
            "has nothing to validate. Depends on test_overtemperature_triggers_fault_state fix."
        ),
    )
    def test_actuators_off_in_fault(self, overtemperature_df):
        """In Fault state, all actuator outputs must be de-asserted (safety shut-off)."""
        assert "Fault" in overtemperature_df["state"].values, (
            "Fault state was never entered — cannot verify actuator-off invariant"
        )
        errors = check_actuators_off_in_fault(overtemperature_df)
        assert errors == [], "\n".join(errors)


# ---------------------------------------------------------------------------
# Diagnostic summary
# ---------------------------------------------------------------------------

def test_print_telemetry_summary(overtemperature_df, capsys):
    summary = summarize(overtemperature_df)
    print("\n--- Overtemperature Scenario Telemetry Summary ---")
    for key, val in summary.items():
        print(f"  {key}: {val}")
    assert summary["overtemp_ticks"] > 0, "Expected overtemperature ticks to be recorded"
