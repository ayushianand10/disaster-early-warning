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
from alert_engine import (
    evaluate_environmental_risk,
    validate_readings,
    DEFAULT_THRESHOLDS,
    ThresholdConfig
)
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

    def test_custom_configurable_thresholds_stricter(self):
        """Test that custom lower thresholds trigger CRITICAL earlier than default."""
        stricter_thresholds = ThresholdConfig(
            flood_rainfall_critical=50.0,
            flood_water_level_critical=50.0
        )
        # 60mm rain and 55% water level is NORMAL under default thresholds (70mm warn / 100mm crit),
        # but CRITICAL under stricter custom thresholds (50mm/50%)
        res_default = evaluate_environmental_risk(
            rainfall=60.0, water_level=55.0, temperature=25.0, aqi=50.0, thresholds=DEFAULT_THRESHOLDS
        )
        self.assertEqual(res_default["status"], "NORMAL")

        res_custom = evaluate_environmental_risk(
            rainfall=60.0, water_level=55.0, temperature=25.0, aqi=50.0, thresholds=stricter_thresholds
        )
        self.assertEqual(res_custom["status"], "CRITICAL")
        self.assertTrue(any("FLOOD" in h for h in res_custom["hazards"]))

    def test_custom_configurable_thresholds_relaxed(self):
        """Test that custom relaxed thresholds avoid CRITICAL triggers for moderate values."""
        relaxed_thresholds = ThresholdConfig(
            temp_critical=48.0,
            temp_warning=44.0
        )
        # 43°C is CRITICAL under default (42°C), but NORMAL under relaxed warning (44°C)
        res_default = evaluate_environmental_risk(
            rainfall=10.0, water_level=30.0, temperature=43.0, aqi=50.0, thresholds=DEFAULT_THRESHOLDS
        )
        self.assertEqual(res_default["status"], "CRITICAL")

        res_custom = evaluate_environmental_risk(
            rainfall=10.0, water_level=30.0, temperature=43.0, aqi=50.0, thresholds=relaxed_thresholds
        )
        self.assertEqual(res_custom["status"], "NORMAL")

    def test_exact_threshold_boundary_conditions(self):
        """Test exact equality on threshold limits (inclusive bounds >=)."""
        # Exact flood critical boundary (100.0 mm and 80.0 %)
        res_crit_flood = evaluate_environmental_risk(100.0, 80.0, 25.0, 50.0)
        self.assertEqual(res_crit_flood["status"], "CRITICAL")
        self.assertTrue(any("FLOOD" in h for h in res_crit_flood["hazards"]))

        # Exact flood warning boundary (70.0 mm rain, water safe at 40%)
        res_warn_flood = evaluate_environmental_risk(70.0, 40.0, 25.0, 50.0)
        self.assertEqual(res_warn_flood["status"], "WARNING")

        # Exact heat critical boundary (42.0 °C)
        res_crit_heat = evaluate_environmental_risk(10.0, 30.0, 42.0, 50.0)
        self.assertEqual(res_crit_heat["status"], "CRITICAL")

        # Exact heat warning boundary (38.0 °C)
        res_warn_heat = evaluate_environmental_risk(10.0, 30.0, 38.0, 50.0)
        self.assertEqual(res_warn_heat["status"], "WARNING")

        # Exact AQI critical boundary (200.0)
        res_crit_aqi = evaluate_environmental_risk(10.0, 30.0, 25.0, 200.0)
        self.assertEqual(res_crit_aqi["status"], "CRITICAL")

        # Exact AQI warning boundary (120.0)
        res_warn_aqi = evaluate_environmental_risk(10.0, 30.0, 25.0, 120.0)
        self.assertEqual(res_warn_aqi["status"], "WARNING")

        # Just below all warning thresholds -> NORMAL
        res_safe = evaluate_environmental_risk(69.9, 64.9, 37.9, 119.0)
        self.assertEqual(res_safe["status"], "NORMAL")

    def test_rainfall_configurable_critical_threshold_transitions(self):
        """
        Verify rainfall transitions with custom thresholds:
        - Warning at 40.0 mm
        - Critical at 60.0 mm
        Tests:
        1. Just below critical (59.9 mm) -> WARNING with warning explanation
        2. Exactly at critical (60.0 mm) -> CRITICAL with critical explanation
        3. Just above critical (60.1 mm & 65.0 mm) -> CRITICAL with critical explanation
        """
        custom_cfg = ThresholdConfig(
            flood_rainfall_warning=40.0,
            flood_rainfall_critical=60.0,
            flood_water_level_warning=65.0,
            flood_water_level_critical=80.0
        )

        # 1. Just below critical (59.9 mm): must be WARNING, not CRITICAL
        res_below = evaluate_environmental_risk(
            rainfall=59.9, water_level=30.0, temperature=25.0, aqi=50.0, thresholds=custom_cfg
        )
        self.assertEqual(res_below["status"], "WARNING")
        self.assertEqual(res_below["risk_rank"], 1)
        self.assertIn("FLOOD WARNING", res_below["hazards"])
        self.assertIn("Moderate flood watch", res_below["alert_message"])
        self.assertIn("59.9 mm ≥ 40.0 mm", res_below["alert_message"])

        # 2. Exactly at critical (60.0 mm): must be CRITICAL, reflecting 60.0 mm critical threshold
        res_exact = evaluate_environmental_risk(
            rainfall=60.0, water_level=30.0, temperature=25.0, aqi=50.0, thresholds=custom_cfg
        )
        self.assertEqual(res_exact["status"], "CRITICAL")
        self.assertEqual(res_exact["risk_rank"], 2)
        self.assertIn("CRITICAL FLOOD RISK", res_exact["hazards"])
        self.assertIn("60.0 mm ≥ 60.0 mm", res_exact["alert_message"])
        self.assertNotIn("Moderate flood watch", res_exact["alert_message"])

        # 3. Just above critical (60.1 mm): must be CRITICAL
        res_above = evaluate_environmental_risk(
            rainfall=60.1, water_level=30.0, temperature=25.0, aqi=50.0, thresholds=custom_cfg
        )
        self.assertEqual(res_above["status"], "CRITICAL")
        self.assertEqual(res_above["risk_rank"], 2)
        self.assertIn("CRITICAL FLOOD RISK", res_above["hazards"])
        self.assertIn("60.1 mm ≥ 60.0 mm", res_above["alert_message"])
        self.assertNotIn("Moderate flood watch", res_above["alert_message"])

        # 4. User's specific manual test vector (65.0 mm): must be CRITICAL
        res_manual = evaluate_environmental_risk(
            rainfall=65.0, water_level=30.0, temperature=25.0, aqi=50.0, thresholds=custom_cfg
        )
        self.assertEqual(res_manual["status"], "CRITICAL")
        self.assertEqual(res_manual["risk_rank"], 2)
        self.assertIn("CRITICAL FLOOD RISK", res_manual["hazards"])
        self.assertIn("65.0 mm ≥ 60.0 mm", res_manual["alert_message"])
        self.assertNotIn("Moderate flood watch", res_manual["alert_message"])

    def test_simultaneous_critical_hazards_highest_severity(self):
        """
        Verify that when multiple critical and warning hazards occur simultaneously,
        the overall status reflects the highest severity (CRITICAL) and all triggered
        hazards and explanations are included.
        """
        custom_cfg = ThresholdConfig(
            flood_rainfall_warning=40.0,
            flood_rainfall_critical=60.0,
            temp_warning=38.0,
            temp_critical=42.0,
            aqi_warning=120.0,
            aqi_critical=200.0
        )

        # Simultaneous Critical Rainfall (65mm) + Critical Heat (43°C) + Critical AQI (250)
        res_triple_crit = evaluate_environmental_risk(
            rainfall=65.0, water_level=30.0, temperature=43.0, aqi=250.0, thresholds=custom_cfg
        )
        self.assertEqual(res_triple_crit["status"], "CRITICAL")
        self.assertEqual(res_triple_crit["risk_rank"], 2)
        self.assertIn("CRITICAL FLOOD RISK", res_triple_crit["hazards"])
        self.assertIn("EXTREME HEAT RISK", res_triple_crit["hazards"])
        self.assertIn("SEVERE AIR POLLUTION", res_triple_crit["hazards"])
        # Check that explanations for all 3 critical hazards are present
        self.assertIn("65.0 mm ≥ 60.0 mm", res_triple_crit["alert_message"])
        self.assertIn("43.0°C ≥ 42.0°C", res_triple_crit["alert_message"])
        self.assertIn("250 ≥ 200", res_triple_crit["alert_message"])

    def test_mixed_severity_highest_precedence(self):
        """
        Verify that when one hazard is CRITICAL and another is WARNING,
        the overall risk status is CRITICAL (reflecting highest severity).
        """
        custom_cfg = ThresholdConfig(
            flood_rainfall_warning=40.0,
            flood_rainfall_critical=60.0,
            aqi_warning=120.0,
            aqi_critical=200.0
        )

        # Critical Rainfall (65mm) + Warning AQI (150) + Safe Temp (25°C)
        res_mixed = evaluate_environmental_risk(
            rainfall=65.0, water_level=30.0, temperature=25.0, aqi=150.0, thresholds=custom_cfg
        )
        self.assertEqual(res_mixed["status"], "CRITICAL")
        self.assertEqual(res_mixed["risk_rank"], 2)
        self.assertIn("CRITICAL FLOOD RISK", res_mixed["hazards"])
        self.assertIn("AIR QUALITY WARNING", res_mixed["hazards"])
        self.assertNotIn("SAFE PARAMETERS", res_mixed["hazards"])


if __name__ == "__main__":
    unittest.main()
