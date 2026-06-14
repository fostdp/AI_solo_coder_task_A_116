import os
import asyncio
import json
from typing import List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Query
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .models import (
    DynamicsRequest, DynamicsResponse, OptimizationRequest,
    OptimizationResult, AlarmData
)
from .database import db_manager
from .modbus_client import modbus_client
from .dynamics import simulator
from .optimization import optimizer
from .alarm import alarm_manager

load_dotenv()


class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in list(self.active_connections):
            try:
                await connection.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()
latest_data = None
collection_task = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global collection_task
    try:
        db_manager.connect()
        print("Database connected")
    except Exception as e:
        print(f"Database connection failed: {e}")

    try:
        alarm_manager.connect_mqtt()
        print("MQTT connected")
    except Exception as e:
        print(f"MQTT connection failed: {e}")

    collection_task = asyncio.create_task(data_collection_loop())

    yield

    if collection_task:
        collection_task.cancel()
        try:
            await collection_task
        except asyncio.CancelledError:
            pass

    db_manager.close()
    alarm_manager.disconnect_mqtt()
    print("Shutdown complete")


app = FastAPI(
    title="古代水转大纺车动力学仿真与能效分析系统",
    description="基于FastAPI的水转大纺车动力学仿真、能效优化与实时监测系统",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


async def data_collection_loop():
    global latest_data
    interval = float(os.getenv("COLLECTION_INTERVAL", "5"))
    while True:
        try:
            data = collect_and_process_data()
            if data:
                latest_data = data
                await manager.broadcast({"type": "data", "data": data})
        except Exception as e:
            print(f"Data collection error: {e}")
        await asyncio.sleep(interval)


def collect_and_process_data() -> dict:
    modbus_data = modbus_client.read_all_data()

    if not modbus_data.get("water_wheel") or modbus_data["water_wheel"].get("water_speed", 0) == 0:
        water_speed = 2.5
        blade_angle = 45.0
        wheel_radius = 1.5
        gear_ratio = 8.0
        mechanical_efficiency = 0.85
        num_spindles = 32
        friction_coefficient = 0.05

        sim_result = simulator.simulate(
            water_speed=water_speed,
            blade_angle=blade_angle,
            wheel_radius=wheel_radius,
            gear_ratio=gear_ratio,
            mechanical_efficiency=mechanical_efficiency,
            num_spindles=num_spindles,
            friction_coefficient=friction_coefficient
        )
    else:
        sim_result = modbus_data

    try:
        db_manager.write_spinning_wheel_data(sim_result)
    except Exception as e:
        print(f"Write to DB error: {e}")

    try:
        alarms = alarm_manager.check_all(sim_result)
        for alarm in alarms:
            try:
                db_manager.write_alarm(alarm)
            except Exception:
                pass
    except Exception as e:
        print(f"Alarm check error: {e}")

    return sim_result


@app.get("/")
async def root():
    return {
        "name": "古代水转大纺车动力学仿真与能效分析系统",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "realtime_data": "/api/data",
            "dynamics_simulation": "/api/dynamics",
            "optimization": "/api/optimize",
            "alarms": "/api/alarms",
            "websocket": "/api/websocket"
        }
    }


@app.get("/api/data")
async def get_realtime_data(
    start_time: Optional[str] = Query(None, description="开始时间 ISO格式"),
    end_time: Optional[str] = Query(None, description="结束时间 ISO格式"),
    measurement: Optional[str] = Query(None, description="测量类型: water_wheel/transmission/spindle/system/alarm"),
    limit: int = Query(100, description="返回数据条数限制")
):
    if not start_time and not end_time and not measurement:
        if latest_data:
            return latest_data
        else:
            data = collect_and_process_data()
            return data

    try:
        if measurement:
            start_dt = datetime.fromisoformat(start_time) if start_time else None
            end_dt = datetime.fromisoformat(end_time) if end_time else None
            if start_dt:
                result = db_manager.query_timerange(measurement, start_dt, end_dt, limit)
            else:
                result = db_manager.query_latest_data(measurement, limit)
            return {"measurement": measurement, "data": result}
        else:
            return {"error": "请指定measurement参数"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"数据查询失败: {str(e)}")


@app.post("/api/dynamics", response_model=DynamicsResponse)
async def run_dynamics_simulation(request: DynamicsRequest):
    try:
        result = simulator.simulate(
            water_speed=request.water_speed,
            blade_angle=request.blade_angle,
            wheel_radius=request.wheel_radius,
            gear_ratio=request.gear_ratio,
            mechanical_efficiency=request.mechanical_efficiency,
            num_spindles=request.num_spindles,
            friction_coefficient=request.friction_coefficient
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"动力学仿真失败: {str(e)}")


@app.post("/api/optimize", response_model=OptimizationResult)
async def run_optimization(request: OptimizationRequest):
    try:
        result = optimizer.optimize(
            water_speed=request.water_speed,
            wheel_radius=request.wheel_radius,
            gear_ratio=request.gear_ratio,
            mechanical_efficiency=request.mechanical_efficiency,
            friction_coefficient=request.friction_coefficient,
            min_tension=request.min_tension,
            max_tension=request.max_tension,
            max_twist_cv=request.max_twist_cv,
            population_size=request.population_size,
            generations=request.generations
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"优化计算失败: {str(e)}")


@app.get("/api/alarms")
async def get_alarms(
    start_time: Optional[str] = Query(None, description="开始时间 ISO格式"),
    end_time: Optional[str] = Query(None, description="结束时间 ISO格式"),
    alarm_type: Optional[str] = Query(None, description="告警类型"),
    severity: Optional[str] = Query(None, description="告警级别: info/warning/critical"),
    limit: int = Query(100, description="返回条数限制")
):
    try:
        start_dt = datetime.fromisoformat(start_time) if start_time else None
        end_dt = datetime.fromisoformat(end_time) if end_time else None

        db_alarms = db_manager.query_alarms(
            start_time=start_dt,
            end_time=end_dt,
            alarm_type=alarm_type,
            severity=severity,
            limit=limit
        )

        if not db_alarms:
            active_alarms = alarm_manager.get_active_alarms(limit)
            return {"alarms": active_alarms, "count": len(active_alarms)}

        return {"alarms": db_alarms, "count": len(db_alarms)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"告警查询失败: {str(e)}")


@app.websocket("/api/websocket")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        if latest_data:
            await websocket.send_json({"type": "data", "data": latest_data})

        while True:
            data = await websocket.receive_text()
            try:
                msg = json.loads(data)
                if msg.get("type") == "ping":
                    await websocket.send_json({"type": "pong", "timestamp": datetime.now().isoformat()})
                elif msg.get("type") == "get_data":
                    if latest_data:
                        await websocket.send_json({"type": "data", "data": latest_data})
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
        print(f"WebSocket error: {e}")


@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "database": "connected" if db_manager._client else "disconnected",
        "mqtt": "connected" if alarm_manager.is_mqtt_connected() else "disconnected",
        "modbus": "connected" if modbus_client.is_connected() else "disconnected",
        "websocket_clients": len(manager.active_connections),
        "timestamp": datetime.now().isoformat()
    }
