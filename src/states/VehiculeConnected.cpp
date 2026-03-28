#include "../../include/VehiculeConnected.h"

StateResult VehiculeConnected::handle(const SensorData &input, const FaultStatus &faults)
{
    StateResult result;
    result.nextState = ChargerState::VehiculeDetected;
    result.commands.close_contactor = false;
    result.commands.enable_charging = false;
    result.commands.current_limit = 0;

    if(faults.any())
    {
        result.nextState = ChargerState::Fault;
    }
    else 
    {
        result.nextState = ChargerState::PreSafeChecks;
    }
}
