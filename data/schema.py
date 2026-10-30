from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime, date, time

class CustomerSiteSchema(BaseModel):
    site_id: str = Field(..., pattern=r"^STE-\d{6}$")
    name: str
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    region_id: str
    is_depot: bool
    access_type: Literal["DOCK", "CURB", "ALLEY", "LOADING_BAY"]
    status: Literal["ACTIVE", "INACTIVE"]

class VehicleCapacitySchema(BaseModel):
    id: str = Field(..., pattern=r"^CAP-\d{3}$")
    weight: float = Field(..., gt=0)
    volume: float = Field(..., gt=0)
    refrig: bool

class VehicleSchema(BaseModel):
    vehicle_id: str = Field(..., pattern=r"^VEH-\d{6}$")
    capacity_id: str
    model: str
    avg_speed_kmh: float = Field(..., gt=0)
    fixed_cost: float = Field(..., ge=0)
    per_km_cost: float = Field(..., ge=0)
    status: Literal["AVAILABLE", "MAINTENANCE", "RETIRED"]

class DriverSchema(BaseModel):
    driver_id: str = Field(..., pattern=r"^DRV-\d{6}$")
    name: str
    license_tier: Literal["B", "C", "CDL-A"]
    max_hours: float = Field(..., ge=1.0, le=14.0)
    status: Literal["AVAILABLE", "ON_DUTY", "OFF_DUTY"]

class ShiftSchema(BaseModel):
    shift_id: str = Field(..., pattern=r"^SHF-2026-\d{6}$")
    driver_id: str
    shift_date: str
    start_time: str
    end_time: str
    max_duration_min: int = Field(..., gt=0)
    status: Literal["SCHEDULED", "IN_PROGRESS", "COMPLETED"]

class OrderSchema(BaseModel):
    order_id: str = Field(..., pattern=r"^ORD-2026-\d{6}$")
    site_id: str
    order_date: str
    priority: int = Field(..., ge=1, le=5)
    total_weight_kg: float = Field(..., gt=0)
    total_volume_m3: float = Field(..., gt=0)
    status: Literal["PLACED", "SCHEDULED", "FULFILLED", "CANCELLED"]

class DeliverySchema(BaseModel):
    delivery_id: str = Field(..., pattern=r"^DEL-2026-\d{6}$")
    order_id: str
    site_id: str
    window_id: str
    package_weight_kg: float = Field(..., gt=0)
    package_volume_m3: float = Field(..., gt=0)
    service_duration_min: int = Field(..., gt=0)
    req_refrigeration: bool
    status: Literal["PENDING", "DISPATCHED", "DELIVERED", "FAILED", "UNSERVED"]
