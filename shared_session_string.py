# 生成一个新的 session string
from pyrogram import Client

async with Client("my_account", in_memory=True) as app:
    print(await app.export_session_string())
