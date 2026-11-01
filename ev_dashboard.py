import streamlit as st
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# ==========================================
# PAGE CONFIGURATION & UI SETUP
# ==========================================
st.set_page_config(
    page_title="In-Silico EV Charging Simulator",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for the "Enterprise SaaS" look
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    h1 { color: #003366; font-family: 'Helvetica Neue', sans-serif; }
    h2, h3 { color: #004080; }
    .stSlider > div > div > div > div { background-color: #003366; }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# MAIN DASHBOARD HEADER
# ==========================================
st.title("⚡ Dynamic Wireless EV Charging Simulator")
st.markdown("""
**Infrastructural Engineering Dashboard (Electrified Highways)**
Adjust the physical and electrical parameters in the sidebar to simulate a real-time coil pass and calculate the kinetic energy transfer efficiency using Faraday's Law.
""")
st.divider()

# ==========================================
# SIDEBAR PARAMETERS (The Variables)
# ==========================================
st.sidebar.header("⚙️ Simulation Parameters")

# 1. Kinematic Variables
st.sidebar.subheader("Kinematics")
v_kmh = st.sidebar.slider("Vehicle Velocity (km/h)", min_value=10.0, max_value=120.0, value=60.0, step=5.0)
v_ms = v_kmh / 3.6  # Convert to m/s

# 2. Spatial Variables
st.sidebar.subheader("Spatial Alignment")
z_gap = st.sidebar.slider("Air Gap Clearance (cm)", min_value=10.0, max_value=25.0, value=15.0, step=1.0)
x_mis = st.sidebar.slider("Lateral Misalignment (cm)", min_value=0.0, max_value=30.0, value=5.0, step=1.0)

# 3. Electrical Constants (Hidden in expander for clean UI)
with st.sidebar.expander("Electrical Grid Constants"):
    freq = st.number_input("Grid Frequency (Hz)", value=85000)
    Ip = st.number_input("Primary Current (A)", value=100)
    L = st.number_input("Coil Inductance (H)", value=0.00005, format="%.5f")
    R = st.number_input("Load Resistance (Ω)", value=10.0)
    w = st.number_input("Effective Coil Width (m)", value=1.0)

# ==========================================
# PHYSICS ENGINE & INTEGRATION
# ==========================================
# Calculate Maximum Coupling Penalty
gap_penalty = max(0, (z_gap - 10) * 0.02)
align_penalty = x_mis * 0.01
k_max = max(0.01, 0.85 - gap_penalty - align_penalty)

# Time Series Array Generation
t_vals = np.linspace(-1.5, 1.5, 300)
dt = t_vals[1] - t_vals[0]

# Pre-allocate arrays
k_vals = np.zeros_like(t_vals)
p_vals = np.zeros_like(t_vals)
e_accumulated = 0
e_vals = np.zeros_like(t_vals)

# Core Integration Loop
for i, t in enumerate(t_vals):
    # Gaussian dynamic coupling decay
    k_t = k_max * np.exp(-((v_ms * t) / w)**2)
    
    # Spatial Exhaustion Gate
    if k_t < 0.02:
        k_t = 0.0
        p_kw = 0.0
    else:
        # Faraday's Law & Power Equation
        M = k_t * L                                  
        V = 2 * np.pi * freq * M * Ip              
        p_kw = ((V**2) / R) / 1000                   
        
    e_accumulated += (p_kw * 1000) * dt
    
    k_vals[i] = k_t
    p_vals[i] = p_kw
    e_vals[i] = e_accumulated / 1000  # Convert J to kJ

# Structure Data into Pandas DataFrame
sim_data = pd.DataFrame({
    "Time (s)": t_vals,
    "Coupling (k)": k_vals,
    "Power (kW)": p_vals,
    "Energy (kJ)": e_vals
})

# ==========================================
# VISUALIZATION & OUTPUT METRICS
# ==========================================
col1, col2, col3 = st.columns(3)
col1.metric("Peak Power Output", f"{np.max(p_vals):.2f} kW")
col2.metric("Total Energy Transferred", f"{e_vals[-1]:.2f} kJ")
col3.metric("Max Coupling Efficiency", f"{k_max:.2%}")

st.divider()

# Matplotlib Graph Rendering
st.subheader("Graphical Kinetics: Power & Coupling Decay")
fig, ax1 = plt.subplots(figsize=(10, 4))

color = 'tab:red'
ax1.set_xlabel('Time (s) relative to Coil Center')
ax1.set_ylabel('Power Transfer (kW)', color=color)
ax1.plot(sim_data["Time (s)"], sim_data["Power (kW)"], color=color, linewidth=2, label="Power (kW)")
ax1.tick_params(axis='y', labelcolor=color)

ax2 = ax1.twinx()  
color = 'tab:blue'
ax2.set_ylabel('Magnetic Coupling (k)', color=color)  
ax2.plot(sim_data["Time (s)"], sim_data["Coupling (k)"], color=color, linewidth=2, linestyle='--', label="Coupling (k)")
ax2.tick_params(axis='y', labelcolor=color)

fig.tight_layout()  
st.pyplot(fig)

# Raw Data Matrix View
with st.expander("View Raw Computational Matrix (CSV Data)"):
    st.dataframe(sim_data, use_container_width=True)
    
    # Download Button
    csv = sim_data.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Simulation Data (CSV)",
        data=csv,
        file_name='ev_highway_simulation.csv',
        mime='text/csv',
    )