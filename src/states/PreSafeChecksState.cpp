#include "PreSafeChecksState.h"

StateResult PreSafeChecksState::handle(const SensorData& input, const FaultStatus& faults) {
    StateResult result;
    result.nextState = ChargerState::PreSafeChecks;
    result.commands.close_contactor = true;
    result.commands.enable_charging = false;
    result.commands.current_limit = 0.0;

    if (faults.any()) {
        result.nextState = ChargerState::Fault;
    } else if (!input.plug_inserted) {
        result.nextState = ChargerState::Stopping;
    } else if (input.relay_feedback_closed) {
        result.nextState = ChargerState::Charging;
    }

    return result;
}
