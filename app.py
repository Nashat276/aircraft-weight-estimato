import streamlit as st
import pandas as pd
import plotly.express as px
from utils import solve_wto_iterative, sensitivity_analysis, ws_wp_curve
from pdf_export import create_pdf_report

st.set_page_config(page_title="AEROSIZER PRO — Regional Turboprop", layout="wide")

# CSS زر Calculate أزرق أنيق
st.markdown("""
    <style>
    .stButton>button {
        background-color: #0b63d6;
        color: #fff;
        border-radius: 8px;
        padding: 8px 14px;
        font-size: 15px;
        border: none;
    }
    .stButton>button:hover {
        background-color: #0954b0;
    }
    </style>
""", unsafe_allow_html=True)

# Hero
st.title("AEROSIZER PRO — Regional Turboprop")
st.subheader("Preliminary Weight Estimation · Breguet Method · Propeller Aircraft")

# Sidebar inputs (مأخوذة من Homework1rev.pdf)
st.sidebar.header("Mission & Payload Inputs")
passengers = st.sidebar.number_input("Number of passengers", value=34, min_value=0)
pax_weight = st.sidebar.number_input("Passenger weight (lbs)", value=175)
baggage = st.sidebar.number_input("Baggage per pax (lbs)", value=30)
pilots = st.sidebar.number_input("Number of pilots", value=2)
attendants = st.sidebar.number_input("Number of attendants", value=1)
crew_weight_total = st.sidebar.number_input("Crew total weight (lbs)", value=615)
wtfo = st.sidebar.number_input("W_tfo (flight attendant + misc) (lbs)", value=242.75)

# Mission performance
st.sidebar.header("Performance Inputs")
V_cruise_kts = st.sidebar.number_input("Cruise speed (kts)", value=250)
L_over_D_cruise = st.sidebar.number_input("L/D (cruise)", value=13.0)
Cp_cruise = st.sidebar.number_input("Cp (lbs/hp/hr) cruise", value=0.6)
eta_p_cruise = st.sidebar.number_input("Propeller efficiency ηp (cruise)", value=0.85)
R_nm = st.sidebar.number_input("Range (NM)", value=250)

# Loiter inputs (from file)
st.sidebar.header("Loiter Inputs")
V_loiter_kts = st.sidebar.number_input("Loiter speed (kts)", value=0.75 * V_cruise_kts)
L_over_D_loiter = st.sidebar.number_input("L/D (loiter)", value=16.0)
Cp_loiter = st.sidebar.number_input("Cp (lbs/hp/hr) loiter", value=0.65)
eta_p_loiter = st.sidebar.number_input("Propeller efficiency ηp (loiter)", value=0.77)
E_loiter_hr = st.sidebar.number_input("Loiter time (hr)", value=0.75)

# Empirical empty weight model (قابلة للتعديل)
st.sidebar.header("Empty Weight Estimation (empirical)")
st.sidebar.markdown("**WE = A * (WTO)^B**  — اضبط A و B حسب مرجعك (Raymer/Roskam)")
A_emp = st.sidebar.number_input("A (empirical)", value=0.32, format="%.4f")
B_emp = st.sidebar.number_input("B (empirical)", value=0.90, format="%.4f")

# Derived payloads
W_payload = passengers * pax_weight + passengers * baggage
W_crew = crew_weight_total
W_pl = W_payload + W_crew + wtfo

st.sidebar.markdown("---")
st.sidebar.write(f"**Payload total (W_pl):** {W_pl:.1f} lbs")

# Use session_state to store results and avoid recalculation on every change
if "results" not in st.session_state:
    st.session_state["results"] = None

# Calculate button
if st.sidebar.button("⟳ Calculate"):
    # call solver
    results = solve_wto_iterative(
        W_pl=W_pl,
        V_cruise_kts=V_cruise_kts,
        L_over_D_cruise=L_over_D_cruise,
        Cp_cruise=Cp_cruise,
        eta_p_cruise=eta_p_cruise,
        R_nm=R_nm,
        V_loiter_kts=V_loiter_kts,
        L_over_D_loiter=L_over_D_loiter,
        Cp_loiter=Cp_loiter,
        eta_p_loiter=eta_p_loiter,
        E_loiter_hr=E_loiter_hr,
        A_emp=A_emp,
        B_emp=B_emp
    )
    st.session_state["results"] = results
    st.success("✅ Calculation complete")

# Show results if available
if st.session_state["results"] is not None:
    res = st.session_state["results"]
    col1, col2, col3 = st.columns(3)
    col1.metric("Takeoff Weight (WTO) [lbs]", f"{res['WTO']:.1f}")
    col2.metric("Empty Weight (WE) [lbs]", f"{res['WE']:.1f}")
    col3.metric("Fuel Weight (WF) [lbs]", f"{res['WF']:.1f}")

    st.markdown("### Weight fractions by phase (used)")
    st.table(pd.DataFrame(res["phase_fractions"], index=[0]).T.rename(columns={0:"Value"}))

    # Sensitivity table & plot
    sens_df = sensitivity_analysis(
        WTO=res["WTO"],
        R_nm=R_nm,
        L_over_D=L_over_D_cruise,
        Cp=Cp_cruise,
        eta_p=eta_p_cruise
    )
    st.markdown("### Sensitivity Analysis (partials)")
    st.dataframe(sens_df.style.format({"Value":"{:.2f}"}))

    fig1 = px.bar(sens_df, x="Parameter", y="Value", title="Sensitivity of WTO to parameters")
    st.plotly_chart(fig1, use_container_width=True)

    # W/S vs W/P curve (illustrative)
    st.markdown("### Design Envelope: Takeoff Power Loading vs Wing Loading (illustrative)")
    ws_wp = ws_wp_curve(res["WTO"])
    fig2 = px.line(ws_wp, x="W/S (lb/ft^2)", y="W/P (lb/hp)", title="W/S vs W/P")
    st.plotly_chart(fig2, use_container_width=True)

    # Export PDF button
    if st.button("📄 Export PDF Report"):
        pdf_path = create_pdf_report(res, sens_df)
        st.success(f"PDF exported: {pdf_path}")

else:
    st.info("اضغط ⟳ Calculate في الشريط الجانبي لحساب الأوزان وعرض النتائج.")
