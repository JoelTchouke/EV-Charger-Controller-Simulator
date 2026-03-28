#pragma once
#include "types.h"

class VehiculeConnected{
public:
    StateResult handle(const SensorData& input, const FaultStatus& faults);
};