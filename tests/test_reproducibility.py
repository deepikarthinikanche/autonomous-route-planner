import hashlib
import json
from data.generator import SyntheticLogisticsGenerator

def test_deterministic_reproducibility():
    gen1 = SyntheticLogisticsGenerator(seed=20261022, num_sites=50, num_deliveries=100, num_vehicles=10)
    gen1.run(inject_anomalies=False)
    
    gen2 = SyntheticLogisticsGenerator(seed=20261022, num_sites=50, num_deliveries=100, num_vehicles=10)
    gen2.run(inject_anomalies=False)
    
    p1 = json.dumps({"sites": gen1.sites, "routes": gen1.routes, "stops": gen1.route_stops}, sort_keys=True)
    p2 = json.dumps({"sites": gen2.sites, "routes": gen2.routes, "stops": gen2.route_stops}, sort_keys=True)
    
    h1 = hashlib.sha256(p1.encode()).hexdigest()
    h2 = hashlib.sha256(p2.encode()).hexdigest()
    
    assert h1 == h2, "Checksum mismatch across identical seeds!"
    assert len(gen1.routes) == len(gen2.routes)
