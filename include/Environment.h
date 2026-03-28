#ifndef ENVIRONMENT_H
#define ENVIRONMENT_H

#include <vector>
#include "types.h"

enum class EventSignal {
    PlugInserted,
    EvReady,
    UserStartRequest,
    UserStopRequest,
    Voltage,
    Temperature,
    GroundFault
};

struct ScenarioEvent {
    int tick;
    EventSignal signal;
    float value;
};

struct EnvironmentState {
    bool plug_inserted = false;
    bool ev_ready = false;
    bool user_start_request = false;
    bool user_stop_request = false;

    float voltage = 240.0f;
    float current = 0.0f;
    float temperature = 25.0f;

    bool ground_fault = false;
    bool relay_feedback_closed = false;
};

class Environment {
private:
    EnvironmentState state_;
    std::vector<ScenarioEvent> events_;
    int current_tick_ = 0;

public:
    explicit Environment(const std::vector<ScenarioEvent>& events);

    void applyEventsForCurrentTick();
    void applyControllerCommands(const ActuatorCommands& commands);

    SensorData getSensorData() const;
    const EnvironmentState& getState() const;

    void advanceTick();
    int getCurrentTick() const;
};

#endif