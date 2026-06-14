import os
from dotenv import load_dotenv

load_dotenv()


class ModbusConfig:
    HOST = os.getenv("MODBUS_HOST", "0.0.0.0")
    PORT = int(os.getenv("MODBUS_PORT", 5020))
    SLAVE_ID = int(os.getenv("MODBUS_SLAVE_ID", 1))


class ReportingConfig:
    INTERVAL_SECONDS = int(os.getenv("REPORT_INTERVAL", 60))


class WaterWheelConfig:
    MAX_RPM = 60.0
    MIN_RPM = 0.0
    INERTIA = 50.0
    FRICTION_COEFF = 0.05
    DIAMETER = 4.0
    TORQUE_COEFF = 800.0


class BeltDriveConfig:
    DRIVEN_PULLEY_RATIO = 5.0
    EFFICIENCY = 0.92
    SLIP = 0.02


class SpindleConfig:
    COUNT = 32
    MAX_RPM = 1500.0
    MIN_RPM = 0.0
    GEAR_RATIO = 12.0
    FRICTION_TORQUE = 0.15
    RPM_FLUCTUATION = 0.03


class YarnConfig:
    SPEC = os.getenv("YARN_SPEC", "cotton_20s")
    TENSION_MAX = 500.0
    TENSION_MIN = 0.0
    TENSION_NOMINAL = 150.0
    TWIST_MAX = 1000.0
    TWIST_MIN = 0.0
    TWIST_NOMINAL = 400.0
    BREAK_TENSION_THRESHOLD = 420.0
    TWIST_UNEVENNESS_THRESHOLD = 0.25


class PowerConfig:
    MAX_POWER = 5000.0
    MIN_POWER = 0.0
    IDLE_POWER = 150.0
    EFFICIENCY = 0.85


class WaterFlowConfig:
    VELOCITY = float(os.getenv("WATER_VELOCITY", 2.5))
    MIN_VELOCITY = 0.0
    MAX_VELOCITY = 5.0
    FLUCTUATION = 0.1


class RegisterMap:
    WATER_WHEEL_RPM = 0x0000
    WATER_FLOW_VELOCITY = 0x0001
    SPINDLE_RPM_START = 0x0010
    SPINDLE_RPM_COUNT = 32
    YARN_TENSION_START = 0x0030
    YARN_TENSION_COUNT = 32
    YARN_TWIST_START = 0x0050
    YARN_TWIST_COUNT = 32
    YARN_BREAK_START = 0x0070
    YARN_BREAK_COUNT = 32
    POWER_CONSUMPTION = 0x0090
    SPINDLE_BREAK_COUNT = 0x0091
    TOTAL_BREAK_COUNT = 0x0092
    RUN_TIME_HOURS = 0x0093
    RUN_TIME_MINUTES = 0x0094
    REGISTER_SCALE = 100
