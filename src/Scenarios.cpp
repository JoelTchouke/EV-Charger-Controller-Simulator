#include "Scenarios.h"

std::vector<ScenarioEvent> makeNormalScenario() {
    return {
        {2, EventSignal::PlugInserted, 1.0f},
        {3, EventSignal::EvReady, 1.0f},
        {4, EventSignal::UserStartRequest, 1.0f},
        {10, EventSignal::UserStopRequest, 1.0f}
    };
}

std::vector<ScenarioEvent> makeOvertemperatureScenario() {
    return {
        {2, EventSignal::PlugInserted, 1.0f},
        {3, EventSignal::EvReady, 1.0f},
        {4, EventSignal::UserStartRequest, 1.0f},
        {7, EventSignal::Temperature, 95.0f}
    };
}

std::vector<ScenarioEvent> makeGroundFaultScenario() {
    return {
        {2, EventSignal::PlugInserted, 1.0f},
        {3, EventSignal::EvReady, 1.0f},
        {4, EventSignal::UserStartRequest, 1.0f},
        {6, EventSignal::GroundFault, 1.0f}
    };
}