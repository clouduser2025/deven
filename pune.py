from telethon import TelegramClient, events
import os
import datetime
import re

# ✅ Replace with your API Credentials from my.telegram.org
API_ID = 27889863
API_HASH = "df4d440af21594b001dc768518140c6b"

# ✅ Target Telegram Channel
CHANNEL_USERNAME = "the_times_of_india_0"  # Remove '@' symbol

# ✅ Directory to Save PDFs
SAVE_DIR = "./toi_pune_editions"
os.makedirs(SAVE_DIR, exist_ok=True)

# ✅ Today's Date Format (DD-MM-YYYY)
today = datetime.datetime.today().strftime("%d-%m-%Y")
file_pattern = rf"TOI_Pune_{today}\.pdf"

# ✅ Initialize Telegram Client
client = TelegramClient("toi_pune_session", API_ID, API_HASH)

async def download_pune_edition():
    await client.start()

    # ✅ Fetch messages from the TOI channel
    async for message in client.iter_messages(CHANNEL_USERNAME):
        if message.file and message.file.name:
            file_name = message.file.name
            if re.search(file_pattern, file_name):
                print(f"✅ Found Pune Edition: {file_name}")

                # ✅ Download the file
                file_path = os.path.join(SAVE_DIR, file_name)
                await message.download_media(file=file_path)

                print(f"✅ Downloaded: {file_name} -> {file_path}")
                break

    await client.disconnect()

# ✅ Run the script
with client:
    client.loop.run_until_complete(download_pune_edition())
