#pragma once
#include "types.h"

class StoppingState {
public:
    StateResult handle(const SensorData& input, const FaultStatus& faults);
};
