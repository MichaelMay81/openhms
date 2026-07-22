from typing import List, Optional
from pydantic import BaseModel, Field

class PVChannel(BaseModel):
    id: int
    voltage: float = Field(..., description="Voltage in Volts")
    current: float = Field(..., description="Current in Amperes")
    power: float = Field(..., description="Power in Watts")
    daily_energy: float = Field(0.0, description="Daily Energy in kWh")
    total_energy: float = Field(0.0, description="Total Energy in kWh")

class InverterMetrics(BaseModel):
    active_power: float = Field(0.0, description="AC Active Power in Watts")
    grid_voltage: float = Field(0.0, description="Grid Voltage in Volts")
    grid_frequency: float = Field(0.0, description="Grid Frequency in Hertz")
    temperature: float = Field(0.0, description="Internal Temperature in Celsius")
    efficiency: float = Field(0.0, description="Inverter Efficiency in Percent")
    daily_energy: float = Field(0.0, description="Daily Energy in kWh")
    total_energy: float = Field(0.0, description="Total Energy in kWh")
    power_limit_pct: Optional[float] = Field(None, description="Power limit as percentage (0-100)")
    power_limit_w: Optional[float] = Field(None, description="Power limit in Watts")
    pv_channels: List[PVChannel] = []
    is_connected: bool = False
    last_update: float = 0.0

class InverterInfo(BaseModel):
    dtu_sn: str = "N/A"
    inverter_sn: str = "N/A"
    firmware_version: str = "N/A"
    hardware_model: str = "N/A"
    wifi_ssid: str = "N/A"
    last_update: float = 0.0

class LogEntry(BaseModel):
    timestamp: float
    level: str
    message: str
