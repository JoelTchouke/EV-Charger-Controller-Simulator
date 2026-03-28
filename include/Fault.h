#pragma once
#include "types.h"

class FaultState {
public:
    StateResult handle(const SensorData& input, const FaultStatus& faults);
};
