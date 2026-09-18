import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

def create_pdf_from_text(text_filepath, output_pdf_path):
    with open(text_filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    doc = SimpleDocTemplate(
        output_pdf_path,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=15,
        leading=19,
        textColor=colors.HexColor('#0891b2'),
        fontName='Helvetica-Bold',
        spaceAfter=6
    )
    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        textColor=colors.HexColor('#64748b'),
        fontName='Helvetica-Oblique',
        spaceAfter=12
    )
    h2_style = ParagraphStyle(
        'Heading2Style',
        parent=styles['Heading2'],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor('#0f766e'),
        fontName='Helvetica-Bold',
        spaceBefore=10,
        spaceAfter=4
    )
    body_style = ParagraphStyle(
        'BodyDark',
        parent=styles['Normal'],
        fontSize=9.5,
        leading=13.5,
        textColor=colors.HexColor('#1e293b'),
        fontName='Helvetica',
        spaceAfter=4
    )

    story = []
    is_first_line = True

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            story.append(Spacer(1, 4))
            continue

        if is_first_line:
            story.append(Paragraph(line, title_style))
            story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#0891b2'), spaceAfter=8))
            is_first_line = False
        elif any(line.startswith(prefix) for prefix in ["Department", "American", "International", "Guideline Code", "Oral and", "Metro Dental", "Chart Number"]):
            story.append(Paragraph(line, subtitle_style))
        elif line.startswith(("1.", "2.", "3.", "4.", "5.", "6.")) and len(line) < 80:
            story.append(Spacer(1, 6))
            story.append(Paragraph(line, h2_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor('#cbd5e1'), spaceAfter=4))
        elif line.startswith(("A.", "B.", "C.", "D.")):
            story.append(Paragraph(f"<b>{line}</b>", body_style))
        else:
            safe_text = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            story.append(Paragraph(safe_text, body_style))

    doc.build(story)
    print(f"Generated PDF: {output_pdf_path}")

def main():
    sample_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'sample_documents')
    for filename in os.listdir(sample_dir):
        if filename.endswith('.txt'):
            txt_path = os.path.join(sample_dir, filename)
            pdf_path = os.path.join(sample_dir, filename.replace('.txt', '.pdf'))
            create_pdf_from_text(txt_path, pdf_path)

if __name__ == '__main__':
    main()
