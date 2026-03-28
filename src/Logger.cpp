#include "Logger.h"
#include <iostream>

Logger::Logger(const std::string& filename) {
    file_.open(filename);
    if (file_.is_open()) {
        writeHeader();
    }
}

Logger::~Logger() {
    if (file_.is_open()) {
        file_.close();
    }
}

bool Logger::isOpen() const {
    return file_.is_open();
}

void Logger::writeHeader() {
    file_
        << "tick,state,"
        << "plug_inserted,ev_ready,user_start_request,user_stop_request,"
        << "voltage,current,temperature,ground_fault,relay_feedback_closed,"
        << "close_contactor,enable_charging,current_limit,"
        << "env_current,env_temperature,env_relay_feedback_closed\n";
}

void Logger::logTick(
    int tick,
    ChargerState state,
    const SensorData& input,
    const ActuatorCommands& commands,
    const EnvironmentState& env_state
) {
    if (!file_.is_open()) {
        return;
    }

    file_
        << tick << ","
        << chargerStateToString(state) << ","
        << input.plug_inserted << ","
        << input.ev_ready << ","
        << input.user_start_request << ","
        << input.user_stop_request << ","
        << input.voltage << ","
        << input.current << ","
        << input.temperature << ","
        << input.ground_fault << ","
        << input.relay_feedback_closed << ","
        << commands.close_contactor << ","
        << commands.enable_charging << ","
        << commands.current_limit << ","
        << env_state.current << ","
        << env_state.temperature << ","
        << env_state.relay_feedback_closed
        << "\n";
}

std::string chargerStateToString(ChargerState state) {
    switch (state) {
        case ChargerState::Idle: return "Idle";
        case ChargerState::VehicleConnected: return "VehicleConnected";
        case ChargerState::PreSafeChecks: return "PreSafeChecks";
        case ChargerState::Charging: return "Charging";
        case ChargerState::Stopping: return "Stopping";
        case ChargerState::Fault: return "Fault";
        default: return "Unknown";
    }
}