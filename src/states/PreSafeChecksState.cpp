#include "PreSafeChecksState.h"

StateResult PreSafeChecksState::handle(const SensorData& input, const FaultStatus& faults) {
    StateResult result;
    result.next_state = ChargerState::PreChargeChecks;
    result.commands.close_contactor = true;
    result.commands.enable_charging = false;
    result.commands.current_limit = 0.0;

    if (faults.any()) {
        result.next_state = ChargerState::Fault;
    } else if (!input.plug_inserted) {
        result.next_state = ChargerState::Stopping;
    } else if (input.relay_feedback_closed) {
        result.next_state = ChargerState::Charging;
    }

    return result;
}