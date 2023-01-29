import textract
from fpdf import FPDF

# Extract text from word document
text = textract.process("original.docx").decode("utf-8")
# text = textract.process("template.pdf").decode("utf-8")
pdf = FPDF()
pdf.add_font('Arial Unicode', '', 'Arial Unicode MS Font.ttf', uni=True)
pdf.set_font("Arial Unicode", size=12)

# Replace the old text with the new text
text = text.replace("offer_to", "new text")

# Create a new pdf document
pdf.add_page()
pdf.multi_cell(0, 10, txt=text)
pdf.output("modified.pdf")
