from typing import List, Dict, Any

class LogisticsValidator:
    """Validates relational schema, foreign keys, lifecycle rules, and domain constraints."""
    def __init__(self, sites, vehicles, drivers, shifts, orders, deliveries, routes, route_stops, outcomes):
        self.sites = sites
        self.vehicles = vehicles
        self.drivers = drivers
        self.shifts = shifts
        self.orders = orders
        self.deliveries = deliveries
        self.routes = routes
        self.route_stops = route_stops
        self.outcomes = outcomes
        self.errors = []

    def validate_all(self) -> Dict[str, Any]:
        self.check_primary_keys()
        self.check_foreign_keys()
        self.check_temporal_ordering()
        self.check_failed_reasons()
        return {
            "is_valid": len(self.errors) == 0,
            "error_count": len(self.errors),
            "errors": self.errors
        }

    def check_primary_keys(self):
        tables = [
            ("CustomerSite", self.sites, "site_id"),
            ("Vehicle", self.vehicles, "vehicle_id"),
            ("Driver", self.drivers, "driver_id"),
            ("Shift", self.shifts, "shift_id"),
            ("Order", self.orders, "order_id"),
            ("Delivery", self.deliveries, "delivery_id"),
            ("Route", self.routes, "route_id"),
            ("RouteStop", self.route_stops, "stop_id"),
            ("DeliveryOutcome", self.outcomes, "outcome_id"),
        ]
        for name, rows, pk in tables:
            seen = set()
            for r in rows:
                val = r[pk]
                if val in seen:
                    self.errors.append(f"Duplicate PK in {name}: {val}")
                seen.add(val)

    def check_foreign_keys(self):
        site_ids = {s["site_id"] for s in self.sites}
        order_ids = {o["order_id"] for o in self.orders}
        deliv_ids = {d["delivery_id"] for d in self.deliveries}
        route_ids = {r["route_id"] for r in self.routes}

        for d in self.deliveries:
            if d["order_id"] not in order_ids:
                self.errors.append(f"Orphan Delivery FK: order_id {d['order_id']}")
            if d["site_id"] not in site_ids:
                self.errors.append(f"Orphan Delivery FK: site_id {d['site_id']}")

        for s in self.route_stops:
            if s["route_id"] not in route_ids:
                self.errors.append(f"Orphan RouteStop FK: route_id {s['route_id']}")
            if s["delivery_id"] not in deliv_ids:
                self.errors.append(f"Orphan RouteStop FK: delivery_id {s['delivery_id']}")

    def check_temporal_ordering(self):
        # Stop ETA should not precede previous stop ETD
        for i in range(len(self.route_stops) - 1):
            s1 = self.route_stops[i]
            s2 = self.route_stops[i+1]
            if s1["route_id"] == s2["route_id"]:
                if s2["planned_eta"] < s1["planned_etd"]:
                    self.errors.append(f"Temporal order inversion between {s1['stop_id']} and {s2['stop_id']}")

    def check_failed_reasons(self):
        for out in self.outcomes:
            if out["status"] == "FAILED" and out["reason_code"] == "NONE":
                self.errors.append(f"Outcome {out['outcome_id']} marked FAILED without reason code.")
