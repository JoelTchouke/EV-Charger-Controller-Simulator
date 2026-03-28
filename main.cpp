#include <iostream>
#include "state_machine.h"

FaultStatus evaluateFaults(const SensorData& input, const ActuatorCommands& previous_commands) {
    FaultStatus faults;
    faults.overtemperature = input.temperature > 80.0;
    faults.overcurrent = input.current > 40.0;
    faults.ground_fault = input.ground_fault;
    faults.relay_mismatch =
        previous_commands.close_contactor && !input.relay_feedback_closed;
    return faults;
}

const char* toString(ChargerState state) {
    switch (state) {
        case ChargerState::Idle: return "Idle";
        case ChargerState::VehicleDetected: return "VehicleDetected";
        case ChargerState::PreChargeChecks: return "PreChargeChecks";
        case ChargerState::Charging: return "Charging";
        case ChargerState::Stopping: return "Stopping";
        case ChargerState::Fault: return "Fault";
        default: return "Unknown";
    }
}

int main() {
    StateMachine sm;
    SensorData input;
    ActuatorCommands previous_commands{};

    for (int tick = 0; tick < 8; ++tick) {
        if (tick == 1) {
            input.plug_inserted = true;
        }
        if (tick == 2) {
            input.ev_ready = true;
            input.user_start_request = true;
        }
        if (tick == 3) {
            input.relay_feedback_closed = true;
            input.user_start_request = false;
        }
        if (tick == 6) {
            input.user_stop_request = true;
        }
        if (tick == 7) {
            input.relay_feedback_closed = false;
            input.user_stop_request = false;
        }

        FaultStatus faults = evaluateFaults(input, previous_commands);
        StateResult result = sm.update(input, faults);

        std::cout << "Tick: " << tick
                  << " | State: " << toString(sm.getCurrentState())
                  << " | close_contactor=" << result.commands.close_contactor
                  << " | enable_charging=" << result.commands.enable_charging
                  << " | current_limit=" << result.commands.current_limit
                  << "\n";

        previous_commands = result.commands;
    }

    return 0;
}