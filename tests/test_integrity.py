from data.generator import SyntheticLogisticsGenerator
from data.validator import LogisticsValidator

def test_clean_generation_integrity():
    # Generator without injected edge cases should pass 100% of relational and temporal rules
    gen = SyntheticLogisticsGenerator(seed=20261022, num_sites=50, num_deliveries=150, num_vehicles=15)
    gen.run(inject_anomalies=False)
    
    validator = LogisticsValidator(gen.sites, gen.vehicles, gen.drivers, gen.shifts,
                                   gen.orders, gen.deliveries, gen.routes, gen.route_stops, gen.outcomes)
    report = validator.validate_all()
    assert report["is_valid"] is True, f"Integrity errors detected: {report['errors']}"
