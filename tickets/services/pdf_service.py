import io
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
)
from reportlab.lib.units import inch
from tickets.services.qr_service import QRService


class PDFService:
    @staticmethod
    def generate_ticket_pdf(context: dict) -> bytes:
        """
        Generates a PDF boarding pass / ticket document as bytes.
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36,
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica-Bold",
        )
        subtitle_style = ParagraphStyle(
            "SubTitle",
            parent=styles["Normal"],
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#64748b"),
        )
        label_style = ParagraphStyle(
            "Label",
            parent=styles["Normal"],
            fontSize=9,
            leading=12,
            textColor=colors.HexColor("#475569"),
            fontName="Helvetica-Bold",
        )
        value_style = ParagraphStyle(
            "Value",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#0f172a"),
            fontName="Helvetica",
        )
        pnr_style = ParagraphStyle(
            "PNR",
            parent=styles["Normal"],
            fontSize=18,
            leading=22,
            textColor=colors.HexColor("#2563eb"),
            fontName="Helvetica-Bold",
        )

        story = []

        # 1. Header
        pnr = context.get("pnr", "N/A")
        qr_bytes = QRService.generate_qr_bytes(pnr)
        qr_image = Image(io.BytesIO(qr_bytes), width=1.1 * inch, height=1.1 * inch)

        header_data = [
            [
                Paragraph(f"<b>ELECTRONIC TICKET</b><br/><font color='#64748b' size=9>{context.get('airline_name', 'Airline')} | E-Boarding Pass</font>", title_style),
                Paragraph(f"PNR:<br/><b><font color='#2563eb' size=18>{pnr}</font></b>", pnr_style),
                qr_image,
            ]
        ]
        header_table = Table(header_data, colWidths=[3.2 * inch, 2.3 * inch, 1.3 * inch])
        header_table.setStyle(TableStyle([
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (1, 0), (1, 0), "CENTER"),
            ("ALIGN", (2, 0), (2, 0), "RIGHT"),
        ]))
        story.append(header_table)
        story.append(Spacer(1, 10))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#e2e8f0"), spaceAfter=12))

        # 2. Flight Details Card
        story.append(Paragraph("<b>FLIGHT DETAILS</b>", label_style))
        story.append(Spacer(1, 6))

        flight_data = [
            [
                Paragraph("<b>Flight</b>", label_style),
                Paragraph("<b>Origin</b>", label_style),
                Paragraph("<b>Destination</b>", label_style),
                Paragraph("<b>Departure</b>", label_style),
                Paragraph("<b>Arrival</b>", label_style),
            ],
            [
                Paragraph(f"<b>{context.get('flight_number')}</b><br/>{context.get('airline_code')}", value_style),
                Paragraph(f"<b>{context.get('origin')}</b>", value_style),
                Paragraph(f"<b>{context.get('destination')}</b>", value_style),
                Paragraph(f"{context.get('departure_time')}", value_style),
                Paragraph(f"{context.get('arrival_time')}", value_style),
            ],
            [
                Paragraph("<b>Terminal / Gate</b>", label_style),
                Paragraph("<b>Class</b>", label_style),
                Paragraph("<b>Status</b>", label_style),
                Paragraph("<b>Total Paid</b>", label_style),
                Paragraph("", label_style),
            ],
            [
                Paragraph(f"{context.get('terminal', 'TBD')} / {context.get('gate', 'TBD')}", value_style),
                Paragraph(f"{context.get('fare_class', 'Economy')}", value_style),
                Paragraph(f"<font color='#16a34a'><b>{context.get('status', 'Confirmed')}</b></font>", value_style),
                Paragraph(f"<b>{context.get('currency')} {context.get('total_amount')}</b>", value_style),
                Paragraph("", value_style),
            ]
        ]
        flight_table = Table(flight_data, colWidths=[1.3 * inch, 1.4 * inch, 1.4 * inch, 1.4 * inch, 1.3 * inch])
        flight_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(flight_table)
        story.append(Spacer(1, 14))

        # 3. Passenger Details Card
        story.append(Paragraph("<b>PASSENGER DETAILS</b>", label_style))
        story.append(Spacer(1, 6))

        p_headers = [Paragraph("<b>#</b>", label_style), Paragraph("<b>Passenger Name</b>", label_style), Paragraph("<b>Type</b>", label_style), Paragraph("<b>Seat Number</b>", label_style)]
        p_rows = [p_headers]

        passengers = context.get("passengers", [])
        for idx, p in enumerate(passengers, 1):
            p_rows.append([
                Paragraph(str(idx), value_style),
                Paragraph(f"<b>{p.get('name')}</b>", value_style),
                Paragraph(p.get("type", "Adult"), value_style),
                Paragraph(f"<b>{p.get('seat', 'Unassigned')}</b>", value_style),
            ])

        p_table = Table(p_rows, colWidths=[0.5 * inch, 3.3 * inch, 1.5 * inch, 1.5 * inch])
        p_table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#f1f5f9")),
            ("PADDING", (0, 0), (-1, -1), 8),
            ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
            ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]))
        story.append(p_table)
        story.append(Spacer(1, 18))

        # 4. Notice
        notice_text = (
            "<b>Important Travel Notice:</b><br/>"
            "• Please present this electronic ticket along with a government-issued photo ID at airport check-in.<br/>"
            "• Check-in counters open 3 hours prior to scheduled departure and close 60 minutes before departure.<br/>"
            "• Standard cabin baggage allowance: 7kg per passenger."
        )
        story.append(Paragraph(notice_text, subtitle_style))

        doc.build(story)
        return buffer.getvalue()
