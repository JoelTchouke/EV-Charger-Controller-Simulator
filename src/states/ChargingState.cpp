#include "ChargingState.h"

StateResult ChargingState::handle(const SensorData& input, const FaultStatus& faults) {
    StateResult result;
    result.nextState = ChargerState::Charging;
    result.commands.close_contactor = true;
    result.commands.enable_charging = true;
    result.commands.current_limit = 32.0;

    if (faults.any()) {
        result.nextState = ChargerState::Fault;
    } else if (input.user_stop_request || !input.plug_inserted) {
        result.nextState = ChargerState::Stopping;
    }

    return result;
}
