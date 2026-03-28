#pragma once

#include "types.h"
#include "IdleState.h"
#include "VehiculeConnected.h"
#include "PreSafeChecksState.h"
#include "ChargingState.h"
#include "StopState.h"
#include "Fault.h"

class StateMachine {
public:
    StateMachine();

    StateResult update(const SensorData& input, const FaultStatus& faults);
    ChargerState getCurrentState() const;

private:
    ChargerState current_state_;

    IdleState idle_state_;
    VehiculeConnected vehicle_detected_state_;
    PreSafeChecksState precharge_checks_state_;
    ChargingState charging_state_;
    StoppingState stopping_state_;
    FaultState fault_state_;
};