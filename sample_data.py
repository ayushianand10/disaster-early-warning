"""
Sample and Demonstration Scenarios for Disaster Early Warning System
---------------------------------------------------------------------
Provides pre-configured one-click classroom/viva scenarios and historical
time-series generator to demonstrate normal, warning, and critical states.
"""

from datetime import datetime, timedelta
from typing import Dict, List, Any
import random
from alert_engine import evaluate_environmental_risk, DEFAULT_THRESHOLDS

DEMO_SCENARIOS: Dict[str, Dict[str, Any]] = {
    "Normal Conditions (Baseline)": {
        "description": "Clear skies, normal reservoir level, pleasant temperature, good air quality.",
        "rainfall": 12.0,
        "water_level": 32.0,
        "temperature": 27.5,
        "aqi": 48.0,
        "source": "Simulated Demo (Normal)"
    },
    "Moderate Weather Watch (Warning)": {
        "description": "Continuous rainfall and climbing water levels near watch thresholds.",
        "rainfall": 78.0,
        "water_level": 68.0,
        "temperature": 29.0,
        "aqi": 95.0,
        "source": "Simulated Demo (Warning)"
    },
    "Critical Flood Emergency (Multi-Parameter)": {
        "description": "Torrential downpour combined with reservoir water level at overflow point.",
        "rainfall": 142.0,
        "water_level": 91.5,
        "temperature": 23.0,
        "aqi": 55.0,
        "source": "Simulated Demo (Flood Crisis)"
    },
    "Extreme Heatwave Alert": {
        "description": "Severe heat spike exceeding critical temperature threshold.",
        "rainfall": 0.0,
        "water_level": 22.0,
        "temperature": 44.8,
        "aqi": 115.0,
        "source": "Simulated Demo (Heatwave)"
    },
    "Hazardous Air Quality Incident": {
        "description": "Industrial smog / seasonal inversion pushing AQI into hazardous zone.",
        "rainfall": 2.0,
        "water_level": 28.0,
        "temperature": 21.0,
        "aqi": 285.0,
        "source": "Simulated Demo (Pollution)"
    }
}


def generate_simulated_history(num_records: int = 24) -> List[Dict[str, Any]]:
    """
    Generates a realistic historical timeline (e.g. past 24 hours in 1-hour intervals)
    demonstrating transitions from normal to elevated risk.
    """
    history: List[Dict[str, Any]] = []
    base_time = datetime.now() - timedelta(hours=num_records)

    # Base realistic parameters with a slight mid-day rainstorm or heat surge
    curr_rain = 10.0
    curr_water = 35.0
    curr_temp = 28.0
    curr_aqi = 60.0

    for i in range(num_records):
        timestamp = base_time + timedelta(hours=i)

        # Introduce a realistic simulated storm around the last 6-8 hours
        if i >= num_records - 6:
            curr_rain = min(150.0, curr_rain + random.uniform(15.0, 30.0))
            curr_water = min(96.0, curr_water + random.uniform(6.0, 11.0))
            curr_temp = max(22.0, curr_temp - random.uniform(0.5, 1.2))
            curr_aqi = max(30.0, curr_aqi - random.uniform(2.0, 5.0))
        else:
            curr_rain = max(0.0, curr_rain + random.uniform(-4.0, 4.0))
            curr_water = max(15.0, min(50.0, curr_water + random.uniform(-2.0, 2.0)))
            curr_temp = max(20.0, min(38.0, curr_temp + random.uniform(-1.0, 1.2)))
            curr_aqi = max(25.0, min(140.0, curr_aqi + random.uniform(-5.0, 6.0)))

        res = evaluate_environmental_risk(
            rainfall=round(curr_rain, 1),
            water_level=round(curr_water, 1),
            temperature=round(curr_temp, 1),
            aqi=round(curr_aqi, 0),
            thresholds=DEFAULT_THRESHOLDS
        )

        record = {
            "timestamp": timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            "rainfall_mm": round(curr_rain, 1),
            "water_level_pct": round(curr_water, 1),
            "temperature_c": round(curr_temp, 1),
            "aqi": round(curr_aqi, 0),
            "risk_level": res["status"],
            "alert_message": res["alert_summary"],
            "detailed_explanation": res["alert_message"],
            "data_source": "Simulated Historical Sensor"
        }
        history.append(record)

    return history
