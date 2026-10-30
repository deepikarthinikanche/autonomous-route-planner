from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple

class VRPTWSolver:
    """
    Vehicle Routing Problem with Time Windows & Capacity Solver.
    Uses sequential heuristic clustering with constraint enforcement.
    """
    def __init__(self, sites: List[Dict[str, Any]], vehicles: List[Dict[str, Any]], 
                 capacities: List[Dict[str, Any]], shifts: List[Dict[str, Any]],
                 deliveries: List[Dict[str, Any]], travel_matrix: Dict[Tuple[str, str], Dict[str, Any]]):
        self.sites = {s["site_id"]: s for s in sites}
        self.vehicles = vehicles
        self.capacities = {c["id"]: c for c in capacities}
        self.shifts = shifts
        self.deliveries = deliveries
        self.matrix = travel_matrix
        
        self.depot_id = "STE-000000"
        self.routes: List[Dict[str, Any]] = []
        self.route_stops: List[Dict[str, Any]] = []
        self.unassigned: List[Dict[str, Any]] = []

    def solve(self) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
        candidates = list(self.deliveries)
        route_count = 0
        
        for veh, shf in zip(self.vehicles, self.shifts):
            if not candidates:
                break
                
            route_count += 1
            route_id = f"RTE-2026-{route_count:06d}"
            cap_meta = self.capacities[veh["capacity_id"]]
            
            curr_site = self.depot_id
            curr_time = datetime.strptime(f"{shf['shift_date']} {shf['start_time']}", "%Y-%m-%d %H:%M:%S")
            shift_end = datetime.strptime(f"{shf['shift_date']} {shf['end_time']}", "%Y-%m-%d %H:%M:%S")
            
            load_kg = 0.0
            load_m3 = 0.0
            total_dist = 0.0
            seq = 1
            assigned_this_route = []
            
            idx = 0
            while idx < len(candidates):
                deliv = candidates[idx]
                
                # Capacity constraints
                if (load_kg + deliv["package_weight_kg"] > cap_meta["weight"] or 
                    load_m3 + deliv["package_volume_m3"] > cap_meta["volume"]):
                    idx += 1
                    continue
                    
                # Refrigeration compatibility
                if deliv["req_refrigeration"] and not cap_meta["refrig"]:
                    idx += 1
                    continue
                    
                # Shift duration constraint check
                leg = self.matrix[(curr_site, deliv["site_id"])]
                arr_time = curr_time + timedelta(minutes=leg["base_travel_time_min"] * leg["congestion_factor"])
                dep_time = arr_time + timedelta(minutes=deliv["service_duration_min"])
                
                # Check return trip viability before shift end
                return_leg = self.matrix[(deliv["site_id"], self.depot_id)]
                return_duration = return_leg["base_travel_time_min"] * return_leg["congestion_factor"]
                if dep_time + timedelta(minutes=return_duration + 15) > shift_end:
                    idx += 1
                    continue
                    
                # Valid stop assignment
                stop_id = f"STP-{route_id}-{seq:03d}"
                total_dist += leg["distance_km"]
                load_kg += deliv["package_weight_kg"]
                load_m3 += deliv["package_volume_m3"]
                
                stop_record = {
                    "stop_id": stop_id,
                    "route_id": route_id,
                    "delivery_id": deliv["delivery_id"],
                    "sequence_index": seq,
                    "site_id": deliv["site_id"],
                    "planned_eta": arr_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "planned_etd": dep_time.strftime("%Y-%m-%d %H:%M:%S"),
                    "cumulative_distance_km": round(total_dist, 2),
                    "status": "PLANNED"
                }
                
                self.route_stops.append(stop_record)
                assigned_this_route.append(stop_record)
                
                curr_site = deliv["site_id"]
                curr_time = dep_time
                seq += 1
                candidates.pop(idx)
                
                if seq > 20: # Limit stops per driver route
                    break

            if assigned_this_route:
                # Return leg to depot
                depot_return = self.matrix[(curr_site, self.depot_id)]
                total_dist += depot_return["distance_km"]
                
                self.routes.append({
                    "route_id": route_id,
                    "vehicle_id": veh["vehicle_id"],
                    "driver_id": shf["driver_id"],
                    "shift_id": shf["shift_id"],
                    "route_date": shf["shift_date"],
                    "total_distance_km": round(total_dist, 2),
                    "total_stops": len(assigned_this_route),
                    "load_weight_kg": round(load_kg, 2),
                    "load_volume_m3": round(load_m3, 3),
                    "weight_utilization_pct": round((load_kg / cap_meta["weight"]) * 100, 2),
                    "status": "PLANNED"
                })

        # Track unserved deliveries
        self.unassigned = candidates
        for d in self.unassigned:
            d["status"] = "UNSERVED"

        return self.routes, self.route_stops, self.unassigned
