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

# ✅ Replace with your API Credentials from my.telegram.org
API_ID = 27889863
API_HASH = "df4d440af21594b001dc768518140c6b"
SESSION_FILE = "toi_session"
CHANNEL_USERNAME = "the_times_of_india_0"

SAVE_DIR = "./toi_editions"
os.makedirs(SAVE_DIR, exist_ok=True)

client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

@app.get("/")
async def home():
    return {"message": "Telegram PDF Scraper API is running!"}

@app.get("/download/{city}")
async def download(city: str):
    city = city.strip().title()
    today = datetime.datetime.today().strftime("%d-%m-%Y")
    file_pattern = rf"TOI_{city}_{today}\.pdf"

    await client.start()
    latest_pdf_path = None

    async for message in client.iter_messages(CHANNEL_USERNAME):
        if message.file and message.file.name and re.search(file_pattern, message.file.name, re.IGNORECASE):
            file_path = os.path.join(SAVE_DIR, message.file.name)
            await message.download_media(file=file_path)
            latest_pdf_path = file_path
            break

    await client.disconnect()
    
    if not latest_pdf_path:
        raise HTTPException(status_code=404, detail=f"No edition found for {city} on {today}")

    return {"message": f"Downloaded {city} edition", "file": latest_pdf_path}

@app.get("/extract/{city}")
def extract(city: str):
    city = city.strip().title()
    today = datetime.datetime.today().strftime("%d-%m-%Y")
    file_pattern = rf"TOI_{city}_{today}\.pdf"
    
    pdf_files = [f for f in os.listdir(SAVE_DIR) if re.search(file_pattern, f, re.IGNORECASE)]
    
    if not pdf_files:
        raise HTTPException(status_code=404, detail="No matching PDF found")

    pdf_path = os.path.join(SAVE_DIR, pdf_files[0])
    output_excel = os.path.splitext(pdf_path)[0] + "_Extracted.xlsx"
    keywords = ["Public Notice", "Tenders", "Property", "Plot", "Registry"]
    matched_results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or pytesseract.image_to_string(page.to_image(resolution=300).original)
            paragraphs = text.split("\n\n")

            for keyword in keywords:
                for idx, paragraph in enumerate(paragraphs):
                    if keyword.lower() in paragraph.lower():
                        before = paragraphs[idx - 1] if idx > 0 else ""
                        after = paragraphs[idx + 1] if idx < len(paragraphs) - 1 else ""
                        matched_results.append({
                            "Page No.": page_number,
                            "Keyword": keyword,
                            "Extracted Text": f"{before}\n\n{paragraph}\n\n{after}".strip()
                        })

    df_extracted = pd.DataFrame(matched_results)
    df_extracted.to_excel(output_excel, index=False)

    return {"message": "Extraction completed", "file": output_excel}

