# Autonomous Route Planner & VRPTW Simulation Engine

**Role Assessment:** AI Forward Deployed Engineer (FDE) Code Challenge  
**Target Operational Horizon:** 2026-10-31  
**Reproducibility Seed:** `20261022`  
**Author:** Deepika Kanche  

---

## 1. Executive Summary & Architecture

This repository implements an end-to-end logistics optimization and simulation platform addressing the Vehicle Routing Problem with Time Windows (VRPTW), multi-tiered vehicle capacities, driver Hours of Service (HOS), and stochastic delivery execution outcomes.

The platform enforces strict relational integrity across master and transactional entities, isolates injected anomaly ground truth for validation testing, and simulates discrete transit delays under dynamic urban traffic congestion.

### Core Architectural Principles

- **Strict Master-Transactional Hierarchy:** Zero orphan records. Master entities (`CustomerSite`, `Vehicle`, `Driver`, `VehicleCapacity`) are instantiated prior to dependent transactions (`Order`, `Delivery`, `RouteStop`).
- **Explicit Lifecycle State Tracking:** Deliveries that cannot fit fleet capacity or shift limits are preserved with an explicit status of `UNSERVED` rather than being dropped silently.
- **Isolated Anomaly Ground Truth:** Injected negative scenarios (`CAPACITY_EXCEEDED`, `TEMPORAL_ORDER_INVERSION`, `SPATIAL_OUT_OF_BOUNDS`) are written directly to `output/ground_truth.json` without leaking into solver decision features.
- **Zero-Drift Reproducibility:** Uses a deterministic pseudo-random number generator (PRNG) with fixed seed `20261022`, asserted by automated SHA-256 hash checks across independent runs.

```text
├── data/
│   ├── generator.py            # Deterministic synthetic data generator (Seed: 20261022)
│   ├── schema.py               # Pydantic v2 domain schemas with validation constraints
│   └── validator.py            # Relational integrity, temporal, & reason-code validator
├── engine/
│   ├── matrix.py               # Haversine spatial calculations & dynamic traffic matrix
│   ├── solver.py               # VRPTW solver with multi-capacity & shift constraints
│   └── simulator.py            # Discrete-event execution & dynamic arrival/outcome simulation
├── observability/
│   └── metrics.py              # Operational KPIs (OTIF, on-time SLA, capacity utilization)
├── tests/
│   ├── test_reproducibility.py # SHA-256 double-generation assertions
│   ├── test_integrity.py       # Foreign key, primary key, and schema validation tests
│   └── test_solver.py          # Weight, volume, and time limit constraint tests
├── main.py                     # Unified CLI entry point
└── requirements.txt
```

---

## 2. Relational Data Dictionary

| Entity | Primary Key | Foreign Keys | Key Attributes & Constraints | Cardinality | Lifecycle States |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **`CustomerSite`** | `site_id` (`STE-000001`) | None | `latitude` ([-90, 90]), `longitude` ([-180, 180]), `access_type`, `region_id` | 1:N with Order | `ACTIVE`, `INACTIVE` |
| **`VehicleCapacity`**| `id` (`CAP-001`) | None | `weight` (> 0 kg), `volume` (> 0 m³), `refrig` (bool) | 1:N with Vehicle | `ACTIVE` |
| **`Vehicle`** | `vehicle_id` (`VEH-000001`) | `capacity_id` | `avg_speed_kmh`, `fixed_cost`, `per_km_cost`, `model` | 1:N with Route | `AVAILABLE`, `MAINTENANCE` |
| **`Driver`** | `driver_id` (`DRV-000001`) | None | `name`, `license_tier` (B, C, CDL-A), `max_hours` (<= 9.0) | 1:N with Shift | `AVAILABLE`, `ON_DUTY` |
| **`Shift`** | `shift_id` (`SHF-2026-000001`)| `driver_id` | `shift_date`, `start_time`, `end_time` (duration <= 8 hrs) | 1:N with Route | `SCHEDULED`, `COMPLETED` |
| **`Order`** | `order_id` (`ORD-2026-000001`)| `site_id` | `order_date`, `total_weight_kg`, `total_volume_m3`, `priority` (1-5) | 1:N with Delivery | `PLACED`, `SCHEDULED` |
| **`TimeWindow`** | `id` (`TW-01`) | None | `open_time`, `close_time` (`open` < `close`) | 1:N with Delivery | `ACTIVE` |
| **`Delivery`** | `delivery_id` (`DEL-2026-000001`)| `order_id`, `site_id`, `window_id` | `package_weight_kg`, `package_volume_m3`, `service_duration_min`, `req_refrigeration` | 1:1 with RouteStop | `PENDING`, `DISPATCHED`, `UNSERVED` |
| **`Route`** | `route_id` (`RTE-2026-000001`)| `vehicle_id`, `driver_id`, `shift_id` | `route_date`, `total_distance_km`, `load_weight_kg`, `weight_utilization_pct` | 1:N with RouteStop | `PLANNED`, `COMPLETED` |
| **`RouteStop`** | `stop_id` (`STP-RTE-...-001`)| `route_id`, `delivery_id` | `sequence_index`, `planned_eta`, `planned_etd`, `cumulative_distance_km` | 1:1 with Outcome | `PLANNED` |
| **`DeliveryOutcome`**| `outcome_id` (`OUT-2026-000001`)| `stop_id`, `delivery_id` | `actual_arrival`, `status` (`SUCCESS`, `FAILED`), `reason_code`, `is_on_time` | 1:1 with RouteStop | `RECORDED` |

---

## 3. Engineering Assumptions & Trade-offs

- **Sequential Insertion Heuristic:** Formulated with greedy sequential insertion evaluating multi-dimensional load packing (weight in kg and volume in m³) alongside shift viability. While Mixed-Integer Programming (MIP) or metaheuristics (such as Tabu Search or OR-Tools Guided Local Search) can optimize global network mileage further, sequential insertion was selected to deliver sub-second, deterministic execution and strict return-to-depot shift bounds.
- **Return Leg Guardrail:** A candidate stop is only scheduled if the vehicle can finish service and travel back to the central depot (`STE-000000`) before the driver's shift officially closes.
- **Traffic Modeling:** Distances incorporate an urban circuity factor ($1.25\times$ over Haversine straight lines), and travel times are adjusted using a dynamic congestion multiplier ($1.0\times - 1.3\times$) with simulated arrival jitter ($-5$ to $+20$ minutes).
- **SLA & OTIF Distinction:** On-Time arrival ($56.9\%$) evaluates whether arrival occurs between the window opening and closing time. On-Time In-Full (OTIF, $55.06\%$) strictly requires both punctual arrival **and** operational completion without failure codes (such as `DAMAGED_PACKAGE` or `ACCESS_DENIED_GATE`).

---

## 4. Setup & Quickstart

### Prerequisites

Python 3.10+ (tested on Python 3.12).

```bash
# 1. Clone repository
git clone https://github.com/deepikarthinikanche/autonomous-route-planner.git
cd autonomous-route-planner

# 2. Virtual environment setup
python -m venv venv

# On Linux/macOS:
source venv/bin/activate
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
```

### Running Test Verification

```bash
python -m pytest tests/ -v
```

### Running the End-to-End Pipeline

```bash
# Full execution: synthetic generation, solving, simulation, validation, and KPI scorecard
python main.py --mode full --seed 20261022 --sites 500 --deliveries 2000 --vehicles 100

# Clean validation mode: runs without injected anomalies to verify 100% schema & relational compliance
python main.py --mode validate --seed 20261022 --sites 500 --deliveries 2000 --vehicles 100
```

---

## 5. Baseline Performance Scorecard (Seed `20261022`)

```json
{
  "total_deliveries_demanded": 2000,
  "total_deliveries_planned": 870,
  "total_deliveries_unassigned": 1130,
  "total_routes_dispatched": 100,
  "total_fleet_distance_km": 15733.17,
  "avg_route_capacity_utilization_pct": 20.54,
  "success_rate_pct": 85.63,
  "on_time_arrival_pct": 56.9,
  "otif_rate_pct": 55.06,
  "failure_modes_summary": {
    "TIME_WINDOW_MISSED_LATE": 103,
    "CUSTOMER_UNAVAILABLE": 9,
    "ACCESS_DENIED_GATE": 7,
    "DAMAGED_PACKAGE": 6
  }
}
```

---

## 6. Anomaly Injections & Ground Truth Handling

In compliance with challenge requirements, edge cases are intentionally injected and tracked in `output/ground_truth.json`:

1. `CAPACITY_EXCEEDED` (`ANOM-001`): Artificially inflates a route's payload beyond the vehicle maximum.
2. `TEMPORAL_ORDER_INVERSION` (`ANOM-002`): Schedules stop arrival prior to the previous stop's departure.
3. `SPATIAL_OUT_OF_BOUNDS` (`ANOM-003`): Positions customer latitude outside the operational bounding box.

These labels are stored completely isolated from features consumed by the dispatch heuristic to avoid data leakage during evaluation.