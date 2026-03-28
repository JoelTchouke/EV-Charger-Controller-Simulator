#ifndef SCENARIOS_H
#define SCENARIOS_H

#include <vector>
#include "Environment.h"

std::vector<ScenarioEvent> makeNormalScenario();
std::vector<ScenarioEvent> makeOvertemperatureScenario();
std::vector<ScenarioEvent> makeGroundFaultScenario();

#endif