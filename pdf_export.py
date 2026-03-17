from fpdf import FPDF

def export_pdf(results, sens):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, "Aircraft Design Report", ln=True, align="C")
    pdf.ln(10)

    pdf.cell(200, 10, f"WTO: {results['WTO']:.2f} lbs", ln=True)
    pdf.cell(200, 10, f"WE: {results['WE']:.2f} lbs", ln=True)
    pdf.cell(200, 10, f"WF: {results['WF']:.2f} lbs", ln=True)

    pdf.ln(10)
    pdf.cell(200, 10, "Sensitivity Analysis", ln=True)

    for i, row in sens.iterrows():
        pdf.cell(200, 10, f"{row['Parameter']}: {row['Sensitivity']:.2f}", ln=True)

    pdf.output("Aircraft_Report.pdf")
