"""
Disaster Early Warning and Emergency Alert System
=================================================
Academic Prototype for B.Tech Cloud Computing FT-III Assessment
Author: B.Tech Cloud Computing Student
Deployment Platform: Streamlit Community Cloud (Managed PaaS)
Containerization Capability: Dockerfile included for OCI-compliant hosting
Persistence: Local Memory & Session CSV (Ephemeral Demo Mode)
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
# 1. Page Configuration & Professional Theming
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Disaster Early Warning System | FT-III",
    layout="wide",
    initial_sidebar_state="expanded"
)
# Custom styling with dark navy, teal, green, amber, and red color scheme
st.markdown("""
<style>
    /* Global Typography and Headers */
    .app-header {
        background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
        color: #FFFFFF;
        padding: 20px 24px;
        border-radius: 10px;
        margin-bottom: 16px;
        border-left: 6px solid #0D9488;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    .app-header h1 {
        color: #F8FAFC;
        margin: 0 0 6px 0;
        font-size: 1.85rem;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    .app-header p {
        color: #94A3B8;
        margin: 0;
        font-size: 0.95rem;
    }
    /* Academic Notice Banner */
    .disclaimer-banner {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 12px 18px;
        border-radius: 8px;
        border: 1px solid #FCD34D;
        font-size: 0.88rem;
        line-height: 1.45;
        margin-bottom: 20px;
    }
    /* Distinct & Accessible Alert Panels */
    .alert-panel-critical {
        background-color: #FEE2E2;
        border: 2px solid #EF4444;
        border-left: 8px solid #DC2626;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 20px;
        color: #991B1B;
    }
    .alert-panel-warning {
        background-color: #FEF3C7;
        border: 2px solid #F59E0B;
        border-left: 8px solid #D97706;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 20px;
        color: #92400E;
    }
    .alert-panel-normal {
        background-color: #ECFDF5;
        border: 2px solid #10B981;
        border-left: 8px solid #059669;
        border-radius: 8px;
        padding: 16px 20px;
        margin-bottom: 20px;
        color: #065F46;
    }
    /* High-Contrast Dark Navy KPI Metric Cards */
    div[data-testid="stMetric"] {
        background-color: #1E293B !important;
        border: 1px solid #334155 !important;
        border-top: 3px solid #0D9488 !important;
        border-radius: 8px !important;
        padding: 14px 16px !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.25) !important;
    }
    div[data-testid="stMetricLabel"] {
        color: #CBD5E1 !important;
    }
    div[data-testid="stMetricLabel"] * {
        color: #CBD5E1 !important;
        font-weight: 600 !important;
        font-size: 0.88rem !important;
    }
    div[data-testid="stMetricValue"] {
        color: #FFFFFF !important;
    }
    div[data-testid="stMetricValue"] * {
        color: #FFFFFF !important;
        font-weight: 800 !important;
        font-size: 1.75rem !important;
        letter-spacing: -0.01em !important;
    }
    div[data-testid="stMetricDelta"] {
        font-size: 0.82rem !important;
        font-weight: 600 !important;
    }
    div[data-testid="stMetricDelta"] * {
        font-weight: 600 !important;
    }
    /* Plotly Chart Wrapper */
    div[data-testid="stPlotlyChart"] {
        background-color: #1E293B;
        border-radius: 10px;
        padding: 10px;
        border: 1px solid #334155;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.2);
    }
    /* Sidebar Section Accents */
    .sidebar-badge {
        display: inline-block;
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.75rem;
        font-weight: 600;
        background-color: #E2E8F0;
        color: #0F172A;
    }
</style>
""", unsafe_allow_html=True)
# -----------------------------------------------------------------------------
# 2. Session State Initialization
# -----------------------------------------------------------------------------
if "storage_manager" not in st.session_state:
    st.session_state.storage_manager = StorageManager()
# Pre-populate with realistic 18-record baseline history on first load
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
    st.markdown("### Simulation Controls")
    st.markdown("---")
    st.markdown("#### 1-Click Demonstration Scenarios")
    st.caption("Instantly load realistic hazard conditions for classroom/viva assessment:")
    selected_scenario = st.selectbox(
        "Select Scenario Preset:",
        options=list(DEMO_SCENARIOS.keys())
    )
    if st.button("Apply Scenario", use_container_width=True):
        scenario_data = DEMO_SCENARIOS[selected_scenario]
        st.session_state.current_values = {
            "rainfall": scenario_data["rainfall"],
            "water_level": scenario_data["water_level"],
            "temperature": scenario_data["temperature"],
            "aqi": scenario_data["aqi"],
            "source": scenario_data["source"]
        }
        st.toast(f"Loaded scenario: {selected_scenario}")
        st.rerun()
    st.markdown("---")
    st.markdown("#### Manual Sensor Input")
    st.caption("Enter simulated readings to test boundary conditions:")
    input_rainfall = st.number_input(
        "Rainfall (mm):",
        min_value=0.0,
        max_value=800.0,
        value=float(st.session_state.current_values["rainfall"]),
        step=5.0,
        help="Simulated precipitation depth over the watershed catchment area."
    )
    input_water_level = st.slider(
        "Reservoir / River Water Level (%):",
        min_value=0.0,
        max_value=100.0,
        value=float(st.session_state.current_values["water_level"]),
        step=1.0,
        help="Simulated reservoir capacity or river gauge saturation percentage."
    )
    input_temperature = st.number_input(
        "Ambient Temperature (°C):",
        min_value=-30.0,
        max_value=60.0,
        value=float(st.session_state.current_values["temperature"]),
        step=0.5,
        help="Simulated ambient air temperature in degrees Celsius."
    )
    input_aqi = st.number_input(
        "Air Quality Index (AQI):",
        min_value=0.0,
        max_value=500.0,
        value=float(st.session_state.current_values["aqi"]),
        step=5.0,
        help="Simulated Air Quality Index (0-500 standard scale)."
    )
    # Configurable Hazard Thresholds (Updates both Alert Engine and Plotly Charts)
    with st.expander("Configurable Hazard Thresholds", expanded=False):
        st.caption("Adjust limits to test dynamic evaluation and chart threshold lines:")
        st.markdown("**Critical Limits (Emergency):**")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            flood_rain_thresh = st.number_input("Crit Rain (mm)", value=100.0, step=5.0)
            heat_thresh = st.number_input("Crit Temp (°C)", value=42.0, step=1.0)
        with col_c2:
            flood_water_thresh = st.number_input("Crit Water (%)", value=80.0, step=5.0)
            aqi_thresh = st.number_input("Crit AQI", value=200.0, step=10.0)
        st.markdown("**Warning Limits (Watch):**")
        col_w1, col_w2 = st.columns(2)
        with col_w1:
            flood_rain_warn = st.number_input("Warn Rain (mm)", value=70.0, step=5.0)
            heat_warn = st.number_input("Warn Temp (°C)", value=38.0, step=1.0)
        with col_w2:
            flood_water_warn = st.number_input("Warn Water (%)", value=65.0, step=5.0)
            aqi_warn = st.number_input("Warn AQI", value=120.0, step=10.0)
        active_thresholds = ThresholdConfig(
            flood_rainfall_critical=float(flood_rain_thresh),
            flood_water_level_critical=float(flood_water_thresh),
            flood_rainfall_warning=float(flood_rain_warn),
            flood_water_level_warning=float(flood_water_warn),
            temp_critical=float(heat_thresh),
            temp_warning=float(heat_warn),
            aqi_critical=float(aqi_thresh),
            aqi_warning=float(aqi_warn)
        )
    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        submit_btn = st.button("Analyze & Log", type="primary", use_container_width=True)
    with col_btn2:
        reset_btn = st.button("Clear Logs", use_container_width=True)
    if reset_btn:
        st.session_state.storage_manager.clear_records()
        st.warning("Cleared historical monitoring records.")
        st.rerun()
    if st.button("Regenerate 24-Hr Time-Series", use_container_width=True):
        st.session_state.storage_manager.clear_records()
        st.session_state.storage_manager.load_bulk_records(generate_simulated_history(24))
        st.success("Loaded 24-hour simulation sequence.")
        st.rerun()
    st.markdown("---")
    # Cloud Architecture & Deployment Status Section (Strictly Accurate)
    st.markdown("#### Cloud Architecture Information")
    st.markdown("""
    - **Deployment Target:** Streamlit Community Cloud (Managed PaaS)
    - **Data Persistence:** Local Session & Memory (Ephemeral Demo Mode)
    - **Container Spec:** Dockerfile included (OCI-compliant capability)
    """)
    st.caption("Sensor streams are simulated. Storage is scoped to the current execution session.")
# -----------------------------------------------------------------------------
# 4. Input Processing & Rule-Based Analysis
# -----------------------------------------------------------------------------
# Update state values from manual inputs
st.session_state.current_values["rainfall"] = input_rainfall
st.session_state.current_values["water_level"] = input_water_level
st.session_state.current_values["temperature"] = input_temperature
st.session_state.current_values["aqi"] = input_aqi
# Measure local risk evaluation processing latency
t_start = time.perf_counter()
# Validate inputs
is_valid, validation_errors = validate_readings(
    input_rainfall, input_water_level, input_temperature, input_aqi
)
if not is_valid:
    for err in validation_errors:
        st.error(f"Input Validation Error: {err}")
    st.stop()
# Evaluate environmental risk using active configured thresholds
analysis_result = evaluate_environmental_risk(
    rainfall=input_rainfall,
    water_level=input_water_level,
    temperature=input_temperature,
    aqi=input_aqi,
    thresholds=active_thresholds
)
t_end = time.perf_counter()
processing_latency_ms = round((t_end - t_start) * 1000, 4)
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
    st.toast("Simulated reading logged successfully!")
# -----------------------------------------------------------------------------
# 5. Header & Academic Prototype Disclaimer
# -----------------------------------------------------------------------------
st.markdown("""
<div class="app-header">
    <h1>Disaster Early Warning System</h1>
    <p>Real-Time Environmental Hazard Monitoring & Emergency Alert Generation | B.Tech Cloud Computing FT-III</p>
</div>
""", unsafe_allow_html=True)
st.markdown("""
<div class="disclaimer-banner">
    <strong>ACADEMIC PROTOTYPE NOTICE:</strong> This application is developed for the&#x20;
    <strong>B.Tech Cloud Computing FT-III Assessment</strong>. All environmental metrics and sensor feeds are&#x20;
    <strong>simulated</strong> for demonstration of cloud concepts (PaaS hosting, container packaging capability,&#x20;
    rule-based evaluation, and data visualization). Historical records are session-specific and not stored in a&#x20;
    durable cloud database. Generated alerts are <strong>illustrative academic outputs</strong> and do not&#x20;
    constitute official meteorological or civil emergency warnings.
</div>
""", unsafe_allow_html=True)
# -----------------------------------------------------------------------------
# 6. Current Risk Status Banner & Root Cause Explanation Panel
# -----------------------------------------------------------------------------
risk_status = analysis_result["status"]
if risk_status == "CRITICAL":
    st.markdown(f"""
    <div class="alert-panel-critical">
        <h3 style="margin-top:0; color:#991B1B;">RISK STATUS: CRITICAL EMERGENCY</h3>
        <p><strong>Triggered Hazards:</strong> {analysis_result['alert_summary']}</p>
        <p style="margin-bottom:0;"><strong>Root Cause Analysis:</strong> {analysis_result['alert_message']}</p>
    </div>
    """, unsafe_allow_html=True)
elif risk_status == "WARNING":
    st.markdown(f"""
    <div class="alert-panel-warning">
        <h3 style="margin-top:0; color:#92400E;">RISK STATUS: WARNING WATCH</h3>
        <p><strong>Triggered Anomalies:</strong> {analysis_result['alert_summary']}</p>
        <p style="margin-bottom:0;"><strong>Root Cause Analysis:</strong> {analysis_result['alert_message']}</p>
    </div>
    """, unsafe_allow_html=True)
else:
    st.markdown(f"""
    <div class="alert-panel-normal">
        <h3 style="margin-top:0; color:#065F46;">RISK STATUS: NORMAL (SAFE)</h3>
        <p><strong>Status Summary:</strong> {analysis_result['alert_summary']}</p>
        <p style="margin-bottom:0;"><strong>Root Cause Analysis:</strong> {analysis_result['alert_message']}</p>
    </div>
    """, unsafe_allow_html=True)
# -----------------------------------------------------------------------------
# 7. Summary Cards / Metric KPIs (Using Active Configurable Thresholds)
# -----------------------------------------------------------------------------
df_history = st.session_state.storage_manager.get_dataframe()
total_alerts = len(df_history[df_history["risk_level"].isin(["WARNING", "CRITICAL"])]) if not df_history.empty else 0
total_records = len(df_history)
col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
with col_m1:
    rain_delta = (
        f"Crit ≥ {active_thresholds.flood_rainfall_critical:.0f} mm"
        if input_rainfall >= active_thresholds.flood_rainfall_critical
        else (
            f"Watch ≥ {active_thresholds.flood_rainfall_warning:.0f} mm"
            if input_rainfall >= active_thresholds.flood_rainfall_warning
            else "Safe"
        )
    )
    st.metric(
        label="Rainfall",
        value=f"{input_rainfall:.1f} mm",
        delta=rain_delta,
        delta_color="inverse" if input_rainfall >= active_thresholds.flood_rainfall_warning else "normal"
    )
with col_m2:
    water_delta = (
        f"Crit ≥ {active_thresholds.flood_water_level_critical:.0f}%"
        if input_water_level >= active_thresholds.flood_water_level_critical
        else (
            f"Watch ≥ {active_thresholds.flood_water_level_warning:.0f}%"
            if input_water_level >= active_thresholds.flood_water_level_warning
            else "Safe"
        )
    )
    st.metric(
        label="Water Level",
        value=f"{input_water_level:.1f} %",
        delta=water_delta,
        delta_color="inverse" if input_water_level >= active_thresholds.flood_water_level_warning else "normal"
    )
with col_m3:
    temp_delta = (
        f"Crit ≥ {active_thresholds.temp_critical:.0f}°C"
        if input_temperature >= active_thresholds.temp_critical
        else (
            f"Watch ≥ {active_thresholds.temp_warning:.0f}°C"
            if input_temperature >= active_thresholds.temp_warning
            else "Safe"
        )
    )
    st.metric(
        label="Temperature",
        value=f"{input_temperature:.1f} °C",
        delta=temp_delta,
        delta_color="inverse" if input_temperature >= active_thresholds.temp_warning else "normal"
    )
with col_m4:
    aqi_delta = (
        f"Crit ≥ {active_thresholds.aqi_critical:.0f}"
        if input_aqi >= active_thresholds.aqi_critical
        else (
            f"Watch ≥ {active_thresholds.aqi_warning:.0f}"
            if input_aqi >= active_thresholds.aqi_warning
            else "Safe"
        )
    )
    st.metric(
        label="Air Quality Index",
        value=f"{input_aqi:.0f} AQI",
        delta=aqi_delta,
        delta_color="inverse" if input_aqi >= active_thresholds.aqi_warning else "normal"
    )
with col_m5:
    st.metric(
        label="Local Evaluation Latency",
        value=f"{processing_latency_ms} ms",
        delta=f"Alerts: {total_alerts}/{total_records}",
        delta_color="off",
        help="Measures local in-process Python algorithm risk evaluation execution time on this host. Does NOT represent total network/cloud round-trip latency."
    )
# -----------------------------------------------------------------------------
# 8. Interactive Plotly Charts (Multi-Parameter Trend with Dynamic Thresholds)
# -----------------------------------------------------------------------------
st.markdown("### Environmental Monitoring Trends")
st.caption(
    "Dashed red lines indicate active **Critical Thresholds**; dotted amber lines indicate active **Warning Thresholds**. "
    "Threshold lines update automatically when settings change in the sidebar."
)
if not df_history.empty:
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            "Rainfall (mm)",
            "Reservoir Water Level (%)",
            "Temperature (°C)",
            "Air Quality Index (AQI)"
        ),
        vertical_spacing=0.22,
        horizontal_spacing=0.09
    )
    timestamps = pd.to_datetime(df_history["timestamp"])
    # 1. Rainfall Plot
    fig.add_trace(
        go.Scatter(
            x=timestamps, y=df_history["rainfall_mm"], name="Rainfall (mm)",
            line=dict(color="#38BDF8", width=2.5),
            marker=dict(size=4, color="#38BDF8"),
            mode="lines+markers"
        ),
        row=1, col=1
    )
    fig.add_hline(
        y=active_thresholds.flood_rainfall_critical, line_dash="dash", line_color="#EF4444", line_width=1.8,
        annotation_text=f"Critical: {active_thresholds.flood_rainfall_critical:.0f} mm",
        annotation_position="top left",
        annotation_font=dict(color="#FCA5A5", size=10, family="sans-serif"),
        annotation_bgcolor="rgba(15, 23, 42, 0.85)",
        annotation_bordercolor="#EF4444",
        annotation_borderwidth=1,
        annotation_borderpad=3,
        row=1, col=1
    )
    fig.add_hline(
        y=active_thresholds.flood_rainfall_warning, line_dash="dot", line_color="#F59E0B", line_width=1.8,
        annotation_text=f"Watch: {active_thresholds.flood_rainfall_warning:.0f} mm",
        annotation_position="bottom right",
        annotation_font=dict(color="#FDE68A", size=10, family="sans-serif"),
        annotation_bgcolor="rgba(15, 23, 42, 0.85)",
        annotation_bordercolor="#F59E0B",
        annotation_borderwidth=1,
        annotation_borderpad=3,
        row=1, col=1
    )
    # 2. Water Level Plot
    fig.add_trace(
        go.Scatter(
            x=timestamps, y=df_history["water_level_pct"], name="Water Level (%)",
            line=dict(color="#2DD4BF", width=2.5),
            marker=dict(size=4, color="#2DD4BF"),
            mode="lines+markers"
        ),
        row=1, col=2
    )
    fig.add_hline(
        y=active_thresholds.flood_water_level_critical, line_dash="dash", line_color="#EF4444", line_width=1.8,
        annotation_text=f"Critical: {active_thresholds.flood_water_level_critical:.0f}%",
        annotation_position="top left",
        annotation_font=dict(color="#FCA5A5", size=10, family="sans-serif"),
        annotation_bgcolor="rgba(15, 23, 42, 0.85)",
        annotation_bordercolor="#EF4444",
        annotation_borderwidth=1,
        annotation_borderpad=3,
        row=1, col=2
    )
    fig.add_hline(
        y=active_thresholds.flood_water_level_warning, line_dash="dot", line_color="#F59E0B", line_width=1.8,
        annotation_text=f"Watch: {active_thresholds.flood_water_level_warning:.0f}%",
        annotation_position="bottom right",
        annotation_font=dict(color="#FDE68A", size=10, family="sans-serif"),
        annotation_bgcolor="rgba(15, 23, 42, 0.85)",
        annotation_bordercolor="#F59E0B",
        annotation_borderwidth=1,
        annotation_borderpad=3,
        row=1, col=2
    )
    # 3. Temperature Plot
    fig.add_trace(
        go.Scatter(
            x=timestamps, y=df_history["temperature_c"], name="Temperature (°C)",
            line=dict(color="#FB923C", width=2.5),
            marker=dict(size=4, color="#FB923C"),
            mode="lines+markers"
        ),
        row=2, col=1
    )
    fig.add_hline(
        y=active_thresholds.temp_critical, line_dash="dash", line_color="#EF4444", line_width=1.8,
        annotation_text=f"Critical: {active_thresholds.temp_critical:.0f}°C",
        annotation_position="top left",
        annotation_font=dict(color="#FCA5A5", size=10, family="sans-serif"),
        annotation_bgcolor="rgba(15, 23, 42, 0.85)",
        annotation_bordercolor="#EF4444",
        annotation_borderwidth=1,
        annotation_borderpad=3,
        row=2, col=1
    )
    fig.add_hline(
        y=active_thresholds.temp_warning, line_dash="dot", line_color="#F59E0B", line_width=1.8,
        annotation_text=f"Watch: {active_thresholds.temp_warning:.0f}°C",
        annotation_position="bottom right",
        annotation_font=dict(color="#FDE68A", size=10, family="sans-serif"),
        annotation_bgcolor="rgba(15, 23, 42, 0.85)",
        annotation_bordercolor="#F59E0B",
        annotation_borderwidth=1,
        annotation_borderpad=3,
        row=2, col=1
    )
    # 4. AQI Plot
    fig.add_trace(
        go.Scatter(
            x=timestamps, y=df_history["aqi"], name="AQI",
            line=dict(color="#C084FC", width=2.5),
            marker=dict(size=4, color="#C084FC"),
            mode="lines+markers"
        ),
        row=2, col=2
    )
    fig.add_hline(
        y=active_thresholds.aqi_critical, line_dash="dash", line_color="#EF4444", line_width=1.8,
        annotation_text=f"Critical: {active_thresholds.aqi_critical:.0f}",
        annotation_position="top left",
        annotation_font=dict(color="#FCA5A5", size=10, family="sans-serif"),
        annotation_bgcolor="rgba(15, 23, 42, 0.85)",
        annotation_bordercolor="#EF4444",
        annotation_borderwidth=1,
        annotation_borderpad=3,
        row=2, col=2
    )
    fig.add_hline(
        y=active_thresholds.aqi_warning, line_dash="dot", line_color="#F59E0B", line_width=1.8,
        annotation_text=f"Watch: {active_thresholds.aqi_warning:.0f}",
        annotation_position="bottom right",
        annotation_font=dict(color="#FDE68A", size=10, family="sans-serif"),
        annotation_bgcolor="rgba(15, 23, 42, 0.85)",
        annotation_bordercolor="#F59E0B",
        annotation_borderwidth=1,
        annotation_borderpad=3,
        row=2, col=2
    )
    fig.update_layout(
        height=580,
        margin=dict(l=45, r=35, t=50, b=35),
        showlegend=False,
        hovermode="x unified",
        paper_bgcolor="#1E293B",
        plot_bgcolor="#0F172A",
        font=dict(color="#F1F5F9", family="sans-serif")
    )
    # Style subplot title font color for high contrast
    fig.for_each_annotation(
        lambda a: a.update(font=dict(color="#F1F5F9", size=12, family="sans-serif"))
        if a.text and a.text in [
            "Rainfall (mm)",
            "Reservoir Water Level (%)",
            "Temperature (°C)",
            "Air Quality Index (AQI)"
        ]
        else None
    )
    fig.update_xaxes(
        showgrid=True, gridwidth=1, gridcolor="#334155",
        color="#94A3B8", tickfont=dict(color="#94A3B8", size=10),
        zeroline=False
    )
    fig.update_yaxes(
        showgrid=True, gridwidth=1, gridcolor="#334155",
        color="#94A3B8", tickfont=dict(color="#94A3B8", size=10),
        zeroline=False
    )
    st.plotly_chart(fig, use_container_width=True)
else:
    st.info("No historical readings recorded yet. Use 'Regenerate 24-Hr Time-Series' or 'Analyze & Log' in the sidebar.")
# -----------------------------------------------------------------------------
# 9. Historical Records Table & CSV Export
# -----------------------------------------------------------------------------
st.markdown("### Historical Monitoring Log")
if not df_history.empty:
    col_t1, col_t2 = st.columns([3, 1])
    with col_t1:
        st.caption(f"Displaying {len(df_history)} session records (stored in local ephemeral memory).")
    with col_t2:
        csv_bytes = st.session_state.storage_manager.export_csv_bytes()
        st.download_button(
            label="Export Monitoring Data (CSV)",
            data=csv_bytes,
            file_name="disaster_monitoring_records.csv",
            mime="text/csv",
            use_container_width=True
        )
    # Display styled table with most recent entries on top
    display_df = df_history.iloc[::-1].copy()
    def style_risk(val):
        if val == "CRITICAL":
            return "background-color: #FEE2E2; color: #991B1B; font-weight: bold;"
        elif val == "WARNING":
            return "background-color: #FEF3C7; color: #92400E; font-weight: bold;"
        return "background-color: #ECFDF5; color: #065F46;"
    # Compatible styling for both pandas 2.x and pandas 3.x
    if hasattr(display_df.style, "map"):
        styled_table = display_df.style.map(style_risk, subset=["risk_level"])
    else:
        styled_table = display_df.style.applymap(style_risk, subset=["risk_level"])
    st.dataframe(styled_table, use_container_width=True, height=280)
else:
    st.markdown("""
    *No records available.*
    - Click **Apply Scenario** in the sidebar to populate demonstration data.
    - Or enter values manually and click **Analyze & Log**.
    """)
# -----------------------------------------------------------------------------
# 10. Cloud Computing Syllabus Mapping (FT-III Academic Assessment Notes)
# -----------------------------------------------------------------------------
with st.expander("Cloud Computing Syllabus & Architecture Reference (FT-III Alignment)"):
    st.markdown("""
    #### Unit 1: Fundamentals of Cloud Computing
    - **Current Deployment Model:** Deployed on **Streamlit Community Cloud**, a managed Platform-as-a-Service (PaaS) that runs the application from the GitHub repository with continuous integration.
    - **TCO & CAPEX vs OPEX:** Using cloud PaaS eliminates hardware capital expenditure (CAPEX). Streamlit Community Cloud provides a zero-cost operational expenditure (OPEX) model suitable for academic prototypes.
    - **SLA Realities:** Streamlit Community Cloud is a developer community tier without a financially-backed uptime SLA. Commercial enterprise cloud platforms (e.g. Google Cloud Run or AWS ECS) offer formal 99.95% monthly uptime SLAs.
    #### Unit 2: Cloud Architecture & Services
    - **PaaS (Current Deployment):** Streamlit Community Cloud manages the runtime platform, build pipeline, and SSL/TLS HTTPS certificate lifecycle.
    - **IaaS (Theoretical Comparison):** Infrastructure-as-a-Service (such as Google Compute Engine or AWS EC2) would provide raw virtual machines where OS patching, web server setup, and firewall maintenance are user-managed.
    - **CaaS / Container Capability:** The project includes a production `Dockerfile`, demonstrating portable packaging that can be deployed to container platforms like Google Cloud Run or Kubernetes if desired.
    - **Managed Database (Theoretical Comparison):** Persistent cloud databases (such as Google Cloud Firestore or Amazon DynamoDB) provide durable multi-user storage. For this assessment prototype, data is retained in ephemeral local memory/CSV mode to ensure zero credential requirements.
    - **SaaS (User View):** The disaster early warning web dashboard accessed over HTTPS in client browsers.
    #### Unit 3: Cloud Security
    - **Transport Layer Security:** Automated end-to-end HTTPS encryption provided by the hosting platform.
    - **Zero Secrets in Codebase:** No hardcoded API keys, database credentials, or private keys.
    - **Input Sanitization:** Strict bounds and type validation protect the alert engine from malformed or out-of-range sensor payloads.
    - **Access Control:** Direct, unauthenticated public access appropriate for an open academic prototype (no fake or insecure authentication).
    #### Unit 4: Virtualization & Capacity Planning
    - **Containerization Capability:** Packaged as an OCI-compliant container using `python:3.11-slim` with a Python standard-library healthcheck. Demonstrates OS-level virtualization sharing host kernel resources rather than running heavyweight virtual machine hypervisors.
    - **Capacity & Scaling Realities:** Streamlit Community Cloud allocates isolated container resources with sleep-on-idle capability to conserve shared cloud resources.
    #### Unit 5: Cloud Computing Applications
    - Cloud web services deployment, automated Git push-to-deploy pipelines, real-time data handling with Pandas, and interactive analytics visualization with Plotly.
    """)
