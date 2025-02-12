import pdfplumber
import pytesseract
from PIL import Image
import pandas as pd

# 🔹 Define File Paths
pdf_path = "C:/Users/shafe/automationbot/toi_pune_editions/TOI_Pune_11-02-2025.pdf"
output_excel = "C:/Users/shafe/automationbot/TOI_Pune_Extracted.xlsx"

# 🔹 Keywords to search
keywords = ["Public Notice", "Tenders", "Property", "Plot", "Registry"]

# 🔹 Initialize DataFrame to store matched results
matched_results = []

# 🔹 Function to extract text from a PDF page
def extract_text_from_page(page):
    try:
        return page.extract_text()  # Extract text if it's a text-based PDF
    except:
        return None

# 🔹 Open PDF and scan each page
with pdfplumber.open(pdf_path) as pdf:
    for page_number, page in enumerate(pdf.pages, start=1):
        text = extract_text_from_page(page)
        
        if not text:  # If text extraction fails, apply OCR
            image = page.to_image(resolution=300).original  # Convert page to image
            text = pytesseract.image_to_string(image)  # Apply OCR
        
        # 🔹 Split text into paragraphs
        paragraphs = text.split("\n\n")  # Double line breaks separate sections
        
        # 🔹 Search for Keywords in Extracted Text
        for keyword in keywords:
            for idx, paragraph in enumerate(paragraphs):
                if keyword.lower() in paragraph.lower():
                    # Extract surrounding paragraphs (to get full context)
                    before = paragraphs[idx - 1] if idx > 0 else ""
                    after = paragraphs[idx + 1] if idx < len(paragraphs) - 1 else ""
                    full_section = f"{before}\n\n{paragraph}\n\n{after}"

                    matched_results.append({
                        "Page No.": page_number,
                        "Keyword": keyword,
                        "Extracted Text": full_section.strip()
                    })

# 🔹 Convert matched results to DataFrame
df_extracted = pd.DataFrame(matched_results)

# 🔹 Save extracted data to Excel
df_extracted.to_excel(output_excel, index=False)

print(f"✅ Extraction Completed! Matched keywords with full context saved in {output_excel}")
