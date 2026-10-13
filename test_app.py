"""
Unit and Integration Tests for Disaster Early Warning System
------------------------------------------------------------
Validates:
1. Input validation and boundary enforcement
2. Rule-based risk evaluation (NORMAL, WARNING, CRITICAL)
3. Multi-parameter Flood risk detection
4. Extreme Heatwave detection
5. Hazardous AQI detection
6. Storage manager operations (save, fetch, export CSV, clear)
7. Response time latency measurement
"""

import unittest
import time
from alert_engine import evaluate_environmental_risk, validate_readings, DEFAULT_THRESHOLDS
from storage_manager import StorageManager
from sample_data import DEMO_SCENARIOS, generate_simulated_history


class TestDisasterWarningSystem(unittest.TestCase):

    def test_input_validation_valid(self):
        """Test plausible sensor inputs are accepted."""
        is_valid, errors = validate_readings(rainfall=25.0, water_level=45.0, temperature=28.0, aqi=55.0)
        self.assertTrue(is_valid)
        self.assertEqual(len(errors), 0)

    def test_input_validation_negative_rainfall(self):
        """Test negative rainfall is rejected."""
        is_valid, errors = validate_readings(rainfall=-5.0, water_level=45.0, temperature=28.0, aqi=55.0)
        self.assertFalse(is_valid)
        self.assertTrue(any("negative" in e.lower() for e in errors))

    def test_input_validation_excessive_water_level(self):
        """Test water level exceeding 100% is rejected."""
        is_valid, errors = validate_readings(rainfall=10.0, water_level=120.0, temperature=28.0, aqi=55.0)
        self.assertFalse(is_valid)
        self.assertTrue(any("percentage" in e.lower() for e in errors))

    def test_input_validation_unrealistic_temperature(self):
        """Test temperature out of bounds is rejected."""
        is_valid, errors = validate_readings(rainfall=10.0, water_level=50.0, temperature=95.0, aqi=55.0)
        self.assertFalse(is_valid)

    def test_input_validation_null_value(self):
        """Test that None values are safely caught without crashing."""
        is_valid, errors = validate_readings(rainfall=None, water_level=50.0, temperature=25.0, aqi=50.0)
        self.assertFalse(is_valid)
        self.assertTrue(any("cannot be null" in e for e in errors))

    def test_input_validation_nan_and_inf(self):
        """Test that NaN and Infinity are caught and rejected."""
        is_valid, errors = validate_readings(rainfall=float("nan"), water_level=50.0, temperature=25.0, aqi=50.0)
        self.assertFalse(is_valid)
        self.assertTrue(any("nan" in e.lower() for e in errors))

        is_valid2, errors2 = validate_readings(rainfall=50.0, water_level=float("inf"), temperature=25.0, aqi=50.0)
        self.assertFalse(is_valid2)
        self.assertTrue(any("infinite" in e.lower() for e in errors2))

    def test_input_validation_non_numeric_string(self):
        """Test that invalid non-numeric strings are safely caught."""
        is_valid, errors = validate_readings(rainfall="invalid_val", water_level=50.0, temperature=25.0, aqi=50.0)
        self.assertFalse(is_valid)
        self.assertTrue(any("numeric reading" in e for e in errors))

    def test_normal_baseline_scenario(self):
        """Test that safe readings yield NORMAL risk."""
        result = evaluate_environmental_risk(
            rainfall=15.0, water_level=30.0, temperature=28.0, aqi=45.0
        )
        self.assertEqual(result["status"], "NORMAL")
        self.assertEqual(result["risk_rank"], 0)
        self.assertIn("SAFE PARAMETERS", result["hazards"])

    def test_critical_flood_risk(self):
        """Test combined heavy rainfall (>100mm) and high water level (>80%) triggers CRITICAL flood."""
        result = evaluate_environmental_risk(
            rainfall=135.0, water_level=88.0, temperature=24.0, aqi=50.0
        )
        self.assertEqual(result["status"], "CRITICAL")
        self.assertEqual(result["risk_rank"], 2)
        self.assertTrue(any("FLOOD" in h for h in result["hazards"]))

    def test_warning_level_conditions(self):
        """Test moderate conditions trigger WARNING status."""
        result = evaluate_environmental_risk(
            rainfall=75.0, water_level=50.0, temperature=26.0, aqi=60.0
        )
        self.assertEqual(result["status"], "WARNING")
        self.assertEqual(result["risk_rank"], 1)

    def test_critical_heatwave(self):
        """Test extreme temperature (>=42°C) triggers CRITICAL heat risk."""
        result = evaluate_environmental_risk(
            rainfall=0.0, water_level=20.0, temperature=44.2, aqi=75.0
        )
        self.assertEqual(result["status"], "CRITICAL")
        self.assertTrue(any("HEAT" in h for h in result["hazards"]))

    def test_critical_air_pollution(self):
        """Test AQI >= 200 triggers CRITICAL air quality alert."""
        result = evaluate_environmental_risk(
            rainfall=0.0, water_level=20.0, temperature=25.0, aqi=260.0
        )
        self.assertEqual(result["status"], "CRITICAL")
        self.assertTrue(any("POLLUTION" in h or "AIR" in h for h in result["hazards"]))

    def test_storage_manager_operations(self):
        """Test record persistence, CSV export, and clear operations."""
        sm = StorageManager(local_csv_path="test_temp_records.csv")
        sm.clear_records()

        # Add record
        record = {
            "timestamp": "2026-10-13 10:00:00",
            "rainfall_mm": 50.0,
            "water_level_pct": 40.0,
            "temperature_c": 30.0,
            "aqi": 70.0,
            "risk_level": "NORMAL",
            "alert_message": "Safe",
            "data_source": "Test Suite"
        }
        sm.save_record(record)
        self.assertEqual(len(sm.get_all_records()), 1)

        # Test CSV export bytes
        csv_bytes = sm.export_csv_bytes()
        self.assertIn(b"rainfall_mm", csv_bytes)
        self.assertIn(b"Test Suite", csv_bytes)

        # Clean up
        sm.clear_records()
        self.assertEqual(len(sm.get_all_records()), 0)

    def test_processing_latency_benchmark(self):
        """Measure latency of evaluation algorithm over 1000 iterations."""
        start_time = time.perf_counter()
        iterations = 1000
        for _ in range(iterations):
            evaluate_environmental_risk(
                rainfall=110.0, water_level=85.0, temperature=35.0, aqi=160.0
            )
        elapsed_sec = time.perf_counter() - start_time
        avg_latency_ms = (elapsed_sec / iterations) * 1000
        print(f"\n[Performance Benchmark] Average Risk Evaluation Latency: {avg_latency_ms:.4f} ms per evaluation")
        # Ensure evaluation takes less than 1ms per execution
        self.assertLess(avg_latency_ms, 1.0)


if __name__ == "__main__":
    unittest.main()
