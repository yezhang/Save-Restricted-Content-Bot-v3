# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

from telethon import TelegramClient
from config import API_ID, API_HASH, BOT_TOKEN, STRING
from pyrogram import Client
import sys

client = TelegramClient("telethonbot", API_ID, API_HASH)
"""client, a telethon client for bot operations."""

app = Client("pyrogrambot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
""" app, a pyrogram client for bot operations.

Returns:
    _type_: pyrogram.Client
"""

userbot = Client("4gbbot", api_id=API_ID, api_hash=API_HASH, session_string=STRING)
"""userbot, pyrogram client for user(4gb client) operations.

Returns:
    _type_: pyrogram.Client
"""

async def start_client():
    if not client.is_connected():
        await client.start(bot_token=BOT_TOKEN)
        print("SpyLib started...")
    if STRING:
        try:
            await userbot.start()
            print("Userbot started...")
            print(await userbot.export_session_string())
        except Exception as e:
            print(f"Hey honey!! check your premium string session, it may be invalid of expire {e}")
            sys.exit(1)
    await app.start()
    print("Pyro App Started...")
    return client, app, userbot

