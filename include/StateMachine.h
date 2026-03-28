#pragma once

#include "types.h"
#include "IdleState.h"
#include "VehiculeConnectedState.h"
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
    VehiculeDetected vehicle_detected_state_;
    PreSafeChecks precharge_checks_state_;
    Charging charging_state_;
    Stoppingg stopping_state_;
    Fault fault_state_;
};