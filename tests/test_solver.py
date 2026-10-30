from data.generator import SyntheticLogisticsGenerator

def test_capacity_and_service_constraints():
    gen = SyntheticLogisticsGenerator(seed=20261022, num_sites=50, num_deliveries=100, num_vehicles=10)
    gen.run(inject_anomalies=False)
    
    cap_map = {c["id"]: c for c in gen.vehicle_capacities}
    veh_map = {v["vehicle_id"]: v for v in gen.vehicles}
    
    for r in gen.routes:
        veh = veh_map[r["vehicle_id"]]
        cap = cap_map[veh["capacity_id"]]
        assert r["load_weight_kg"] <= cap["weight"], f"Route {r['route_id']} exceeds max weight"
        assert r["load_volume_m3"] <= cap["volume"], f"Route {r['route_id']} exceeds max volume"
