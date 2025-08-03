# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import BadRequest, SessionPasswordNeeded, PhoneCodeInvalid, PhoneCodeExpired, MessageNotModified
import logging
import os
from config import API_HASH, API_ID
from shared_client import app as bot
from utils.func import save_user_session, get_user_data, remove_user_session, save_user_bot, remove_user_bot
from utils.func import save_user_activity
from utils.encrypt import ecs, dcs
from plugins.batch import UB, UC
from utils.custom_filters import login_in_progress, set_user_step, get_user_step

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
model = "v3saver"

STEP_PHONE = 1
STEP_CODE = 2
STEP_PASSWORD = 3
login_cache = {}

@bot.on_message(filters.command('login'))
async def login_command(client, message):
    user_id = message.from_user.id
    await save_user_activity(user_id, message.from_user, "/login")

    set_user_step(user_id, STEP_PHONE)
    login_cache.pop(user_id, None)
    await message.delete()

    status_msg = await message.reply(
        """请输入手机号（带国家代码）
例如: `+861234567890`"""
        )
    login_cache[user_id] = {'status_msg': status_msg}
    
    
@bot.on_message(filters.command("setbot"))
async def set_bot_token(C, m):
    user_id = m.from_user.id

    await save_user_activity(user_id, m.from_user, "/setbot")

    args = m.text.split(" ", 1)
    if user_id in UB:
        try:
            await UB[user_id].stop()
            if UB.get(user_id, None):
                del UB[user_id]  # Remove from dictionary
                
            try:
                if os.path.exists(f"user_{user_id}.session"):
                    os.remove(f"user_{user_id}.session")
            except Exception:
                pass
            
            print(f"Stopped and removed old bot for user {user_id}")
        except Exception as e:
            print(f"Error stopping old bot for user {user_id}: {e}")
            del UB[user_id]  # Remove from dictionary

    if len(args) < 2:
        await m.reply_text("⚠️ 请提供机器人 Token. 用法: `/setbot <替换为真实的 bot token>`", quote=True)
        return

    bot_token = args[1].strip()
    await save_user_bot(user_id, bot_token)
    await m.reply_text("✅ 机器人 Token 设置成功.", quote=True)
    
    
@bot.on_message(filters.command("rembot"))
async def rem_bot_token(C, m):
    user_id = m.from_user.id

    await save_user_activity(user_id, m.from_user, "/rembot")

    if user_id in UB:
        try:
            await UB[user_id].stop()
            
            if UB.get(user_id, None):
                del UB[user_id]  # Remove from dictionary # Remove from dictionary
            print(f"Stopped and removed old bot for user {user_id}")
            try:
                if os.path.exists(f"user_{user_id}.session"):
                    os.remove(f"user_{user_id}.session")
            except Exception:
                pass
        except Exception as e:
            print(f"Error stopping old bot for user {user_id}: {e}")
            if UB.get(user_id, None):
                del UB[user_id]  # Remove from dictionary  # Remove from dictionary
            try:
                if os.path.exists(f"user_{user_id}.session"):
                    os.remove(f"user_{user_id}.session")
            except Exception:
                pass
    await remove_user_bot(user_id)
    await m.reply_text("✅ 机器人 Token 移除成功.", quote=True)

    
@bot.on_message(login_in_progress & filters.text & filters.private & ~filters.command([
    'start', 'batch', 'cancel', 'login', 'logout', 'stop', 'set', 'pay',
    'redeem', 'gencode', 'generate', 'keyinfo', 'encrypt', 'decrypt', 'keys', 'setbot', 'rembot']))
async def handle_login_steps(client, message):
    user_id = message.from_user.id
    text = message.text.strip()
    step = get_user_step(user_id)

    await save_user_activity(user_id, message.from_user, "login steps", {"step": step, "text": text})

    try:
        await message.delete()
    except Exception as e:
        logger.warning(f'Could not delete message: {e}')
    status_msg = login_cache[user_id].get('status_msg')
    if not status_msg:
        status_msg = await message.reply('处理中...')
        login_cache[user_id]['status_msg'] = status_msg
    try:
        if step == STEP_PHONE:
            if not text.startswith('+'):
                await edit_message_safely(status_msg,
                    '❌ 请输入有效的手机号（+开头）')
                return
            await edit_message_safely(status_msg,
                '🔄 正在处理手机号...')
            temp_client = Client(f'temp_{user_id}', api_id=API_ID, api_hash
                =API_HASH, device_model=model, in_memory=True)
            try:
                await temp_client.connect()
                sent_code = await temp_client.send_code(text)
                login_cache[user_id]['phone'] = text
                login_cache[user_id]['phone_code_hash'
                    ] = sent_code.phone_code_hash
                login_cache[user_id]['temp_client'] = temp_client
                set_user_step(user_id, STEP_CODE)
                await edit_message_safely(status_msg,
                    """✅ 验证码已发送到您的 Telegram 账户。

请输入您收到的验证码，例如 1 2 3 4 5（用空格分隔）："""
                    )
            except BadRequest as e:
                await edit_message_safely(status_msg,
                    f"""❌ 错误: {str(e)}
请尝试使用 /login 再次登录。""")
                await temp_client.disconnect()
                set_user_step(user_id, None)
        elif step == STEP_CODE:
            code = text.replace(' ', '')
            phone = login_cache[user_id]['phone']
            phone_code_hash = login_cache[user_id]['phone_code_hash']
            temp_client = login_cache[user_id]['temp_client']
            try:
                await edit_message_safely(status_msg, '🔄 正在检查验证码...')
                await temp_client.sign_in(phone, phone_code_hash, code)
                session_string = await temp_client.export_session_string()
                encrypted_session = ecs(session_string)
                await save_user_session(user_id, encrypted_session)
                await temp_client.disconnect()
                temp_status_msg = login_cache[user_id]['status_msg']
                login_cache.pop(user_id, None)
                login_cache[user_id] = {'status_msg': temp_status_msg}
                await edit_message_safely(status_msg,
                    """✅ 登录成功!!"""
                    )
                set_user_step(user_id, None)
            except SessionPasswordNeeded:
                set_user_step(user_id, STEP_PASSWORD)
                await edit_message_safely(status_msg,
                    """🔒 启用了双重验证。
请输入您的密码:"""
                    )
            except (PhoneCodeInvalid, PhoneCodeExpired) as e:
                await edit_message_safely(status_msg,
                    f'❌ {str(e)}. 请尝试使用 /login 再次登录。')
                await temp_client.disconnect()
                login_cache.pop(user_id, None)
                set_user_step(user_id, None)
        elif step == STEP_PASSWORD:
            temp_client = login_cache[user_id]['temp_client']
            try:
                await edit_message_safely(status_msg, '🔄 验证密码中...'
                    )
                await temp_client.check_password(text)
                session_string = await temp_client.export_session_string()
                encrypted_session = ecs(session_string)
                await save_user_session(user_id, encrypted_session)
                await temp_client.disconnect()
                temp_status_msg = login_cache[user_id]['status_msg']
                login_cache.pop(user_id, None)
                login_cache[user_id] = {'status_msg': temp_status_msg}
                await edit_message_safely(status_msg,
                    """✅ 登录成功!!"""
                    )
                set_user_step(user_id, None)
            except BadRequest as e:
                await edit_message_safely(status_msg,
                    f"""❌ 密码错误: {str(e)}
请再试一次:""")
    except Exception as e:
        logger.error(f'Error in login flow: {str(e)}')
        await edit_message_safely(status_msg,
            f"""❌ 发生错误: {str(e)}
请尝试使用 /login 再次登录。""")
        if user_id in login_cache and 'temp_client' in login_cache[user_id]:
            await login_cache[user_id]['temp_client'].disconnect()
        login_cache.pop(user_id, None)
        set_user_step(user_id, None)


async def edit_message_safely(message, text):
    """Helper function to edit message and handle errors"""
    try:
        await message.edit(text)
    except MessageNotModified:
        pass
    except Exception as e:
        logger.error(f'Error editing message: {e}')
        
@bot.on_message(filters.command('cancel'))
async def cancel_login_command(client, message):
    user_id = message.from_user.id

    await save_user_activity(user_id, message.from_user, "/cancel")

    await message.delete()
    if get_user_step(user_id):
        status_msg = login_cache.get(user_id, {}).get('status_msg')
        if user_id in login_cache and 'temp_client' in login_cache[user_id]:
            await login_cache[user_id]['temp_client'].disconnect()
        login_cache.pop(user_id, None)
        set_user_step(user_id, None)
        if status_msg:
            await edit_message_safely(status_msg,
                '✅ 登录过程已取消。请使用 /login 再次开始。')
        else:
            temp_msg = await message.reply(
                '✅ 登录过程已取消。请使用 /login 再次开始。')
            await temp_msg.delete(5)
    else:
        temp_msg = await message.reply('没有活动的登录过程可以取消。')
        await temp_msg.delete(5)
        
@bot.on_message(filters.command('logout'))
async def logout_command(client, message):
    user_id = message.from_user.id

    await save_user_activity(user_id, message.from_user, "/logout")

    await message.delete()
    status_msg = await message.reply('🔄 处理登出请求...')
    try:
        session_data = await get_user_data(user_id)
        
        if not session_data or 'session_string' not in session_data:
            await edit_message_safely(status_msg,
                '❌ 找不到您帐户的活动会话。')
            return
        encss = session_data['session_string']
        session_string = dcs(encss)
        temp_client = Client(f'temp_logout_{user_id}', api_id=API_ID,
            api_hash=API_HASH, session_string=session_string)
        try:
            await temp_client.connect()
            await temp_client.log_out()
            await edit_message_safely(status_msg,
                '✅ Telegram 会话成功终止。正在从数据库中删除...'
                )
        except Exception as e:
            logger.error(f'Error terminating session: {str(e)}')
            await edit_message_safely(status_msg,
                f"""⚠️ 终止 Telegram 会话时出错: {str(e)}
仍在从数据库中删除..."""
                )
        finally:
            await temp_client.disconnect()
        await remove_user_session(user_id)
        await edit_message_safely(status_msg,
            '✅ 登出成功!!')
        try:
            if os.path.exists(f"{user_id}_client.session"):
                os.remove(f"{user_id}_client.session")
        except Exception:
            pass
        if UC.get(user_id, None):
            del UC[user_id]
    except Exception as e:
        logger.error(f'Error in logout command: {str(e)}')
        try:
            await remove_user_session(user_id)
        except Exception:
            pass
        if UC.get(user_id, None):
            del UC[user_id]
        await edit_message_safely(status_msg,
            f'❌ 发生错误: {str(e)}')
        try:
            if os.path.exists(f"{user_id}_client.session"):
                os.remove(f"{user_id}_client.session")
        except Exception:
            pass
