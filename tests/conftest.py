"""
Shared pytest fixtures and constants for EV Charger Controller Simulator validation.

Run the simulator first to generate CSV telemetry files:
    ./sim.exe          (from project root)

Then run tests:
    cd tests && pytest -v
"""

import subprocess
import pandas as pd
import pytest
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent

SCENARIO_FILES = {
    "normal": PROJECT_ROOT / "normal_scenario.csv",
    "overtemperature": PROJECT_ROOT / "overtemperature_scenario.csv",
    "ground_fault": PROJECT_ROOT / "ground_fault_scenario.csv",
}

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

VALID_STATES = {"Idle", "VehicleConnected", "PreSafeChecks", "Charging", "Stopping", "Fault"}

NOMINAL_VOLTAGE = 240.0
MAX_CURRENT_LIMIT = 32.0
OVERTEMPERATURE_THRESHOLD = 80.0


def _load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        pytest.fail(
            f"Telemetry file not found: {path}\n"
            "Run the simulator first: ./sim.exe (from project root)"
        )
    df = pd.read_csv(path)
    # Strip any whitespace from column names and state values
    df.columns = df.columns.str.strip()
    if "state" in df.columns:
        df["state"] = df["state"].str.strip()
    return df


@pytest.fixture(scope="session")
def normal_df() -> pd.DataFrame:
    return _load_csv(SCENARIO_FILES["normal"])


@pytest.fixture(scope="session")
def overtemperature_df() -> pd.DataFrame:
    return _load_csv(SCENARIO_FILES["overtemperature"])


@pytest.fixture(scope="session")
def ground_fault_df() -> pd.DataFrame:
    return _load_csv(SCENARIO_FILES["ground_fault"])


def pytest_addoption(parser):
    parser.addoption(
        "--rebuild",
        action="store_true",
        default=False,
        help="Re-run sim.exe before executing tests to regenerate telemetry CSV files.",
    )


@pytest.fixture(scope="session", autouse=True)
def maybe_rebuild(request):
    """If --rebuild flag is passed, re-run the simulator before tests."""
    if request.config.getoption("--rebuild"):
        sim_exe = PROJECT_ROOT / "sim.exe"
        if not sim_exe.exists():
            pytest.fail(f"sim.exe not found at {sim_exe}")
        result = subprocess.run(
            [str(sim_exe)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        if result.returncode != 0:
            pytest.fail(
                f"sim.exe exited with code {result.returncode}\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )
