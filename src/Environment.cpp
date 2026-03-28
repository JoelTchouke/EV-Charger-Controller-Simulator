#include "Environment.h"

Environment::Environment(const std::vector<ScenarioEvent>& events)
    : events_(events) {}

void Environment::applyEventsForCurrentTick() {
    for (const ScenarioEvent& event : events_) {
        if (event.tick != current_tick_) {
            continue;
        }

        switch (event.signal) {
            case EventSignal::PlugInserted:
                state_.plug_inserted = (event.value != 0.0f);
                break;

            case EventSignal::EvReady:
                state_.ev_ready = (event.value != 0.0f);
                break;

            case EventSignal::UserStartRequest:
                state_.user_start_request = (event.value != 0.0f);
                break;

            case EventSignal::UserStopRequest:
                state_.user_stop_request = (event.value != 0.0f);
                break;

            case EventSignal::Voltage:
                state_.voltage = event.value;
                break;

            case EventSignal::Temperature:
                state_.temperature = event.value;
                break;

            case EventSignal::GroundFault:
                state_.ground_fault = (event.value != 0.0f);
                break;
        }
    }
}

void Environment::applyControllerCommands(const ActuatorCommands& commands) {
    state_.relay_feedback_closed = commands.close_contactor;

    if (commands.enable_charging &&
        state_.plug_inserted &&
        state_.ev_ready &&
        state_.relay_feedback_closed &&
        !state_.ground_fault) {
        state_.current = commands.current_limit;
    } else {
        state_.current = 0.0f;
    }
}

SensorData Environment::getSensorData() const {
    SensorData input{};

    input.plug_inserted = state_.plug_inserted;
    input.ev_ready = state_.ev_ready;
    input.user_start_request = state_.user_start_request;
    input.user_stop_request = state_.user_stop_request;

    input.voltage = state_.voltage;
    input.current = state_.current;
    input.temperature = state_.temperature;

    input.ground_fault = state_.ground_fault;
    input.relay_feedback_closed = state_.relay_feedback_closed;

    return input;
}

const EnvironmentState& Environment::getState() const {
    return state_;
}

void Environment::advanceTick() {
    current_tick_++;
}

int Environment::getCurrentTick() const {
    return current_tick_;
}