#ifndef LOGGER_H
#define LOGGER_H

#include <fstream>
#include <string>
#include "types.h"
#include "Environment.h"

class Logger {
private:
    std::ofstream file_;

public:
    explicit Logger(const std::string& filename);
    ~Logger();

    bool isOpen() const;

    void writeHeader();
    void logTick(
        int tick,
        ChargerState state,
        const SensorData& input,
        const ActuatorCommands& commands,
        const EnvironmentState& env_state
    );
};

std::string chargerStateToString(ChargerState state);

#endif