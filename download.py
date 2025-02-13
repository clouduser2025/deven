from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from telethon import TelegramClient
import os
import datetime
import re

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
            latest_pdf_path = os.path.abspath(file_path)  # Get absolute path
            break

    await client.disconnect()
    
    if not latest_pdf_path:
        raise HTTPException(status_code=404, detail=f"No edition found for {city} on {today}")

    return {"message": f"Downloaded {city} edition", "file_path": latest_pdf_path}

@app.get("/get_pdf/{filename}")
async def get_pdf(filename: str):
    file_path = os.path.join(SAVE_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(file_path, media_type="application/pdf", filename=filename)
