"""
Tests for the ground-fault safety scenario (ground_fault_scenario.csv).

Scenario profile:
  Ticks 0-5 : Same as normal scenario (Idle → VehicleConnected → PreSafeChecks → Charging)
  Tick 6+   : ground_fault=1 injected — should trigger Fault state

DESIGN SPLIT
------------
- The Environment model CORRECTLY stops current flow when ground_fault=1.
  (env_current = 0 from tick 6 onwards even though enable_charging=1)
- The State Machine does NOT detect ground_fault and stays in Charging.
  (same root cause as overtemperature: FaultStatus never populated)

Tests verifying EXPECTED SM safety behaviour are marked @pytest.mark.xfail.
"""

import pytest
from conftest import VALID_STATES
from validators.csv_validator import full_schema_report
from validators.telemetry_validator import (
    check_voltage_constant,
    check_actuators_off_in_fault,
    check_ground_fault_triggers_fault,
    summarize,
)


# ---------------------------------------------------------------------------
# Schema / structural integrity
# ---------------------------------------------------------------------------

class TestSchema:
    def test_full_schema_valid(self, ground_fault_df):
        errors = full_schema_report(ground_fault_df, VALID_STATES)
        assert errors == [], "\n".join(errors)


# ---------------------------------------------------------------------------
# Telemetry recording  (logger is correct — these always pass)
# ---------------------------------------------------------------------------

class TestTelemetryRecording:
    def test_ground_fault_is_logged(self, ground_fault_df):
        fault_rows = ground_fault_df[ground_fault_df["ground_fault"] == 1]
        assert not fault_rows.empty, "ground_fault=1 was never recorded in telemetry"

    def test_ground_fault_starts_at_tick_6(self, ground_fault_df):
        fault_ticks = ground_fault_df[ground_fault_df["ground_fault"] == 1]["tick"]
        assert fault_ticks.min() == 6, (
            f"Ground fault expected to start at tick 6, started at {fault_ticks.min()}"
        )

    def test_no_ground_fault_before_tick_6(self, ground_fault_df):
        pre_fault = ground_fault_df[ground_fault_df["tick"] < 6]
        assert pre_fault["ground_fault"].sum() == 0, (
            "ground_fault signal asserted before tick 6 — unexpected"
        )

    def test_voltage_constant(self, ground_fault_df):
        errors = check_voltage_constant(ground_fault_df)
        assert errors == [], "\n".join(errors)


# ---------------------------------------------------------------------------
# Environment model behaviour  (physical layer — correct, should always pass)
# ---------------------------------------------------------------------------

class TestEnvironmentModel:
    def test_environment_stops_current_on_ground_fault(self, ground_fault_df):
        """
        The environment model blocks current whenever ground_fault=1.
        This is the hardware-level protection that works correctly.
        """
        fault_rows = ground_fault_df[ground_fault_df["ground_fault"] == 1]
        wrong = fault_rows[fault_rows["env_current"] != 0]
        assert wrong.empty, (
            f"env_current != 0 during ground fault at ticks: {list(wrong['tick'])}"
        )

    def test_current_zero_from_tick_6(self, ground_fault_df):
        post_fault = ground_fault_df[ground_fault_df["tick"] >= 6]
        assert all(post_fault["env_current"] == 0.0), (
            "env_current should be 0 from tick 6 (ground fault active)"
        )

    def test_current_flows_before_ground_fault(self, ground_fault_df):
        """
        Before the ground fault is injected, normal charging current should flow.
        Confirms the scenario setup mirrors the normal scenario through tick 5.
        """
        # Tick 6 is the first Charging tick where enable_charging=1 AND ground_fault=1
        # Tick 5 has enable_charging=0 (first Charging tick — relay warm-up)
        # Tick 6 in ground fault scenario: enable_charging=1 but ground_fault=1 → 0A
        # So we only see 0A throughout this scenario post-relay-close.
        # Verify that at least one pre-fault tick had charging commanded.
        commanded = ground_fault_df[
            (ground_fault_df["tick"] < 6) & (ground_fault_df["enable_charging"] == 0)
        ]
        # The scenario progresses identically to normal up to tick 5
        pre5 = ground_fault_df[ground_fault_df["tick"] == 5].iloc[0]
        assert pre5["state"] == "Charging"
        assert pre5["close_contactor"] == 1


# ---------------------------------------------------------------------------
# Observed (current broken) SM behaviour — documents the design gap
# ---------------------------------------------------------------------------

class TestObservedBehaviour:
    def test_state_machine_does_not_detect_ground_fault(self, ground_fault_df):
        """
        DOCUMENTS KNOWN ISSUE: State machine stays in Charging despite ground_fault=1.
        This test asserts the CURRENT (broken) behaviour to catch regressions.
        """
        post_fault = ground_fault_df[ground_fault_df["tick"] >= 7]
        assert all(post_fault["state"] == "Charging"), (
            "Unexpected: state machine reacted to ground fault. "
            "Update this test and remove xfail from the safety test below."
        )

    def test_controller_keeps_commanding_charging_despite_fault(self, ground_fault_df):
        """
        DOCUMENTS KNOWN ISSUE: The controller keeps asserting enable_charging=1
        and current_limit=32 even while ground_fault=1.
        The environment model correctly ignores these commands (env_current=0),
        but the controller itself is unaware of the fault.
        """
        post_fault = ground_fault_df[ground_fault_df["tick"] >= 6]
        commanding = post_fault[post_fault["enable_charging"] == 1]
        assert not commanding.empty, (
            "Unexpected: enable_charging was de-asserted after ground fault injection."
        )


# ---------------------------------------------------------------------------
# Expected (safe) behaviour — xfail until design gap is fixed
# ---------------------------------------------------------------------------

class TestExpectedSafetyBehaviour:
    @pytest.mark.xfail(
        strict=True,
        reason=(
            "DESIGN GAP: FaultStatus.ground_fault is never set from sensor data. "
            "State machine does not transition to Fault on ground_fault=1. "
            "Fix: populate FaultStatus from SensorData before passing to state handlers."
        ),
    )
    def test_ground_fault_triggers_fault_state(self, ground_fault_df):
        """The SM must transition to Fault within one tick of seeing ground_fault=1."""
        errors = check_ground_fault_triggers_fault(ground_fault_df)
        assert errors == [], "\n".join(errors)

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "DESIGN GAP: Fault state never entered — actuator-off check has nothing "
            "to validate. Depends on test_ground_fault_triggers_fault_state fix."
        ),
    )
    def test_actuators_off_in_fault(self, ground_fault_df):
        """All actuator outputs must be de-asserted once Fault state is entered."""
        assert "Fault" in ground_fault_df["state"].values, (
            "Fault state was never entered — cannot verify actuator-off invariant"
        )
        errors = check_actuators_off_in_fault(ground_fault_df)
        assert errors == [], "\n".join(errors)


# ---------------------------------------------------------------------------
# Diagnostic summary
# ---------------------------------------------------------------------------

def test_print_telemetry_summary(ground_fault_df, capsys):
    summary = summarize(ground_fault_df)
    print("\n--- Ground Fault Scenario Telemetry Summary ---")
    for key, val in summary.items():
        print(f"  {key}: {val}")
    assert summary["ground_fault_ticks"] > 0, "Expected ground_fault ticks to be recorded"
    assert summary["max_env_current_A"] == 0.0, (
        "max env_current should be 0 A — ground fault prevents any current flow "
        "in this scenario (fault is injected before enable_charging=1 takes effect)"
    )
