#include "StopState.h"

StateResult StoppingState::handle(const SensorData& input, const FaultStatus& faults) {
    StateResult result;
    result.nextState = ChargerState::Stopping;
    result.commands.close_contactor = false;
    result.commands.enable_charging = false;
    result.commands.current_limit = 0.0;

    if (faults.any()) {
        result.nextState = ChargerState::Fault;
    } else if (!input.relay_feedback_closed) {
        result.nextState = ChargerState::Idle;
    }

    return result;
}
