import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any
from engine.matrix import haversine_km, build_travel_time_matrix
from engine.solver import VRPTWSolver
from engine.simulator import RouteExecutionSimulator

SEED = 20261022
DEPOT_LAT, DEPOT_LON = 37.7749, -122.4194
BBOX = {"min_lat": 37.6000, "max_lat": 37.9000, "min_lon": -122.5500, "max_lon": -122.2500}

class SyntheticLogisticsGenerator:
    def __init__(self, seed: int = SEED, num_sites: int = 500, num_deliveries: int = 2000, num_vehicles: int = 100):
        self.seed = seed
        self.rng = random.Random(seed)
        self.num_sites = num_sites
        self.num_deliveries = num_deliveries
        self.num_vehicles = num_vehicles
        
        self.sites = []
        self.vehicle_capacities = []
        self.vehicles = []
        self.drivers = []
        self.shifts = []
        self.time_windows = []
        self.orders = []
        self.deliveries = []
        self.travel_matrix = {}
        self.routes = []
        self.route_stops = []
        self.unassigned = []
        self.outcomes = []
        self.ground_truth_anomalies = []

    def run(self, inject_anomalies: bool = True):
        self._gen_depot_and_sites()
        self._gen_fleet_and_shifts()
        self._gen_orders_and_deliveries()
        self.travel_matrix = build_travel_time_matrix(self.sites[:100], self.rng) # Bounded matrix sample for solver
        
        # Route solver
        solver = VRPTWSolver(self.sites[:100], self.vehicles, self.vehicle_capacities, self.shifts, self.deliveries, self.travel_matrix)
        self.routes, self.route_stops, self.unassigned = solver.solve()
        
        # Discrete-event simulation
        simulator = RouteExecutionSimulator(self.route_stops, self.deliveries, self.time_windows, self.rng)
        self.outcomes = simulator.simulate()
        
        if inject_anomalies:
            self._inject_controlled_anomalies()

    def _gen_depot_and_sites(self):
        self.sites.append({
            "site_id": "STE-000000",
            "name": "Central Distribution Depot",
            "latitude": DEPOT_LAT,
            "longitude": DEPOT_LON,
            "region_id": "SF-BAY",
            "is_depot": True,
            "access_type": "DOCK",
            "status": "ACTIVE"
        })
        for i in range(1, self.num_sites + 1):
            lat = self.rng.uniform(BBOX["min_lat"], BBOX["max_lat"])
            lon = self.rng.uniform(BBOX["min_lon"], BBOX["max_lon"])
            self.sites.append({
                "site_id": f"STE-{i:06d}",
                "name": f"Customer Facility #{i}",
                "latitude": round(lat, 6),
                "longitude": round(lon, 6),
                "region_id": "SF-BAY",
                "is_depot": False,
                "access_type": self.rng.choice(["CURB", "ALLEY", "LOADING_BAY"]),
                "status": "ACTIVE"
            })

    def _gen_fleet_and_shifts(self):
        self.vehicle_capacities = [
            {"id": "CAP-001", "weight": 1500.0, "volume": 12.0, "refrig": False},
            {"id": "CAP-002", "weight": 3500.0, "volume": 25.0, "refrig": True},
            {"id": "CAP-003", "weight": 8000.0, "volume": 45.0, "refrig": True}
        ]
        for i in range(1, self.num_vehicles + 1):
            cap = self.rng.choice(self.vehicle_capacities)
            self.vehicles.append({
                "vehicle_id": f"VEH-{i:06d}",
                "capacity_id": cap["id"],
                "model": f"Van-T{cap['id'][-1]}",
                "avg_speed_kmh": 40.0,
                "fixed_cost": 75.0,
                "per_km_cost": 1.25,
                "status": "AVAILABLE"
            })
            
        num_drivers = int(self.num_vehicles * 1.2)
        for i in range(1, num_drivers + 1):
            self.drivers.append({
                "driver_id": f"DRV-{i:06d}",
                "name": f"Driver {i}",
                "license_tier": self.rng.choice(["B", "C", "CDL-A"]),
                "max_hours": 9.0,
                "status": "AVAILABLE"
            })

        for idx, drv in enumerate(self.drivers):
            st_hour = self.rng.choice([6, 7, 8])
            self.shifts.append({
                "shift_id": f"SHF-2026-{idx+1:06d}",
                "driver_id": drv["driver_id"],
                "shift_date": "2026-10-31",
                "start_time": f"{st_hour:02d}:00:00",
                "end_time": f"{st_hour+8:02d}:00:00",
                "max_duration_min": 480,
                "status": "SCHEDULED"
            })

    def _gen_orders_and_deliveries(self):
        self.time_windows = [
            {"id": "TW-01", "open": "08:00:00", "close": "12:00:00"},
            {"id": "TW-02", "open": "12:00:00", "close": "16:00:00"},
            {"id": "TW-03", "open": "09:00:00", "close": "17:00:00"}
        ]
        # Restrict delivery destination to active sub-sample
        candidate_sites = self.sites[1:100]
        for i in range(1, self.num_deliveries + 1):
            site = self.rng.choice(candidate_sites)
            order_id = f"ORD-2026-{i:06d}"
            weight = round(self.rng.uniform(15.0, 120.0), 2)
            volume = round(self.rng.uniform(0.1, 1.2), 3)
            
            self.orders.append({
                "order_id": order_id,
                "site_id": site["site_id"],
                "order_date": "2026-10-30",
                "priority": self.rng.choices([1, 2, 3], weights=[0.1, 0.7, 0.2])[0],
                "total_weight_kg": weight,
                "total_volume_m3": volume,
                "status": "SCHEDULED"
            })
            
            tw = self.rng.choice(self.time_windows)
            self.deliveries.append({
                "delivery_id": f"DEL-2026-{i:06d}",
                "order_id": order_id,
                "site_id": site["site_id"],
                "window_id": tw["id"],
                "package_weight_kg": weight,
                "package_volume_m3": volume,
                "service_duration_min": self.rng.choice([10, 15, 20]),
                "req_refrigeration": self.rng.random() < 0.15,
                "status": "PENDING"
            })

    def _inject_controlled_anomalies(self):
        if not self.routes or not self.route_stops:
            return
        # 1. Capacity Exceeded
        bad_route = self.routes[0]
        bad_route["load_weight_kg"] += 6000.0
        bad_route["weight_utilization_pct"] = 195.0
        self.ground_truth_anomalies.append({
            "anomaly_id": "ANOM-001",
            "entity": "Route",
            "entity_id": bad_route["route_id"],
            "issue_type": "CAPACITY_EXCEEDED",
            "details": "Weight exceeds vehicle maximum capacity limit."
        })
        # 2. Inverted Temporal Stop
        if len(self.route_stops) >= 2:
            s1, s2 = self.route_stops[0], self.route_stops[1]
            s2["planned_eta"] = (datetime.strptime(s1["planned_eta"], "%Y-%m-%d %H:%M:%S") - timedelta(minutes=45)).strftime("%Y-%m-%d %H:%M:%S")
            self.ground_truth_anomalies.append({
                "anomaly_id": "ANOM-002",
                "entity": "RouteStop",
                "entity_id": s2["stop_id"],
                "issue_type": "TEMPORAL_ORDER_INVERSION",
                "details": "Stop arrival precedes prior stop departure."
            })
        # 3. Spatial Out of Bounds
        bad_site = self.sites[1]
        bad_site["latitude"] = 85.0
        self.ground_truth_anomalies.append({
            "anomaly_id": "ANOM-003",
            "entity": "CustomerSite",
            "entity_id": bad_site["site_id"],
            "issue_type": "SPATIAL_OUT_OF_BOUNDS",
            "details": "Latitude outside designated SF-BAY operational region."
        })
