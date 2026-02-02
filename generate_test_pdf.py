from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

def create_test_drawing(filename="test_drawing.pdf"):
    c = canvas.Canvas(filename, pagesize=A4)
    width, height = A4

    # Title
    c.setFont("Helvetica-Bold", 16)
    c.drawString(20 * mm, 280 * mm, "Calibration Test Drawing")

    # 1. Standard Linear Dimension with Tolerance
    c.setFont("Helvetica", 12)
    c.drawString(50 * mm, 250 * mm, "Feature A: 50.0 +/- 0.1")
    c.rect(40 * mm, 240 * mm, 60 * mm, 20 * mm)

    # 2. Geometric Tolerance (Text based)
    c.drawString(50 * mm, 220 * mm, "Perpendicularity 0.05 A")
    
    # 3. Geometric Symbols (Simulated with text characters for OCR)
    # Note: Real CAD uses fonts, OCR needs to match shapes.
    # We use standard unicode that Tesseract understands best.
    c.drawString(50 * mm, 190 * mm, "Pos: ⌖ 0.1 M A B")
    c.drawString(50 * mm, 180 * mm, "Perp: ⏊ 0.05 A")
    
    # 4. Standard Dimension (No explicit tolerance)
    c.drawString(50 * mm, 150 * mm, "100.00")
    c.line(40 * mm, 145 * mm, 140 * mm, 145 * mm) # visual line

    # 5. Diameter
    c.drawString(150 * mm, 250 * mm, "Ø 25.0 +/- 0.05")
    c.circle(160 * mm, 240 * mm, 10 * mm)

    # 6. Comma Decimal (European)
    c.drawString(150 * mm, 200 * mm, "12,5 +/- 0,1")

    c.save()
    print(f"Created {filename}")

if __name__ == "__main__":
    create_test_drawing()
