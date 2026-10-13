"""
Alert Engine for Disaster Early Warning System
----------------------------------------------
Implements rule-based threshold evaluation, input validation,
hazard classification (Flood, Heat, Air Quality), and risk categorization:
- NORMAL
- WARNING
- CRITICAL

Note: This is an academic simulation engine for cloud demonstration.
Thresholds are illustrative and not official meteorological limits.
"""

from dataclasses import dataclass
from typing import Dict, List, Tuple, Any


@dataclass
class ThresholdConfig:
    """Configurable thresholds for environmental hazard detection."""
    # Flood risk thresholds
    flood_rainfall_critical: float = 100.0  # mm
    flood_water_level_critical: float = 80.0  # %
    flood_rainfall_warning: float = 70.0    # mm
    flood_water_level_warning: float = 65.0   # %

    # Heat risk thresholds
    temp_critical: float = 42.0             # °C
    temp_warning: float = 38.0              # °C

    # Air Quality Index (AQI) thresholds
    aqi_critical: float = 200.0             # AQI index
    aqi_warning: float = 120.0              # AQI index


DEFAULT_THRESHOLDS = ThresholdConfig()


def validate_readings(rainfall: float, water_level: float, temperature: float, aqi: float) -> Tuple[bool, List[str]]:
    """
    Validates physical feasibility and sensor input bounds.
    Returns (is_valid, error_messages).
    """
    errors = []

    if rainfall < 0:
        errors.append("Rainfall cannot be negative.")
    elif rainfall > 1000:
        errors.append("Rainfall exceeds realistic meteorological upper limit (1000 mm).")

    if water_level < 0 or water_level > 100:
        errors.append("Water level must be a percentage between 0% and 100%.")

    if temperature < -50 or temperature > 65:
        errors.append("Temperature must be within plausible range (-50°C to 65°C).")

    if aqi < 0 or aqi > 500:
        errors.append("Air Quality Index (AQI) must be between 0 and 500.")

    return len(errors) == 0, errors


def evaluate_environmental_risk(
    rainfall: float,
    water_level: float,
    temperature: float,
    aqi: float,
    thresholds: ThresholdConfig = DEFAULT_THRESHOLDS
) -> Dict[str, Any]:
    """
    Evaluates sensor readings against configured thresholds.
    Determines hazard types and assigns overall risk status:
    NORMAL, WARNING, or CRITICAL.
    """
    hazards_detected: List[str] = []
    explanations: List[str] = []
    risk_rank = 0  # 0: NORMAL, 1: WARNING, 2: CRITICAL

    # 1. Flood Risk Detection (Multi-parameter: Rainfall + Water Level)
    if rainfall >= thresholds.flood_rainfall_critical and water_level >= thresholds.flood_water_level_critical:
        risk_rank = max(risk_rank, 2)
        hazards_detected.append("CRITICAL FLOOD RISK")
        explanations.append(
            f"Severe flood condition: Extreme rainfall ({rainfall:.1f} mm ≥ {thresholds.flood_rainfall_critical} mm) "
            f"coupled with dangerously high reservoir/river water level ({water_level:.1f}% ≥ {thresholds.flood_water_level_critical}%)."
        )
    elif rainfall >= thresholds.flood_rainfall_warning or water_level >= thresholds.flood_water_level_warning:
        risk_rank = max(risk_rank, 1)
        hazards_detected.append("FLOOD WARNING")
        reasons = []
        if rainfall >= thresholds.flood_rainfall_warning:
            reasons.append(f"Heavy rainfall ({rainfall:.1f} mm ≥ {thresholds.flood_rainfall_warning} mm)")
        if water_level >= thresholds.flood_water_level_warning:
            reasons.append(f"Elevated water level ({water_level:.1f}% ≥ {thresholds.flood_water_level_warning}%)")
        explanations.append("Moderate flood watch: " + " and ".join(reasons) + ".")

    # 2. Extreme Heat Risk Detection
    if temperature >= thresholds.temp_critical:
        risk_rank = max(risk_rank, 2)
        hazards_detected.append("EXTREME HEAT RISK")
        explanations.append(
            f"Severe heatwave condition: Ambient temperature ({temperature:.1f}°C ≥ {thresholds.temp_critical}°C) "
            f"exceeds critical human and infrastructure safety threshold."
        )
    elif temperature >= thresholds.temp_warning:
        risk_rank = max(risk_rank, 1)
        hazards_detected.append("HEAT WARNING")
        explanations.append(
            f"Elevated temperature warning: Ambient temperature ({temperature:.1f}°C ≥ {thresholds.temp_warning}°C)."
        )

    # 3. Air Quality Hazard Detection
    if aqi >= thresholds.aqi_critical:
        risk_rank = max(risk_rank, 2)
        hazards_detected.append("SEVERE AIR POLLUTION")
        explanations.append(
            f"Hazardous air quality alert: AQI ({aqi:.0f} ≥ {thresholds.aqi_critical}) "
            f"poses significant respiratory and environmental hazard."
        )
    elif aqi >= thresholds.aqi_warning:
        risk_rank = max(risk_rank, 1)
        hazards_detected.append("AIR QUALITY WARNING")
        explanations.append(
            f"Moderate air pollution alert: AQI ({aqi:.0f} ≥ {thresholds.aqi_warning})."
        )

    # Resolve overall risk status
    if risk_rank == 2:
        status = "CRITICAL"
        status_color = "#E53935"  # Bright Red
    elif risk_rank == 1:
        status = "WARNING"
        status_color = "#FB8C00"  # Amber / Orange
    else:
        status = "NORMAL"
        status_color = "#43A047"  # Green
        hazards_detected.append("SAFE PARAMETERS")
        explanations.append("All environmental readings are within acceptable, non-hazardous demonstration thresholds.")

    alert_summary = " | ".join(hazards_detected)
    detailed_message = " ".join(explanations)

    return {
        "status": status,
        "status_color": status_color,
        "risk_rank": risk_rank,
        "hazards": hazards_detected,
        "alert_summary": alert_summary,
        "alert_message": detailed_message,
        "parameters": {
            "rainfall_mm": rainfall,
            "water_level_pct": water_level,
            "temperature_c": temperature,
            "aqi": aqi
        }
    }
