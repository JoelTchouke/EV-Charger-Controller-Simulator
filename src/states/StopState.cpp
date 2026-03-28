#include "stopping_state.h"

StateResult StoppingState::handle(const SensorData& input, const FaultStatus& faults) {
    StateResult result;
    result.next_state = ChargerState::Stopping;
    result.commands.close_contactor = false;
    result.commands.enable_charging = false;
    result.commands.current_limit = 0.0;

    if (faults.any()) {
        result.next_state = ChargerState::Fault;
    } else if (!input.relay_feedback_closed) {
        result.next_state = ChargerState::Idle;
    }

    return result;
}