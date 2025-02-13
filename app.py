from fastapi import FastAPI, HTTPException
from telethon import TelegramClient
import os
import datetime
import re
import pdfplumber
import pytesseract
from PIL import Image
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

# ✅ Initialize Telegram Client
client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

async def download_newspaper_edition(city):
    """Download the latest newspaper PDF from Telegram"""
    await client.start()
    today = datetime.datetime.today().strftime("%d-%m-%Y")
    file_pattern = rf"TOI_{city}_{today}\.pdf"

    latest_pdf_path = None
    async for message in client.iter_messages(CHANNEL_USERNAME):
        if message.file and message.file.name:
            file_name = message.file.name
            if re.search(file_pattern, file_name, re.IGNORECASE):
                file_path = os.path.join(SAVE_DIR, file_name)
                await message.download_media(file=file_path)
                latest_pdf_path = file_path
                break

    await client.disconnect()
    return latest_pdf_path

def extract_text_from_pdf(pdf_path):
    """Extract text from a downloaded PDF"""
    if not pdf_path or not os.path.exists(pdf_path):
        return {"error": "PDF not found."}

    keywords = ["Public Notice", "Tenders", "Property", "Plot", "Registry"]
    matched_results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or pytesseract.image_to_string(page.to_image(resolution=300).original)
            paragraphs = text.split("\n\n") if text else []

            for keyword in keywords:
                for idx, paragraph in enumerate(paragraphs):
                    if keyword.lower() in paragraph.lower():
                        before = paragraphs[idx - 1] if idx > 0 else ""
                        after = paragraphs[idx + 1] if idx < len(paragraphs) - 1 else ""
                        full_section = f"{before}\n\n{paragraph}\n\n{after}"
                        matched_results.append({
                            "Page No.": page_number,
                            "Keyword": keyword,
                            "Extracted Text": full_section.strip()
                        })

    return {"extracted_data": matched_results}

@app.get("/download-pdf")
async def download_pdf(city: str):
    """API Endpoint to Download Newspaper PDF"""
    latest_pdf = await download_newspaper_edition(city)
    if not latest_pdf:
        raise HTTPException(status_code=404, detail=f"No edition found for {city}.")
    return {"message": f"PDF downloaded: {latest_pdf}", "pdf_path": latest_pdf}

@app.get("/extract-text")
async def extract_text(city: str):
    """API Endpoint to Extract Text from Downloaded PDF"""
    today = datetime.datetime.today().strftime("%d-%m-%Y")
    file_pattern = rf"TOI_{city}_{today}\.pdf"

    # Find downloaded PDF
    for file in os.listdir(SAVE_DIR):
        if re.search(file_pattern, file, re.IGNORECASE):
            pdf_path = os.path.join(SAVE_DIR, file)
            return extract_text_from_pdf(pdf_path)

    raise HTTPException(status_code=404, detail=f"No PDF found for {city} on {today}. Download first.")
