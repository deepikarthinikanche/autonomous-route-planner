from datetime import datetime, timedelta
from typing import List, Dict, Any

class RouteExecutionSimulator:
    """
    Simulates actual fleet execution, stochastic road travel delays,
    time-window SLA evaluation, and business failure modes.
    """
    def __init__(self, route_stops: List[Dict[str, Any]], deliveries: List[Dict[str, Any]],
                 time_windows: List[Dict[str, Any]], rng):
        self.route_stops = route_stops
        self.deliveries = {d["delivery_id"]: d for d in deliveries}
        self.time_windows = {w["id"]: w for w in time_windows}
        self.rng = rng
        self.outcomes: List[Dict[str, Any]] = []

    def simulate(self) -> List[Dict[str, Any]]:
        for idx, stop in enumerate(self.route_stops):
            deliv = self.deliveries[stop["delivery_id"]]
            tw = self.time_windows[deliv["window_id"]]
            
            planned_eta = datetime.strptime(stop["planned_eta"], "%Y-%m-%d %H:%M:%S")
            # Inject traffic jitter (-5 to +20 minutes)
            jitter_min = self.rng.uniform(-5.0, 20.0)
            actual_arr = planned_eta + timedelta(minutes=jitter_min)
            actual_dep = actual_arr + timedelta(minutes=deliv["service_duration_min"])
            
            tw_open = datetime.strptime(f"2026-10-31 {tw['open']}", "%Y-%m-%d %H:%M:%S")
            tw_close = datetime.strptime(f"2026-10-31 {tw['close']}", "%Y-%m-%d %H:%M:%S")
            
            is_success = True
            reason = "NONE"
            
            # Failure Mode 1: Missed time window (> 15 min late)
            if actual_arr > tw_close + timedelta(minutes=15):
                is_success = False
                reason = "TIME_WINDOW_MISSED_LATE"
            # Failure Mode 2: Unplanned operational exception (3% probability)
            elif self.rng.random() < 0.03:
                is_success = False
                reason = self.rng.choice(["CUSTOMER_UNAVAILABLE", "ACCESS_DENIED_GATE", "DAMAGED_PACKAGE"])
            
            outcome = {
                "outcome_id": f"OUT-2026-{idx+1:06d}",
                "stop_id": stop["stop_id"],
                "delivery_id": deliv["delivery_id"],
                "actual_arrival": actual_arr.strftime("%Y-%m-%d %H:%M:%S"),
                "actual_departure": actual_dep.strftime("%Y-%m-%d %H:%M:%S"),
                "status": "SUCCESS" if is_success else "FAILED",
                "reason_code": reason,
                "is_on_time": tw_open <= actual_arr <= tw_close
            }
            self.outcomes.append(outcome)
            
        return self.outcomes
