#include <iostream>
#include <vector>
#include <string>

#include "Environment.h"
#include "StateMachine.h"
#include "types.h"
#include "Logger.h"
#include "Scenarios.h"

using namespace std;

string contactorStateToString(bool closed) {
    return closed ? "Closed" : "Open";
}

void printTick(
    int tick,
    ChargerState state,
    const ActuatorCommands& commands,
    const EnvironmentState& env_state
) {
    cout << "Tick: " << tick << "\n";
    cout << "State: " << chargerStateToString(state) << "\n";
    cout << "Contactor Command: " << contactorStateToString(commands.close_contactor) << "\n";
    cout << "Charging Enabled: " << commands.enable_charging << "\n";
    cout << "Current Limit: " << commands.current_limit << "\n";
    cout << "Measured Current: " << env_state.current << "\n";
    cout << "Relay Feedback: " << contactorStateToString(env_state.relay_feedback_closed) << "\n";
    cout << "Temperature: " << env_state.temperature << "\n";
    cout << "------------------------------------\n";
}

void runScenario(
    const string& scenario_name,
    const vector<ScenarioEvent>& events,
    int total_ticks
) {
    Environment env(events);
    StateMachine sm;
    Logger logger(scenario_name + ".csv");

    if (!logger.isOpen()) {
        cerr << "Failed to open log file for scenario: " << scenario_name << "\n";
        return;
    }

    cout << "\n===== Running Scenario: " << scenario_name << " =====\n";

    for (int i = 0; i < total_ticks; i++) {
        env.applyEventsForCurrentTick();

        SensorData input = env.getSensorData();

        // Replace this if your state machine internally evaluates faults.
        FaultStatus faults{};
        StateResult result = sm.update(input, faults);

        env.applyControllerCommands(result.commands);

        printTick(env.getCurrentTick(), result.nextState, result.commands, env.getState());

        logger.logTick(
            env.getCurrentTick(),
            result.nextState,
            input,
            result.commands,
            env.getState()
        );

        env.advanceTick();
    }
}

int main() {
    runScenario("normal_scenario", makeNormalScenario(), 15);
    runScenario("overtemperature_scenario", makeOvertemperatureScenario(), 15);
    runScenario("ground_fault_scenario", makeGroundFaultScenario(), 15);

    return 0;
}