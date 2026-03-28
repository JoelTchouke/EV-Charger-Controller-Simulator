#pragma once
#include "types.h"

class PreSafeChecksState{
public:
    StateResult handle(const SensorData& input, const FaultStatus& faults);   
};