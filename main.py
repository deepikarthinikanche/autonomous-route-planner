import argparse
import json
from pathlib import Path
from data.generator import SyntheticLogisticsGenerator
from data.validator import LogisticsValidator
from observability.metrics import calculate_operational_kpis

def main():
    parser = argparse.ArgumentParser(description="Autonomous VRPTW Optimization & Simulation Engine")
    parser.add_argument("--mode", choices=["generate", "validate", "full"], default="full", help="Execution mode")
    parser.add_argument("--seed", type=int, default=20261022, help="Deterministic seed")
    parser.add_argument("--sites", type=int, default=500, help="Number of customer sites")
    parser.add_argument("--deliveries", type=int, default=2000, help="Number of deliveries")
    parser.add_argument("--vehicles", type=int, default=100, help="Number of fleet vehicles")
    parser.add_argument("--outdir", type=str, default="output", help="Output directory for generated artifacts")
    
    args = parser.parse_args()
    outpath = Path(args.outdir)
    outpath.mkdir(exist_ok=True, parents=True)
    
    print(f"[*] Initializing Logistics Generator (Seed: {args.seed})...")
    gen = SyntheticLogisticsGenerator(seed=args.seed, num_sites=args.sites, num_deliveries=args.deliveries, num_vehicles=args.vehicles)
    gen.run(inject_anomalies=(args.mode != "validate"))
    
    print(f"[+] Master sites generated: {len(gen.sites)}")
    print(f"[+] Orders: {len(gen.orders)} | Deliveries: {len(gen.deliveries)}")
    print(f"[+] Dispatched Routes: {len(gen.routes)} | Planned Stops: {len(gen.route_stops)}")
    
    # Validation
    validator = LogisticsValidator(gen.sites, gen.vehicles, gen.drivers, gen.shifts,
                                   gen.orders, gen.deliveries, gen.routes, gen.route_stops, gen.outcomes)
    val_report = validator.validate_all()
    print(f"[*] Validation Check: {'PASS' if val_report['is_valid'] else 'ANOMALIES DETECTED'} (Errors found: {val_report['error_count']})")
    
    # KPIs
    kpis = calculate_operational_kpis(gen.routes, gen.outcomes, gen.deliveries, gen.unassigned)
    print("\n--- OPERATIONAL METRICS & SLA SCORECARD ---")
    print(json.dumps(kpis, indent=2))
    
    # Save artifacts
    with open(outpath / "ground_truth.json", "w") as f:
        json.dump(gen.ground_truth_anomalies, f, indent=2)
    with open(outpath / "metrics_report.json", "w") as f:
        json.dump(kpis, f, indent=2)
    with open(outpath / "validation_summary.json", "w") as f:
        json.dump(val_report, f, indent=2)
    print(f"\n[+] Artifacts successfully persisted to ./{args.outdir}/")

if __name__ == "__main__":
    main()
