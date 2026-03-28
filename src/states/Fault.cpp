#include "fault_state.h"

StateResult FaultState::handle(const SensorData& input, const FaultStatus& faults) {
    (void)input;
    (void)faults;

    StateResult result;
    result.next_state = ChargerState::Fault;
    result.commands.close_contactor = false;
    result.commands.enable_charging = false;
    result.commands.current_limit = 0.0;

    return result;
}