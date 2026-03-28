#pragma once
#include "types.h"

class IdleState {
public:
    StateResult handle(const SensorData& input, const FaultStatus& faults);
};