#include "state_machine.h"

StateMachine::StateMachine() : current_state_(ChargerState::Idle) {}

StateResult StateMachine::update(const SensorData& input, const FaultStatus& faults) {
    StateResult result;

    switch (current_state_) {
        case ChargerState::Idle:
            result = idle_state_.handle(input, faults);
            break;
        case ChargerState::VehicleDetected:
            result = vehicle_detected_state_.handle(input, faults);
            break;
        case ChargerState::PreChargeChecks:
            result = precharge_checks_state_.handle(input, faults);
            break;
        case ChargerState::Charging:
            result = charging_state_.handle(input, faults);
            break;
        case ChargerState::Stopping:
            result = stopping_state_.handle(input, faults);
            break;
        case ChargerState::Fault:
            result = fault_state_.handle(input, faults);
            break;
    }

    current_state_ = result.next_state;
    return result;
}

ChargerState StateMachine::getCurrentState() const {
    return current_state_;
}