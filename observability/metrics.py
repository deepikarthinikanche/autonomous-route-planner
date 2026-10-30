from typing import List, Dict, Any

def calculate_operational_kpis(routes: List[Dict[str, Any]], outcomes: List[Dict[str, Any]], 
                               deliveries: List[Dict[str, Any]], unassigned: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculates SLA, OTIF, utilization, and cost metrics."""
    total_deliveries = len(deliveries)
    total_outcomes = len(outcomes)
    
    successful = sum(1 for o in outcomes if o["status"] == "SUCCESS")
    on_time = sum(1 for o in outcomes if o["is_on_time"])
    otif = sum(1 for o in outcomes if o["status"] == "SUCCESS" and o["is_on_time"])
    
    avg_weight_util = (sum(r["weight_utilization_pct"] for r in routes) / len(routes)) if routes else 0.0
    total_dist_km = sum(r["total_distance_km"] for r in routes)
    
    # Reason code breakdown
    failures_by_reason = {}
    for o in outcomes:
        if o["status"] == "FAILED":
            reason = o["reason_code"]
            failures_by_reason[reason] = failures_by_reason.get(reason, 0) + 1
            
    return {
        "total_deliveries_demanded": total_deliveries,
        "total_deliveries_planned": total_outcomes,
        "total_deliveries_unassigned": len(unassigned),
        "total_routes_dispatched": len(routes),
        "total_fleet_distance_km": round(total_dist_km, 2),
        "avg_route_capacity_utilization_pct": round(avg_weight_util, 2),
        "success_rate_pct": round((successful / total_outcomes * 100), 2) if total_outcomes > 0 else 0.0,
        "on_time_arrival_pct": round((on_time / total_outcomes * 100), 2) if total_outcomes > 0 else 0.0,
        "otif_rate_pct": round((otif / total_outcomes * 100), 2) if total_outcomes > 0 else 0.0,
        "failure_modes_summary": failures_by_reason
    }
