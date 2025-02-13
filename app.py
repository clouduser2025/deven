from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from telethon.sync import TelegramClient  # ✅ Use sync Telethon client
import os
import datetime
import re
import pdfplumber
import pytesseract
import pandas as pd

app = FastAPI()

# ✅ Telegram API Credentials
API_ID = 27889863
API_HASH = "df4d440af21594b001dc768518140c6b"

# ✅ Telegram Session and Channel
SESSION_FILE = "toi_session"
CHANNEL_USERNAME = "the_times_of_india_0"
SAVE_DIR = "./toi_editions"
os.makedirs(SAVE_DIR, exist_ok=True)

# ✅ Initialize Telegram Client (Synchronous)
client = TelegramClient(SESSION_FILE, API_ID, API_HASH)
client.connect()


def download_newspaper_edition(city):
    """Download the latest newspaper PDF from Telegram (Sync Version)"""
    if not client.is_user_authorized():
        raise HTTPException(status_code=403, detail="Telegram client is not authorized.")

    today = datetime.datetime.today().strftime("%d-%m-%Y")
    file_pattern = rf"TOI_{city}_{today}\.pdf"

    latest_pdf_path = None
    for message in client.iter_messages(CHANNEL_USERNAME):
        if message.file and message.file.name:
            file_name = message.file.name
            if re.search(file_pattern, file_name, re.IGNORECASE):
                file_path = os.path.join(SAVE_DIR, file_name)
                message.download_media(file=file_path)
                latest_pdf_path = file_path
                break

    return latest_pdf_path


def extract_text_from_pdf(pdf_path):
    """Extract text from a downloaded PDF and match keywords."""
    if not pdf_path or not os.path.exists(pdf_path):
        raise HTTPException(status_code=404, detail="PDF file not found.")

    keywords = ["Public Notice", "Tenders", "Property", "Plot", "Registry"]
    matched_results = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_number, page in enumerate(pdf.pages, start=1):
                text = page.extract_text()
                
                # 🛠️ If text extraction fails, use OCR
                if not text:
                    text = pytesseract.image_to_string(page.to_image(resolution=300).original)
                
                # 📝 Clean up and process extracted text
                paragraphs = [p.strip() for p in text.split("\n\n")] if text else []

                for keyword in keywords:
                    for idx, paragraph in enumerate(paragraphs):
                        if keyword.lower() in paragraph.lower():
                            before = paragraphs[idx - 1] if idx > 0 else ""
                            after = paragraphs[idx + 1] if idx < len(paragraphs) - 1 else ""
                            full_section = f"{before}\n\n{paragraph}\n\n{after}".strip()

                            matched_results.append({
                                "Page No.": page_number,
                                "Keyword": keyword,
                                "Extracted Text": full_section
                            })

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing PDF: {str(e)}")

    return {"extracted_data": matched_results if matched_results else "No matches found"}


@app.get("/download-pdf")
def download_pdf(city: str):
    """API Endpoint to Download Newspaper PDF"""
    latest_pdf = download_newspaper_edition(city)
    if not latest_pdf:
        raise HTTPException(status_code=404, detail=f"No edition found for {city}.")
    return {"message": f"PDF downloaded: {latest_pdf}", "pdf_path": latest_pdf}


@app.get("/extract-text-excel")
def extract_text_excel(city: str):
    """Extract text and save as an Excel file."""
    today = datetime.datetime.today().strftime("%d-%m-%Y")
    file_pattern = rf"TOI_{city}_{today}\.pdf"

    # Find downloaded PDF
    for file in os.listdir(SAVE_DIR):
        if re.search(file_pattern, file, re.IGNORECASE):
            pdf_path = os.path.join(SAVE_DIR, file)
            extracted_data = extract_text_from_pdf(pdf_path)

            # Convert extracted data to a Pandas DataFrame
            df = pd.DataFrame(extracted_data["extracted_data"])

            # Save to an Excel file
            excel_path = os.path.join(SAVE_DIR, f"Extracted_{city}_{today}.xlsx")
            df.to_excel(excel_path, index=False)

            # Return the Excel file as a response
            return FileResponse(excel_path, filename=f"Extracted_{city}_{today}.xlsx", media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    raise HTTPException(status_code=404, detail=f"No PDF found for {city} on {today}. Download first.")
