from telethon import TelegramClient
import os
import datetime
import re
import pdfplumber
import pytesseract
from PIL import Image
import pandas as pd
import time

# ✅ Replace with your API Credentials from my.telegram.org
API_ID = 27889863
API_HASH = "df4d440af21594b001dc768518140c6b"

# ✅ Persistent session file (avoids repeated phone verification)
SESSION_FILE = "toi_session"

# ✅ Target Telegram Channel
CHANNEL_USERNAME = "the_times_of_india_0"  # Remove '@' symbol

# ✅ Directory to Save PDFs
SAVE_DIR = "./toi_editions"
os.makedirs(SAVE_DIR, exist_ok=True)

# ✅ Get City Name from Environment Variable
city = os.getenv("CITY_NAME", "Pune").strip().title()  # Default city = Pune

# ✅ Initialize Telegram Client with a Persistent Session
client = TelegramClient(SESSION_FILE, API_ID, API_HASH)

async def download_newspaper_edition():
    """Fetch and download the newspaper PDF from Telegram"""
    await client.start()  # ✅ Logs in and saves session automatically

    # ✅ Today's Date Format (DD-MM-YYYY)
    today = datetime.datetime.today().strftime("%d-%m-%Y")

    # ✅ Generate Dynamic File Pattern for the Selected City
    file_pattern = rf"TOI_{city}_{today}\.pdf"

    latest_pdf_path = None
    async for message in client.iter_messages(CHANNEL_USERNAME):
        if message.file and message.file.name:
            file_name = message.file.name
            if re.search(file_pattern, file_name, re.IGNORECASE):
                print(f"✅ Found {city} Edition: {file_name}")

                # ✅ Download the file
                file_path = os.path.join(SAVE_DIR, file_name)
                await message.download_media(file=file_path)

                print(f"✅ Downloaded: {file_name} -> {file_path}")
                latest_pdf_path = file_path
                break
    else:
        print(f"❌ No edition found for {city} on {today}")

    await client.disconnect()
    return latest_pdf_path

def extract_text_from_pdf(pdf_path):
    """Extract and process text from the newspaper PDF"""
    if not pdf_path:
        print("❌ No valid PDF found for processing.")
        return

    # ✅ Define Output Excel File Path
    output_excel = os.path.splitext(pdf_path)[0] + "_Extracted.xlsx"

    # ✅ Keywords to search
    keywords = ["Public Notice", "Tenders", "Property", "Plot", "Registry"]

    # ✅ Initialize DataFrame to store matched results
    matched_results = []

    # ✅ Open PDF and scan each page
    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() if page.extract_text() else pytesseract.image_to_string(page.to_image(resolution=300).original)

            # ✅ Split text into paragraphs
            paragraphs = text.split("\n\n")

            # ✅ Search for Keywords in Extracted Text
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

    # ✅ Convert matched results to DataFrame
    df_extracted = pd.DataFrame(matched_results)

    # ✅ Save extracted data to Excel
    df_extracted.to_excel(output_excel, index=False)

    print(f"✅ Extraction Completed! Matched keywords with full context saved in {output_excel}")

# ✅ Run the Full Pipeline in a Loop Every 1 Hour
while True:
    with client:
        latest_pdf = client.loop.run_until_complete(download_newspaper_edition())
        if latest_pdf:
            extract_text_from_pdf(latest_pdf)
    
    print("🔄 Checking again in 1 hour...")
    time.sleep(3600)  # Wait for 1 hour before checking again
