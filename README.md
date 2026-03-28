# EV Charger Controller Simulator

A C++ state machine simulator for an electric vehicle (EV) charging controller. Models real-world charging behavior and safety-critical fault conditions using a tick-based simulation with CSV logging.

---

## Overview

This simulator replicates the operational logic of an EV charger controller as it transitions through discrete states in response to sensor inputs and fault conditions. Three predefined scenarios exercise the normal charge cycle and two safety fault paths (overtemperature and ground fault).

---

## Project Structure

```
EV-Charger-Controller-Simulator/
├── main.cpp                        # Entry point — runs all three scenarios
├── include/
│   ├── types.h                     # Core data structures (states, sensors, commands, faults)
│   ├── StateMachine.h              # State machine controller
│   ├── Environment.h               # Physical environment model
│   ├── Logger.h                    # CSV logging utility
│   ├── Scenarios.h                 # Scenario definitions
│   ├── IdleState.h
│   ├── VehiculeConnected.h
│   ├── PreSafeChecksState.h
│   ├── ChargingState.h
│   ├── StopState.h
│   └── Fault.h
└── src/
    ├── StateMachine.cpp
    ├── Environment.cpp
    ├── Logger.cpp
    ├── Scenarios.cpp
    └── states/
        ├── IdleState.cpp
        ├── VehiculeConnected.cpp
        ├── PreSafeChecksState.cpp
        ├── ChargingState.cpp
        ├── StopState.cpp
        └── Fault.cpp
```

---

## State Machine

The controller operates as a finite state machine with six states:

```
                      ┌─────────┐
              ┌──────►│  Idle   │◄──────────────────┐
              │        └────┬────┘                   │
              │             │ plug inserted           │
              │        ┌────▼──────────────┐         │
              │        │ VehicleConnected  │         │
              │        └────┬──────────────┘         │
              │             │ EV ready                │
              │        ┌────▼──────────────┐         │
              │        │  PreSafeChecks    │         │
              │        └────┬──────────────┘         │
              │             │ relay closed            │
              │        ┌────▼──────────────┐         │
              │        │    Charging       │         │
              │        └────┬──────────────┘         │
              │             │ user stop / unplug     │
              │        ┌────▼──────────────┐         │
              │        │    Stopping       ├─────────┘
              │        └───────────────────┘
              │
    any fault │        ┌───────────────────┐
              └────────┤      Fault        │
                       └───────────────────┘
```

| State | Description | Actuator Commands |
|---|---|---|
| **Idle** | Waiting for vehicle | All off |
| **VehicleConnected** | Plug detected, waiting for EV ready | All off |
| **PreSafeChecks** | Validates relay feedback before charging | Contactor closed, charging disabled |
| **Charging** | Active power delivery | Contactor closed, charging enabled, 32 A limit |
| **Stopping** | Graceful shutdown, waits for relay to open | All off |
| **Fault** | Terminal safety state | All off |

---

## Key Components

### `types.h` — Core Data Structures

- **`SensorData`** — Inputs to the state machine: `plug_inserted`, `ev_ready`, `user_start_request`, `user_stop_request`, `voltage`, `current`, `temperature`, `ground_fault`, `relay_feedback_closed`
- **`ActuatorCommands`** — Controller outputs: `close_contactor`, `enable_charging`, `current_limit`
- **`FaultStatus`** — Fault flags: `overtemperature`, `overcurrent`, `ground_fault`, `relay_mismatch`
- **`ChargerState`** — Enum for all six states above

### `Environment` — Physical Model

Simulates the physical charging environment. Applies tick-based scenario events (plug insertion, temperature spikes, etc.), accepts controller commands, computes relay feedback, and returns sensor data back to the state machine.

Current flows only when: plug inserted AND EV ready AND relay closed AND charging enabled AND no ground fault.

### `Logger` — CSV Output

Logs 17 columns per tick to a CSV file:

| Column Group | Columns |
|---|---|
| Metadata | `tick`, `state` |
| Sensor inputs | `plug_inserted`, `ev_ready`, `user_start_request`, `user_stop_request`, `voltage`, `current`, `temperature`, `ground_fault`, `relay_feedback_closed` |
| Controller commands | `close_contactor`, `enable_charging`, `current_limit` |
| Environment state | `env_current`, `env_temperature`, `env_relay_feedback_closed` |

### `Scenarios` — Test Cases

Three predefined 15-tick scenarios:

#### Normal Scenario
| Tick | Event |
|---|---|
| 2 | Plug inserted |
| 3 | EV ready |
| 4 | User start request |
| 10 | User stop request |

Expected flow: `Idle → VehicleConnected → PreSafeChecks → Charging → Stopping → Idle`

#### Overtemperature Scenario
Same as normal through tick 4, then at tick 7 temperature rises to 95°C during charging.

Expected flow: `Idle → ... → Charging → Fault`

#### Ground Fault Scenario
Same as normal through tick 4, then at tick 6 a ground fault is detected during pre-charge.

Expected flow: `Idle → ... → Charging → Fault`

---

## Data Flow

```
Scenario Events
       │
       ▼
Environment.applyEventsForCurrentTick()   ← updates plug, temperature, fault flags
       │
       ▼
Environment.getSensorData()               ← packages sensor readings
       │
       ▼
StateMachine.update(SensorData, Faults)   ← dispatches to current state handler
       │
       ▼
StateHandler.handle()                     ← returns next state + actuator commands
       │
       ▼
Environment.applyControllerCommands()     ← updates relay and current
       │
       ▼
Logger.logTick()                          ← writes row to CSV
       │
       ▼
Console output (printTick)
```

---

## Build & Run

Compile with any C++17-compatible compiler:

```bash
# Example with g++
g++ -std=c++17 main.cpp src/*.cpp src/states/*.cpp -Iinclude -o sim

# Run
./sim
```

On Windows, the project was compiled with MSVC to `sim.exe`.

Running the simulator produces three CSV output files in the working directory:
- `normal_scenario.csv`
- `overtemperature_scenario.csv`
- `ground_fault_scenario.csv`

---

## Design Notes

- **State machine pattern** — Each state is its own class with a `handle()` method, keeping transition logic isolated and testable.
- **Tick-based simulation** — Discrete time steps allow precise, reproducible event sequencing.
- **Contactor feedback loop** — The controller validates relay feedback before enabling power, mirroring real hardware behavior.
- **Fault safety** — Any fault condition immediately transitions to the terminal `Fault` state with all outputs disabled.
