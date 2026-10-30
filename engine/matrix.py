import math
from typing import Dict, Tuple, List, Any

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate great-circle distance between two spatial coordinates."""
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))

def build_travel_time_matrix(sites: List[Dict[str, Any]], rng) -> Dict[Tuple[str, str], Dict[str, Any]]:
    """Constructs symmetric spatial distance and asymmetric traffic time matrix."""
    matrix = {}
    for s1 in sites:
        for s2 in sites:
            s1_id = s1["site_id"]
            s2_id = s2["site_id"]
            if s1_id == s2_id:
                matrix[(s1_id, s2_id)] = {
                    "from_site_id": s1_id,
                    "to_site_id": s2_id,
                    "distance_km": 0.0,
                    "base_travel_time_min": 0.0,
                    "congestion_factor": 1.0
                }
            else:
                dist = round(haversine_km(s1["latitude"], s1["longitude"], s2["latitude"], s2["longitude"]) * 1.25, 2)
                base_time = round((dist / 35.0) * 60 + rng.uniform(1.0, 3.0), 2)
                matrix[(s1_id, s2_id)] = {
                    "from_site_id": s1_id,
                    "to_site_id": s2_id,
                    "distance_km": dist,
                    "base_travel_time_min": base_time,
                    "congestion_factor": round(rng.uniform(1.0, 1.3), 2)
                }
    return matrix
