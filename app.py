from flask import Flask, request, jsonify
from telethon import TelegramClient, events
import os
import datetime
import re
import pdfplumber
import pytesseract
from PIL import Image
import pandas as pd
import asyncio

app = Flask(__name__)

# ✅ Telegram API Credentials (Replace with yours)
API_ID = 27889863
API_HASH = "df4d440af21594b001dc768518140c6b"
SESSION_FILE = "toi_session"
CHANNEL_USERNAME = "the_times_of_india_0"  # Remove '@' symbol
SAVE_DIR = "./toi_editions"

# ✅ Ensure Directory Exists
os.makedirs(SAVE_DIR, exist_ok=True)

# ✅ Initialize Telegram Client
client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

async def download_newspaper_edition(city):
    """Fetch and download the newspaper PDF from Telegram."""
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
    """Extract and process text from the newspaper PDF."""
    if not pdf_path:
        return {"error": "No valid PDF found for processing."}

    output_excel = os.path.splitext(pdf_path)[0] + "_Extracted.xlsx"
    keywords = ["Public Notice", "Tenders", "Property", "Plot", "Registry"]
    matched_results = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            if not text:
                image = page.to_image(resolution=300).original
                text = pytesseract.image_to_string(image)

            paragraphs = text.split("\n\n")
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

    df_extracted = pd.DataFrame(matched_results)
    df_extracted.to_excel(output_excel, index=False)

    return {"message": "Extraction completed", "excel_file": output_excel, "data": matched_results}

@app.route("/download", methods=["GET"])
def download_and_extract():
    """API Endpoint to download and extract text from a newspaper."""
    city = request.args.get("city", "").strip().title()
    if not city:
        return jsonify({"error": "City name is required"}), 400

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    pdf_path = loop.run_until_complete(download_newspaper_edition(city))

    if not pdf_path:
        return jsonify({"error": f"No edition found for {city} on {datetime.datetime.today().strftime('%d-%m-%Y')}"}), 404

    extraction_result = extract_text_from_pdf(pdf_path)
    return jsonify(extraction_result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
