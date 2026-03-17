from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
import pandas as pd
import io

def create_pdf_report(results, sens_df, filename="Aircraft_Report.pdf"):
    """
    Create a professional PDF report using reportlab.
    sens_df: pandas DataFrame of sensitivity results.
    Returns path to saved PDF.
    """
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=2*cm, leftMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph("AEROSIZER PRO — Aircraft Design Report", styles['Title']))
    story.append(Spacer(1, 12))

    # Summary table (WTO, WE, WF)
    story.append(Paragraph("<b>Summary of Results</b>", styles['Heading2']))
    data = [
        ["Takeoff Weight (WTO) [lbs]", f"{results['WTO']:.1f}"],
        ["Empty Weight (WE) [lbs]", f"{results['WE']:.1f}"],
        ["Fuel Weight (WF) [lbs]", f"{results['WF']:.1f}"],
        ["Fuel fraction used (Mff)", f"{results['Mff']:.4f}"],
        ["Iterations to converge", f"{results.get('iterations', '')}"]
    ]
    t = Table(data, colWidths=[9*cm, 6*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('FONTNAME', (0,0), (-1,-1), 'Helvetica')
    ]))
    story.append(t)
    story.append(Spacer(1, 12))

    # Phase fractions table
    story.append(Paragraph("<b>Phase Weight Fractions Used</b>", styles['Heading3']))
    pf = results['phase_fractions']
    pf_items = [[k, f"{v:.6f}"] for k, v in pf.items()]
    t2 = Table(pf_items, colWidths=[9*cm, 6*cm])
    t2.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 0.4, colors.grey)]))
    story.append(t2)
    story.append(Spacer(1, 12))

    # Sensitivity table with controlled column widths to avoid overflow
    story.append(Paragraph("<b>Sensitivity Analysis</b>", styles['Heading3']))
    sens_data = [["Parameter", "Value"]]
    for _, row in sens_df.iterrows():
        sens_data.append([str(row['Parameter']), f"{row['Value']:.3f}"])
    t3 = Table(sens_data, colWidths=[10*cm, 5*cm])
    t3.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#f0f0f0")),
        ('GRID', (0,0), (-1,-1), 0.4, colors.grey),
        ('ALIGN', (1,1), (-1,-1), 'RIGHT')
    ]))
    story.append(t3)
    story.append(Spacer(1, 12))

    # Footer / notes
    story.append(Paragraph("Notes:", styles['Heading4']))
    story.append(Paragraph("• Cruise and loiter fractions computed using Breguet propeller equations.", styles['Normal']))
    story.append(Paragraph("• Empty weight estimated using empirical model WE = A * WTO^B (A,B user inputs).", styles['Normal']))
    story.append(Spacer(1, 20))

    doc.build(story)
    # write buffer to file
    with open(filename, "wb") as f:
        f.write(buffer.getvalue())
    buffer.close()
    return filename
