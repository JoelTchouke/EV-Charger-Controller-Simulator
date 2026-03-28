#pragma once

enum class ChargerState
{
    Idle,
    VehicleConnected,
    PreSafeChecks,
    Charging,
    Stopping,
    Fault
};

struct SensorData
{
    bool plug_inserted;
    bool ev_ready;
    bool user_start_request;
    bool user_stop_request;

    float voltage;
    float current;
    float temperature;

    bool ground_fault;
    bool relay_feedback_closed;
};

struct ActuatorCommands
{
    bool close_contactor;
    bool enable_charging;
    float current_limit;
};

struct FaultStatus {
    bool overtemperature;
    bool overcurrent;
    bool ground_fault;
    bool relay_mismatch;

    bool any() const {
        return overtemperature || overcurrent || ground_fault || relay_mismatch;
    }
};

struct StateResult
{
    ChargerState nextState;
    ActuatorCommands commands;
};