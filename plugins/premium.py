# Copyright (c) 2025 Gagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

from shared_client import client as bot_client, app
from telethon import events
from datetime import timedelta
from config import OWNER_ID
from utils.func import add_premium_user, is_private_chat, save_user_activity
from pyrogram import filters
from pyrogram.types import InlineKeyboardButton as IK, InlineKeyboardMarkup as IKM
from config import OWNER_ID, JOIN_LINK , ADMIN_CONTACT
from plugins.start import subscribe


@bot_client.on(events.NewMessage(pattern='/add'))
async def add_premium_handler(event):

    user_id = event.sender_id
    sender = await event.get_sender()
    await save_user_activity(user_id, sender, "/add")

    if not await is_private_chat(event):
        await event.respond(
            'This command can only be used in private chats for security reasons.'
            )
        return
    """Handle /add command to add premium users (owner only)"""
    
    if user_id not in OWNER_ID:
        await event.respond('This command is restricted to the bot owner.')
        return
    text = event.message.text.strip()
    parts = text.split(' ')
    if len(parts) != 4:
        await event.respond(
            """Invalid format. Use: /add user_id duration_value duration_unit
Example: /add 123456 1 week"""
            )
        return
    try:
        target_user_id = int(parts[1])
        duration_value = int(parts[2])
        duration_unit = parts[3].lower()
        valid_units = ['min', 'hours', 'days', 'weeks', 'month', 'year',
            'decades']
        if duration_unit not in valid_units:
            await event.respond(
                f"Invalid duration unit. Choose from: {', '.join(valid_units)}"
                )
            return
        success, result = await add_premium_user(target_user_id,
            duration_value, duration_unit)
        if success:
            expiry_utc = result
            expiry_ist = expiry_utc + timedelta(hours=5, minutes=30)
            formatted_expiry = expiry_ist.strftime('%d-%b-%Y %I:%M:%S %p')
            await event.respond(
                f"""✅ User {target_user_id} added as premium member
Subscription valid until: {formatted_expiry} (IST)"""
                )
            await bot_client.send_message(target_user_id,
                f"""✅ Your have been added as premium member
**Validity upto**: {formatted_expiry} (IST)"""
                )
        else:
            await event.respond(f'❌ Failed to add premium user: {result}')
    except ValueError:
        await event.respond(
            'Invalid user ID or duration value. Both must be integers.')
    except Exception as e:
        await event.respond(f'Error: {str(e)}')
        
        

# 机器人是可以在群或频道中接收消息的，所以使用 filter.private 来确保只在私聊中处理 /start 命令
@app.on_message(filters.command('start') & filters.private)
async def start_handler(client, message):

    user_id = message.from_user.id
    await save_user_activity(user_id, message.from_user, "/start")

    subscription_status = await subscribe(client, message)
    if subscription_status == 1:
        return

    kb = IKM([
        [IK('加入频道（必选）', url=JOIN_LINK)],
        [IK('升级套餐', url=ADMIN_CONTACT)]
    ])

    hello_message = f"""
<b>嗨，{message.from_user.mention}（id= {message.from_user.id}）！</b>
<b>欢迎使用 本机器人！</b>
<b>请注意：</b>
<b>1. 在禁止转发的情况下，我仍然可以转发频道或群组的视频、文件</b>
<b>2. 如果需要获取公有频道/群的视频，执行 /single 后，直接发送公有频道的链接</b>
<b>3. 如果需要获取私有频道/群的视频，请先执行 /login（只需一次），然后执行 /single，最后发送消息链接。后续下载中，每次执行 /single 后，发送链接即可</b>
"""

    await message.reply_text(hello_message, reply_markup=kb, quote=False)