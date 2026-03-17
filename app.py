import streamlit as st
import plotly.express as px
from utils import calculate_weights, sensitivity_analysis
from pdf_export import export_pdf

st.set_page_config(page_title="Aircraft Design Tool", layout="wide")

# CSS لتنسيق زر Calculate
st.markdown("""
    <style>
    div.stButton > button:first-child {
        background-color: #007BFF;
        color: white;
        border-radius: 8px;
        font-size: 16px;
        padding: 8px 16px;
    }
    </style>
""", unsafe_allow_html=True)

# Hero Section
st.title("✈️ Regional Turboprop Design Tool")
st.subheader("Based on Homework & Project Specs")

# Sidebar Inputs
st.sidebar.header("Mission Inputs")
payload = st.sidebar.number_input("Payload (lbs)", value=6970)
crew = st.sidebar.number_input("Crew Weight (lbs)", value=615)
range_nm = st.sidebar.number_input("Cruise Range (NM)", value=250)
ld_ratio = st.sidebar.number_input("L/D Ratio", value=13.0)
cp = st.sidebar.number_input("Specific Fuel Consumption Cp (lbs/hp/hr)", value=0.6)
eta_p = st.sidebar.number_input("Propeller Efficiency ηp", value=0.85)

# زر الحساب
if st.sidebar.button("⟳ Calculate"):
    results = calculate_weights(payload, crew, range_nm, ld_ratio, cp, eta_p)
    st.success("✅ Calculation Complete")

    # عرض النتائج
    st.write("### Results")
    st.write(f"**Takeoff Weight (WTO):** {results['WTO']:.2f} lbs")
    st.write(f"**Empty Weight (WE):** {results['WE']:.2f} lbs")
    st.write(f"**Fuel Weight (WF):** {results['WF']:.2f} lbs")

    # حساسية
    st.write("### Sensitivity Analysis")
    sens = sensitivity_analysis(results['WTO'], range_nm, ld_ratio, cp, eta_p)
    st.dataframe(sens)

    # رسومات Plotly
    fig = px.line(sens, x="Parameter", y="Sensitivity", title="Sensitivity Analysis")
    st.plotly_chart(fig)

    # إخراج PDF
    if st.button("📄 Export PDF"):
        export_pdf(results, sens)
        st.success("📄 PDF Exported Successfully! Check Aircraft_Report.pdf")
