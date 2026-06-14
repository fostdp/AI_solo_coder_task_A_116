import asyncio
import random
import time
import logging
from pymodbus.server import StartAsyncTcpServer
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.device import ModbusDeviceIdentification
from config import (
    ModbusConfig,
    ReportingConfig,
    WaterWheelConfig,
    BeltDriveConfig,
    SpindleConfig,
    YarnConfig,
    PowerConfig,
    WaterFlowConfig,
    RegisterMap,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("WaterWheelSimulator")


class SpindleData:
    def __init__(self, index: int):
        self.index = index
        self.rpm = 0.0
        self.tension = 0.0
        self.twist = 0.0
        self.is_broken = False
        self.break_count = 0
        self.rpm_fluctuation_phase = random.uniform(0, 6.28)


class WaterWheelSimulator:
    def __init__(self):
        self.water_wheel_rpm = 0.0
        self.water_flow_velocity = WaterFlowConfig.VELOCITY
        self.main_shaft_rpm = 0.0
        self.power_consumption = 0.0
        self.total_break_count = 0
        self.run_time_hours = 0
        self.run_time_minutes = 0
        self.start_time = time.time()
        self.last_update_time = time.time()

        self.spindles = [SpindleData(i) for i in range(SpindleConfig.COUNT)]
        self.store = self._create_datastore()
        self.context = ModbusServerContext(slaves=self.store, single=True)

    def _create_datastore(self):
        holding_registers = ModbusSequentialDataBlock(0, [0] * 200)
        slave = ModbusSlaveContext(hr=holding_registers, zero_mode=True)
        return {ModbusConfig.SLAVE_ID: slave}

    def _clamp(self, value: float, min_val: float, max_val: float) -> float:
        return max(min_val, min(max_val, value))

    def update_water_flow(self, dt: float):
        target_velocity = WaterFlowConfig.VELOCITY
        fluctuation = WaterFlowConfig.FLUCTUATION * WaterFlowConfig.VELOCITY
        noise = random.uniform(-fluctuation, fluctuation)
        self.water_flow_velocity = self._clamp(
            target_velocity + noise,
            WaterFlowConfig.MIN_VELOCITY,
            WaterFlowConfig.MAX_VELOCITY,
        )

    def update_water_wheel(self, dt: float):
        water_power = (
            WaterWheelConfig.TORQUE_COEFF
            * self.water_flow_velocity
            * WaterWheelConfig.DIAMETER
            / 2.0
        )

        friction_torque = WaterWheelConfig.FRICTION_COEFF * self.water_wheel_rpm

        net_torque = water_power - friction_torque

        if self.water_wheel_rpm > 0:
            load_torque = self._calculate_load_torque()
            net_torque -= load_torque

        angular_accel = net_torque / WaterWheelConfig.INERTIA
        self.water_wheel_rpm += angular_accel * dt * 60.0 / (2 * 3.14159)
        self.water_wheel_rpm = self._clamp(
            self.water_wheel_rpm, WaterWheelConfig.MIN_RPM, WaterWheelConfig.MAX_RPM
        )

    def _calculate_load_torque(self) -> float:
        active_spindles = sum(1 for s in self.spindles if not s.is_broken)
        if active_spindles == 0:
            return 0.0

        spindle_load = active_spindles * SpindleConfig.FRICTION_TORQUE
        spindle_load += active_spindles * 0.02 * self.water_wheel_rpm

        total_load = spindle_load / (
            BeltDriveConfig.EFFICIENCY * BeltDriveConfig.DRIVEN_PULLEY_RATIO
        )
        return total_load

    def update_main_shaft(self):
        if self.water_wheel_rpm <= 0:
            self.main_shaft_rpm = 0.0
            return

        theoretical_rpm = self.water_wheel_rpm * BeltDriveConfig.DRIVEN_PULLEY_RATIO
        slip_factor = 1.0 - BeltDriveConfig.SLIP * (
            1.0 + random.uniform(-0.1, 0.1)
        )
        self.main_shaft_rpm = theoretical_rpm * slip_factor

    def update_spindles(self, dt: float):
        for spindle in self.spindles:
            if spindle.is_broken:
                spindle.rpm = max(0.0, spindle.rpm - 50.0 * dt)
                if spindle.rpm < 1.0:
                    spindle.rpm = 0.0
                continue

            spindle.rpm_fluctuation_phase += dt * 2.0
            fluctuation = 1.0 + SpindleConfig.RPM_FLUCTUATION * random.uniform(
                -1.0, 1.0
            )
            fluctuation += 0.01 * SpindleConfig.RPM_FLUCTUATION * random.uniform(
                -1.0, 1.0
            )

            base_rpm = self.main_shaft_rpm * SpindleConfig.GEAR_RATIO
            spindle.rpm = base_rpm * fluctuation

            rpm_variation = 0.5 * random.uniform(-1, 1) * spindle.rpm / 100.0
            spindle.rpm += rpm_variation

            spindle.rpm = self._clamp(
                spindle.rpm, SpindleConfig.MIN_RPM, SpindleConfig.MAX_RPM
            )

    def update_yarn_tension(self):
        for spindle in self.spindles:
            if spindle.is_broken:
                spindle.tension = 0.0
                continue

            tension_base = YarnConfig.TENSION_NOMINAL
            rpm_factor = spindle.rpm / SpindleConfig.MAX_RPM
            tension_from_rpm = tension_base * (1.0 + 0.8 * rpm_factor)

            random_variation = random.uniform(-0.15, 0.15)
            spindle.tension = tension_from_rpm * (1.0 + random_variation)

            if random.random() < 0.02:
                spike = random.uniform(1.2, 2.0)
                spindle.tension *= spike

            spindle.tension = self._clamp(
                spindle.tension, YarnConfig.TENSION_MIN, YarnConfig.TENSION_MAX
            )

    def update_yarn_twist(self):
        for spindle in self.spindles:
            if spindle.is_broken:
                spindle.twist = 0.0
                continue

            twist_base = YarnConfig.TWIST_NOMINAL
            rpm_factor = spindle.rpm / SpindleConfig.MAX_RPM
            twist_from_rpm = twist_base * (0.5 + 0.5 * rpm_factor)

            random_variation = random.uniform(-0.1, 0.1)
            spindle.twist = twist_from_rpm * (1.0 + random_variation)
            spindle.twist = self._clamp(
                spindle.twist, YarnConfig.TWIST_MIN, YarnConfig.TWIST_MAX
            )

    def check_yarn_breaks(self):
        for spindle in self.spindles:
            if spindle.is_broken:
                continue

            if spindle.tension >= YarnConfig.BREAK_TENSION_THRESHOLD:
                spindle.is_broken = True
                spindle.break_count += 1
                self.total_break_count += 1
                logger.warning(
                    f"纱线断头！锭子 {spindle.index + 1}: "
                    f"张力={spindle.tension:.1f} cN (超过阈值)"
                )
                continue

            avg_twist = sum(s.twist for s in self.spindles if not s.is_broken)
            active_count = sum(1 for s in self.spindles if not s.is_broken)
            if active_count > 0:
                avg_twist /= active_count
                if avg_twist > 0:
                    twist_unevenness = abs(spindle.twist - avg_twist) / avg_twist
                    if twist_unevenness > YarnConfig.TWIST_UNEVENNESS_THRESHOLD:
                        if random.random() < 0.3:
                            spindle.is_broken = True
                            spindle.break_count += 1
                            self.total_break_count += 1
                            logger.warning(
                                f"纱线断头！锭子 {spindle.index + 1}: "
                                f"捻度不均={twist_unevenness:.2%}"
                            )

    def update_power_consumption(self):
        if self.water_wheel_rpm <= 0:
            self.power_consumption = PowerConfig.IDLE_POWER
            return

        active_spindles = sum(1 for s in self.spindles if not s.is_broken)

        water_power = (
            self.water_wheel_rpm
            / WaterWheelConfig.MAX_RPM
            * PowerConfig.MAX_POWER
            * 0.6
        )

        spindle_power = (
            active_spindles
            / SpindleConfig.COUNT
            * PowerConfig.MAX_POWER
            * 0.35
        )

        total_power = PowerConfig.IDLE_POWER + water_power + spindle_power
        total_power /= PowerConfig.EFFICIENCY

        variation = random.uniform(-0.05, 0.05)
        self.power_consumption = total_power * (1.0 + variation)
        self.power_consumption = self._clamp(
            self.power_consumption,
            PowerConfig.MIN_POWER,
            PowerConfig.MAX_POWER,
        )

    def update_run_time(self):
        elapsed = time.time() - self.start_time
        self.run_time_hours = int(elapsed // 3600)
        self.run_time_minutes = int((elapsed % 3600) // 60)

    def update_registers(self):
        slave = self.store[ModbusConfig.SLAVE_ID]
        scale = RegisterMap.REGISTER_SCALE

        slave.setValues(
            3,
            RegisterMap.WATER_WHEEL_RPM,
            [int(self.water_wheel_rpm * scale)],
        )
        slave.setValues(
            3,
            RegisterMap.WATER_FLOW_VELOCITY,
            [int(self.water_flow_velocity * scale)],
        )

        rpm_values = [int(s.rpm * scale) for s in self.spindles]
        slave.setValues(3, RegisterMap.SPINDLE_RPM_START, rpm_values)

        tension_values = [int(s.tension * scale) for s in self.spindles]
        slave.setValues(3, RegisterMap.YARN_TENSION_START, tension_values)

        twist_values = [int(s.twist * scale) for s in self.spindles]
        slave.setValues(3, RegisterMap.YARN_TWIST_START, twist_values)

        break_values = [1 if s.is_broken else 0 for s in self.spindles]
        slave.setValues(3, RegisterMap.YARN_BREAK_START, break_values)

        slave.setValues(
            3,
            RegisterMap.POWER_CONSUMPTION,
            [int(self.power_consumption * scale)],
        )

        broken_count = sum(1 for s in self.spindles if s.is_broken)
        slave.setValues(3, RegisterMap.SPINDLE_BREAK_COUNT, [broken_count])

        slave.setValues(
            3,
            RegisterMap.TOTAL_BREAK_COUNT,
            [self.total_break_count],
        )

        slave.setValues(3, RegisterMap.RUN_TIME_HOURS, [self.run_time_hours])
        slave.setValues(3, RegisterMap.RUN_TIME_MINUTES, [self.run_time_minutes])

    async def simulation_loop(self):
        logger.info("纺车模拟器启动...")
        logger.info(f"水流速度: {self.water_flow_velocity} m/s")
        logger.info(f"纱线规格: {YarnConfig.SPEC}")
        logger.info(f"上报间隔: {ReportingConfig.INTERVAL_SECONDS} 秒")

        last_report_time = time.time()

        while True:
            current_time = time.time()
            dt = current_time - self.last_update_time
            self.last_update_time = current_time

            self.update_water_flow(dt)
            self.update_water_wheel(dt)
            self.update_main_shaft()
            self.update_spindles(dt)
            self.update_yarn_tension()
            self.update_yarn_twist()
            self.check_yarn_breaks()
            self.update_power_consumption()
            self.update_run_time()
            self.update_registers()

            if current_time - last_report_time >= ReportingConfig.INTERVAL_SECONDS:
                self._report_status()
                last_report_time = current_time

            await asyncio.sleep(0.1)

    def _report_status(self):
        active_count = sum(1 for s in self.spindles if not s.is_broken)
        avg_rpm = (
            sum(s.rpm for s in self.spindles if not s.is_broken) / active_count
            if active_count > 0
            else 0
        )
        avg_tension = (
            sum(s.tension for s in self.spindles if not s.is_broken) / active_count
            if active_count > 0
            else 0
        )

        logger.info("=" * 60)
        logger.info(f"运行时间: {self.run_time_hours}小时 {self.run_time_minutes}分钟")
        logger.info(f"水轮转速: {self.water_wheel_rpm:.2f} rpm")
        logger.info(f"水流速度: {self.water_flow_velocity:.2f} m/s")
        logger.info(f"主轴转速: {self.main_shaft_rpm:.2f} rpm")
        logger.info(f"活跃锭子: {active_count}/{SpindleConfig.COUNT}")
        logger.info(f"平均锭速: {avg_rpm:.1f} rpm")
        logger.info(f"平均张力: {avg_tension:.1f} cN")
        logger.info(f"功耗: {self.power_consumption:.1f} W")
        logger.info(f"累计断头: {self.total_break_count} 次")
        logger.info("=" * 60)

    def set_water_velocity(self, velocity: float):
        WaterFlowConfig.VELOCITY = self._clamp(
            velocity, WaterFlowConfig.MIN_VELOCITY, WaterFlowConfig.MAX_VELOCITY
        )
        logger.info(f"水流速度设置为: {WaterFlowConfig.VELOCITY} m/s")

    def repair_spindle(self, index: int):
        if 0 <= index < SpindleConfig.COUNT:
            if self.spindles[index].is_broken:
                self.spindles[index].is_broken = False
                logger.info(f"锭子 {index + 1} 已修复")
            else:
                logger.info(f"锭子 {index + 1} 正常，无需修复")

    def repair_all_spindles(self):
        count = 0
        for spindle in self.spindles:
            if spindle.is_broken:
                spindle.is_broken = False
                count += 1
        logger.info(f"已修复 {count} 个锭子")


async def run_modbus_server(simulator: WaterWheelSimulator):
    identity = ModbusDeviceIdentification()
    identity.VendorName = "AncientTechnology"
    identity.ProductCode = "WW-Sim"
    identity.VendorUrl = "http://example.com"
    identity.ProductName = "Water Wheel Spinning Wheel Simulator"
    identity.ModelName = "YuanDynasty-Wheel"
    identity.MajorMinorRevision = "1.0.0"

    logger.info(
        f"启动 Modbus TCP 服务器: {ModbusConfig.HOST}:{ModbusConfig.PORT}"
    )

    await StartAsyncTcpServer(
        context=simulator.context,
        identity=identity,
        address=(ModbusConfig.HOST, ModbusConfig.PORT),
    )


async def main():
    simulator = WaterWheelSimulator()

    server_task = asyncio.create_task(run_modbus_server(simulator))
    sim_task = asyncio.create_task(simulator.simulation_loop())

    logger.info("元代水转大纺车传感器模拟器已启动")
    logger.info(f"Modbus TCP 从站地址: {ModbusConfig.HOST}:{ModbusConfig.PORT}")
    logger.info(f"从站 ID: {ModbusConfig.SLAVE_ID}")

    try:
        await asyncio.gather(server_task, sim_task)
    except KeyboardInterrupt:
        logger.info("模拟器已停止")


if __name__ == "__main__":
    asyncio.run(main())
