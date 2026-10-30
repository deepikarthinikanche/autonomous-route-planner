# Autonomous Delivery Planning & Simulation Engine (VRPTW)
**Role Assessment:** AI Forward Deployed Engineer (FDE) Code Challenge  
**Operational Date:** 2026-10-31  
**Reproducibility Seed:** `20261022`

---

## 1. Executive Summary & Architecture
This repository implements an end-to-end logistics optimization and simulation platform addressing the Vehicle Routing Problem with Time Windows (VRPTW), multi-tiered vehicle capacities, driver shift hours of service (HOS), and stochastic delivery outcomes.

The system is designed with:
- **Strict Master-Transactional Hierarchy:** Zero orphan records, valid foreign key relationships.
- **Deterministic Synthesis & Provenance:** Predictable PRNG sequence under seed `20261022`.
- **Isolated Anomaly Ground Truth:** Edge cases logged in `ground_truth.json` without leaking into solver features.
- **Auditable Lifecycle State Machine:** Explicit transitions for Deliveries, Shifts, and Routes.
- **Zero-Drift Reproducibility:** End-to-end double generation verifies identical sha256 checksums.

```
├── data/
│   ├── generator.py          # Deterministic synthetic data generator (Seed: 20261022)
│   ├── schema.py             # Pydantic v2 domain schemas & constraints
│   ├── validator.py          # Relational integrity, temporal, & arithmetic assertions
│   └── ground_truth.json     # Isolated label store for injected edge cases
├── engine/
│   ├── matrix.py             # Spatial distance (Haversine/Manhattan) & time matrices
│   ├── solver.py             # VRPTW solver (Greedy insertion + capacity/shift constraints)
│   └── simulator.py          # Discrete-event execution & dynamic arrival/outcome simulation
├── observability/
│   ├── metrics.py            # SLA adherence, OTIF, capacity utilization, failure rates
│   └── telemetry.py          # Immutable audit events & transition state log
├── tests/
│   ├── test_reproducibility.py # Double-run sha256 checksum comparisons
│   ├── test_integrity.py       # FK, PK, and domain validation tests
│   └── test_solver.py          # Route & schedule constraints verification
├── main.py                   # Unified CLI runner (generate, solve, simulate, validate)
└── requirements.txt
```

---

## 2. Data Dictionary & Entity Model

| Entity | PK | FK | Key Attributes & Constraints | Cardinality | Lifecycle States |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`CustomerSite`** | `site_id` (`STE-000001`) | None | `latitude` ([-90, 90]), `longitude` ([-180, 180]), `access_type`, `region_id` | 1:N with Order | `ACTIVE`, `INACTIVE` |
| **`VehicleCapacity`** | `capacity_id` (`CAP-001`) | None | `max_weight_kg` (> 0), `max_volume_m3` (> 0), `has_refrigeration` (bool) | 1:N with Vehicle | `ACTIVE` |
| **`Vehicle`** | `vehicle_id` (`VEH-000001`) | `capacity_id` | `make_model`, `avg_speed_kmh`, `fixed_cost`, `per_km_cost` | 1:N with Route | `AVAILABLE`, `MAINTENANCE`, `RETIRED` |
| **`Driver`** | `driver_id` (`DRV-000001`) | None | `name`, `license_tier`, `max_consecutive_hours` (<= 9.0) | 1:N with Shift | `ON_DUTY`, `OFF_DUTY`, `REST` |
| **`Shift`** | `shift_id` (`SHF-2026-000001`)| `driver_id` | `shift_date`, `start_time`, `end_time` (start < end, duration <= max) | 1:N with Route | `SCHEDULED`, `IN_PROGRESS`, `COMPLETED` |
| **`Order`** | `order_id` (`ORD-2026-000001`)| `site_id` | `order_date`, `total_weight_kg`, `total_volume_m3`, `priority` (1-5) | 1:N with Delivery | `PLACED`, `SCHEDULED`, `FULFILLED`, `CANCELLED` |
| **`TimeWindow`** | `window_id` (`TW-01`) | None | `open_time`, `close_time` (`open_time` < `close_time`) | 1:N with Delivery | `ACTIVE` |
| **`Delivery`** | `delivery_id` (`DEL-2026-000001`)| `order_id`, `site_id`, `window_id` | `package_weight_kg`, `package_volume_m3`, `service_duration_min`, `req_refrigeration` | 1:1 with RouteStop | `PENDING`, `DISPATCHED`, `DELIVERED`, `FAILED` |
| **`Route`** | `route_id` (`RTE-2026-000001`)| `vehicle_id`, `driver_id`, `shift_id` | `route_date`, `total_distance_km`, `total_time_min`, `capacity_utilization_pct` | 1:N with RouteStop | `PLANNED`, `DISPATCHED`, `COMPLETED`, `CANCELLED` |
| **`RouteStop`** | `stop_id` (`STP-RTE-2026-000001-001`)| `route_id`, `delivery_id` | `sequence_index` (1, 2, ...), `planned_eta`, `planned_etd`, `cumulative_distance_km` | 1:1 with DeliveryOutcome | `PENDING`, `EN_ROUTE`, `ARRIVED`, `DEPARTED` |
| **`TravelTimeMatrix`**| `matrix_id` (`TTM-...`) | `from_site_id`, `to_site_id` | `distance_km`, `base_travel_time_min`, `congestion_factor` | N:M bridge | `STATIC`, `DYNAMIC_UPDATED` |
| **`DeliveryOutcome`** | `outcome_id` (`OUT-2026-000001`)| `stop_id`, `delivery_id` | `actual_arrival`, `actual_departure`, `status` (`SUCCESS`, `FAILED`), `reason_code` | 1:1 with RouteStop | `RECORDED` |

---

## 3. Quickstart & Execution

### Setup
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Full Pipeline Run (Generation, Solving, Simulation, Validation)
```bash
python main.py --mode full --seed 20261022 --sites 500 --deliveries 2000 --vehicles 100
```

### Run Automated Test Suite
```bash
pytest tests/ -v
```
