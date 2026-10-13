"""
Disaster Early Warning and Emergency Alert System
=================================================
Academic Prototype for B.Tech Cloud Computing FT-III Assessment

Author: B.Tech Cloud Computing Student
Deployment Platform: Google Cloud Run (Containerized PaaS)
Persistence: Local Memory / CSV (Default Demo) & Google Cloud Firestore (Optional)
"""

import time
import os
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from alert_engine import (
    evaluate_environmental_risk,
    validate_readings,
    ThresholdConfig,
    DEFAULT_THRESHOLDS
)
from sample_data import DEMO_SCENARIOS, generate_simulated_history
from storage_manager import StorageManager

# -----------------------------------------------------------------------------
# 1. Page Configuration & Custom Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Disaster Early Warning System",
    page_icon="🚨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for crisp cards, responsive layout, and distinct status badges
st.markdown("""
<style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 16px;
        border-left: 5px solid #1E88E5;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        margin-bottom: 12px;
    }
    .status-badge-critical {
        background-color: #ffebee;
        color: #c62828;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        border: 1px solid #ef9a9a;
        display: inline-block;
    }
    .status-badge-warning {
        background-color: #fff8e1;
        color: #e65100;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        border: 1px solid #ffe082;
        display: inline-block;
    }
    .status-badge-normal {
        background-color: #e8f5e9;
        color: #2e7d32;
        padding: 6px 14px;
        border-radius: 20px;
        font-weight: 700;
        border: 1px solid #a5d6a7;
        display: inline-block;
    }
    .disclaimer-banner {
        background-color: #fff3cd;
        color: #856404;
        padding: 10px 16px;
        border-radius: 6px;
        border: 1px solid #ffeeba;
        font-size: 0.9rem;
        margin-bottom: 15px;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. Session State Initialization
# -----------------------------------------------------------------------------
if "storage_manager" not in st.session_state:
    st.session_state.storage_manager = StorageManager()

# Pre-populate with realistic 24-hour baseline history on first load
if "initialized_history" not in st.session_state:
    initial_records = generate_simulated_history(num_records=18)
    st.session_state.storage_manager.load_bulk_records(initial_records)
    st.session_state.initialized_history = True

# Store current sensor values in session state for cross-component reactivity
if "current_values" not in st.session_state:
    st.session_state.current_values = {
        "rainfall": 15.0,
        "water_level": 30.0,
        "temperature": 28.0,
        "aqi": 50.0,
        "source": "Initial Simulated Baseline"
    }

# -----------------------------------------------------------------------------
# 3. Sidebar Controls & Simulation Panel
# -----------------------------------------------------------------------------
with st.sidebar:
    st.header("🎛️ Simulation Controls")

    st.markdown("---")
    st.subheader("1-Click Demonstration Scenarios")
    st.caption("Instantly load realistic disaster or normal scenarios for viva evaluation:")

    selected_scenario = st.selectbox(
        "Choose Pre-configured Scenario:",
        options=list(DEMO_SCENARIOS.keys())
    )

    if st.button("📥 Apply Scenario", use_container_width=True):
        scenario_data = DEMO_SCENARIOS[selected_scenario]
        st.session_state.current_values = {
            "rainfall": scenario_data["rainfall"],
            "water_level": scenario_data["water_level"],
            "temperature": scenario_data["temperature"],
            "aqi": scenario_data["aqi"],
            "source": scenario_data["source"]
        }
        st.success(f"Loaded: {selected_scenario}")
        st.rerun()

    st.markdown("---")
    st.subheader("Manual Sensor Input")
    st.caption("Adjust simulated sensor readings to test custom boundary limits:")

    input_rainfall = st.number_input(
        "Rainfall (mm):",
        min_value=0.0,
        max_value=800.0,
        value=float(st.session_state.current_values["rainfall"]),
        step=5.0,
        help="Simulated precipitation depth over the monitoring area."
    )

    input_water_level = st.slider(
        "Reservoir / River Water Level (%):",
        min_value=0.0,
        max_value=100.0,
        value=float(st.session_state.current_values["water_level"]),
        step=1.0,
        help="Simulated reservoir capacity or river gauge percentage."
    )

    input_temperature = st.number_input(
        "Ambient Temperature (°C):",
        min_value=-30.0,
        max_value=60.0,
        value=float(st.session_state.current_values["temperature"]),
        step=0.5,
        help="Simulated ambient air temperature."
    )

    input_aqi = st.number_input(
        "Air Quality Index (AQI):",
        min_value=0.0,
        max_value=500.0,
        value=float(st.session_state.current_values["aqi"]),
        step=5.0,
        help="Simulated Air Quality Index (0-500 scale)."
    )

    # Threshold configuration expander for viva demonstrations
    with st.expander("⚙️ Configurable Hazard Thresholds"):
        st.caption("Academic threshold limits for hazard triggers:")
        flood_rain_thresh = st.number_input("Crit Flood Rain (mm)", value=100.0, step=5.0)
        flood_water_thresh = st.number_input("Crit Water Level (%)", value=80.0, step=5.0)
        heat_thresh = st.number_input("Crit Heat Temp (°C)", value=42.0, step=1.0)
        aqi_thresh = st.number_input("Crit AQI Limit", value=200.0, step=10.0)

        custom_thresholds = ThresholdConfig(
            flood_rainfall_critical=flood_rain_thresh,
            flood_water_level_critical=flood_water_thresh,
            temp_critical=heat_thresh,
            aqi_critical=aqi_thresh
        )

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        submit_btn = st.button("🚀 Analyze & Log", type="primary", use_container_width=True)
    with col_btn2:
        reset_btn = st.button("🧹 Clear Logs", use_container_width=True)

    if reset_btn:
        st.session_state.storage_manager.clear_records()
        st.warning("Cleared historical monitoring records.")
        st.rerun()

    if st.button("🔄 Reload 24-Hr Time-Series", use_container_width=True):
        st.session_state.storage_manager.clear_records()
        st.session_state.storage_manager.load_bulk_records(generate_simulated_history(24))
        st.success("Loaded 24-hour simulation sequence.")
        st.rerun()

    st.markdown("---")
    # Cloud Architecture & Storage Backend Indicator
    storage_info = st.session_state.storage_manager.get_status_info()
    st.subheader("☁️ Cloud Architecture Info")
    st.info(f"**Storage Mode:** {storage_info['backend_description']}")
    st.caption("Google Cloud Run (PaaS Container) | Streamlit Web Engine")

# -----------------------------------------------------------------------------
# 4. Input Processing & Rule-Based Analysis
# -----------------------------------------------------------------------------
# Update state values from manual inputs
st.session_state.current_values["rainfall"] = input_rainfall
st.session_state.current_values["water_level"] = input_water_level
st.session_state.current_values["temperature"] = input_temperature
st.session_state.current_values["aqi"] = input_aqi

# Measure response time for performance assessment (latency tracking)
t_start = time.perf_counter()

# Validate inputs
is_valid, validation_errors = validate_readings(
    input_rainfall, input_water_level, input_temperature, input_aqi
)

if not is_valid:
    for err in validation_errors:
        st.error(f"Input Validation Error: {err}")
    st.stop()

# Evaluate risk
active_thresholds = custom_thresholds if 'custom_thresholds' in locals() else DEFAULT_THRESHOLDS
analysis_result = evaluate_environmental_risk(
    rainfall=input_rainfall,
    water_level=input_water_level,
    temperature=input_temperature,
    aqi=input_aqi,
    thresholds=active_thresholds
)

t_end = time.perf_counter()
processing_latency_ms = round((t_end - t_start) * 1000, 2)

# If user clicked "Analyze & Log", persist the reading
if submit_btn:
    new_record = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "rainfall_mm": input_rainfall,
        "water_level_pct": input_water_level,
        "temperature_c": input_temperature,
        "aqi": input_aqi,
        "risk_level": analysis_result["status"],
        "alert_message": analysis_result["alert_summary"],
        "detailed_explanation": analysis_result["alert_message"],
        "data_source": "Simulated Sensor Reading"
    }
    st.session_state.storage_manager.save_record(new_record)
    st.toast("Reading logged successfully!", icon="✅")

# -----------------------------------------------------------------------------
# 5. Header & Academic Prototype Disclaimer
# -----------------------------------------------------------------------------
st.title("🚨 Disaster Early Warning System")

st.markdown("""
<div class="disclaimer-banner">
    <strong>⚠️ ACADEMIC PROTOTYPE NOTICE:</strong> This system is developed for the 
    <strong>B.Tech Cloud Computing FT-III Assessment</strong>. All data points are 
    <strong>simulated</strong> for demonstration of cloud concepts (PaaS, containerization, 
    monitoring, and alerting). These generated warnings are <strong>not official emergency alerts</strong>.
</div>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 6. Current Risk Status Banner & Detailed Explanation Panel
# -----------------------------------------------------------------------------
risk_status = analysis_result["status"]
if risk_status == "CRITICAL":
    st.error(f"""
    ### 🔴 RISK STATUS: CRITICAL EMERGENCY
    **Detected Hazards:** {analysis_result['alert_summary']}
    
    **Root Cause Analysis:** {analysis_result['alert_message']}
    """)
elif risk_status == "WARNING":
    st.warning(f"""
    ### 🟠 RISK STATUS: WARNING WATCH
    **Detected Anomalies:** {analysis_result['alert_summary']}
    
    **Root Cause Analysis:** {analysis_result['alert_message']}
    """)
else:
    st.success(f"""
    ### 🟢 RISK STATUS: NORMAL (SAFE)
    **All Parameters Safe:** {analysis_result['alert_summary']}
    
    **Analysis:** {analysis_result['alert_message']}
    """)

# -----------------------------------------------------------------------------
# 7. Summary Cards / Metric KPIs
# -----------------------------------------------------------------------------
df_history = st.session_state.storage_manager.get_dataframe()
total_alerts = len(df_history[df_history["risk_level"].isin(["WARNING", "CRITICAL"])]) if not df_history.empty else 0
total_records = len(df_history)

col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)

with col_m1:
    st.metric(
        label="🌧️ Rainfall",
        value=f"{input_rainfall:.1f} mm",
        delta="Flood watch > 70 mm" if input_rainfall >= 70 else None,
        delta_color="inverse"
    )

with col_m2:
    st.metric(
        label="🌊 Water Level",
        value=f"{input_water_level:.1f} %",
        delta="Overflow risk > 80%" if input_water_level >= 80 else None,
        delta_color="inverse"
    )

with col_m3:
    st.metric(
        label="🌡️ Temperature",
        value=f"{input_temperature:.1f} °C",
        delta="Heatwave > 42°C" if input_temperature >= 42 else None,
        delta_color="inverse"
    )

with col_m4:
    st.metric(
        label="💨 Air Quality Index",
        value=f"{input_aqi:.0f} AQI",
        delta="Unhealthy > 120" if input_aqi >= 120 else None,
        delta_color="inverse"
    )

with col_m5:
    st.metric(
        label="📊 Logged Alerts",
        value=f"{total_alerts} / {total_records}",
        delta=f"Latency: {processing_latency_ms} ms",
        delta_color="off"
    )

# -----------------------------------------------------------------------------
# 8. Interactive Plotly Charts (Multi-Parameter Trend)
# -----------------------------------------------------------------------------
st.markdown("### 📈 Environmental Monitoring Trends")

if not df_history.empty:
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "🌧️ Rainfall (mm) & Threshold",
            "🌊 Reservoir Water Level (%) & Threshold",
            "🌡️ Temperature (°C) & Heat Limit",
            "💨 Air Quality Index (AQI) & Safety Limit"
        ),
        vertical_spacing=0.15,
        horizontal_spacing=0.08
    )

    timestamps = pd.to_datetime(df_history["timestamp"])

    # 1. Rainfall Plot
    fig.add_trace(
        go.Scatter(x=timestamps, y=df_history["rainfall_mm"], name="Rainfall (mm)",
                   line=dict(color="#1976D2", width=2.5), mode="lines+markers"),
        row=1, col=1
    )
    fig.add_hline(y=100.0, line_dash="dash", line_color="red",
                  annotation_text="Critical (100mm)", row=1, col=1)

    # 2. Water Level Plot
    fig.add_trace(
        go.Scatter(x=timestamps, y=df_history["water_level_pct"], name="Water Level (%)",
                   line=dict(color="#0097A7", width=2.5), mode="lines+markers"),
        row=1, col=2
    )
    fig.add_hline(y=80.0, line_dash="dash", line_color="red",
                  annotation_text="Critical (80%)", row=1, col=2)

    # 3. Temperature Plot
    fig.add_trace(
        go.Scatter(x=timestamps, y=df_history["temperature_c"], name="Temperature (°C)",
                   line=dict(color="#E64A19", width=2.5), mode="lines+markers"),
        row=2, col=1
    )
    fig.add_hline(y=42.0, line_dash="dash", line_color="red",
                  annotation_text="Heatwave (42°C)", row=2, col=1)

    # 4. AQI Plot
    fig.add_trace(
        go.Scatter(x=timestamps, y=df_history["aqi"], name="AQI",
                   line=dict(color="#7B1FA2", width=2.5), mode="lines+markers"),
        row=2, col=2
    )
    fig.add_hline(y=200.0, line_dash="dash", line_color="red",
                  annotation_text="Hazardous (200 AQI)", row=2, col=2)

    fig.update_layout(
        height=480,
        margin=dict(l=20, r=20, t=40, b=20),
        showlegend=False,
        hovermode="x unified"
    )

    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No historical readings recorded yet. Use 'Reload 24-Hr Time-Series' or 'Analyze & Log' in the sidebar.")

# -----------------------------------------------------------------------------
# 9. Historical Records Table & CSV Export
# -----------------------------------------------------------------------------
st.markdown("### 📋 Historical Monitoring Log")

if not df_history.empty:
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.caption(f"Displaying {len(df_history)} monitoring records recorded during this session.")
    with col_t2:
        csv_bytes = st.session_state.storage_manager.export_csv_bytes()
        st.download_button(
            label="📥 Export Monitoring Data (CSV)",
            data=csv_bytes,
            file_name="disaster_monitoring_records.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Display styled table with most recent entries on top
    display_df = df_history.iloc[::-1].copy()

    def style_risk(val):
        if val == "CRITICAL":
            return "background-color: #ffcdd2; color: #b71c1c; font-weight: bold;"
        elif val == "WARNING":
            return "background-color: #ffe0b2; color: #e65100; font-weight: bold;"
        return "background-color: #c8e6c9; color: #1b5e20;"

    # Compatible styling for both pandas 2.x and pandas 3.x
    if hasattr(display_df.style, "map"):
        styled_table = display_df.style.map(style_risk, subset=["risk_level"])
    else:
        styled_table = display_df.style.applymap(style_risk, subset=["risk_level"])
    st.dataframe(styled_table, use_container_width=True, height=280)
else:
    st.markdown("""
    *No records available.*
    - Click **📥 Apply Scenario** in the sidebar to populate demonstration data.
    - Or enter values manually and click **🚀 Analyze & Log**.
    """)

# -----------------------------------------------------------------------------
# 10. Cloud Computing Syllabus Mapping (FT-III Academic Assessment Notes)
# -----------------------------------------------------------------------------
with st.expander("📚 Cloud Computing Syllabus & Architecture Reference (FT-III Alignment)"):
    st.markdown("""
    #### Unit 1: Fundamentals of Cloud Computing
    - **Cloud Characteristics Demonstrated:** On-demand self-service, broad network access, measured service (latency tracking & records counting), rapid elasticity (Cloud Run scaling).
    - **TCO & CAPEX vs OPEX:** Deploying on Google Cloud Run eliminates server CAPEX (no hardware purchase). Pay-per-use OPEX model where idle applications incur zero compute cost.
    - **Service Level Agreements (SLA):** Cloud Run provides a 99.95% monthly uptime SLA.

    #### Unit 2: Cloud Architecture & Services
    - **IaaS:** Google Compute Engine represents IaaS (virtual machines where OS and runtime must be managed).
    - **PaaS (Current Deployment):** Google Cloud Run is a managed serverless PaaS/CaaS platform handling container execution, scaling, health checks, and OS maintenance.
    - **SaaS:** The web dashboard accessed over HTTPS acts as the end-user software interface.
    - **Database:** Google Cloud Firestore is a managed NoSQL document database.

    #### Unit 3: Cloud Security
    - **Least Privilege IAM:** Cloud Run runs with a dedicated service account containing minimal permissions.
    - **Encrypted Transport:** Enforced HTTPS with managed TLS certificates at the Cloud Run load balancer.
    - **Zero Hardcoded Secrets:** Configuration and optional cloud credentials rely on environment variables (`GCP_PROJECT_ID`).

    #### Unit 4: Virtualization & Capacity Planning
    - **Containerization vs Virtualization:** The application is packaged as an OCI Docker container (sharing host kernel) rather than a full VM with hypervisor overhead.
    - **Capacity Planning:** Autoscaling configured from 0 to N instances based on concurrent HTTP requests. Zero instances when idle saves cloud credits.

    #### Unit 5: Cloud Computing Applications
    - Google Cloud Run web application deployment, Google Cloud Storage / Firestore integration, and automated container health management.
    """)
