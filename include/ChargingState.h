#pragma once
#include "types.h"

class ChargingState {
public:
    StateResult handle(const SensorData& input, const FaultStatus& faults);
};
