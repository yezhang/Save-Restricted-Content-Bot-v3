# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.

import os, re, time, asyncio, json, asyncio 
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import UserNotParticipant
from config import API_ID, API_HASH, LOG_GROUP, STRING, FORCE_SUB, FREEMIUM_LIMIT, PREMIUM_LIMIT
from utils.func import get_user_data, screenshot, thumbnail, get_video_metadata
from utils.func import get_user_data_key, process_text_with_rules, is_premium_user, extract_chat_and_message_id
from utils.func import is_user_free_limit_exceeded, update_user_free_quota_usage
from utils.func import add_download_record, save_user_activity
from shared_client import app as X
from plugins.settings import rename_file
from plugins.start import subscribe as sub
from utils.custom_filters import login_in_progress
from utils.encrypt import dcs
from typing import Dict, Any, Optional

import logging
logging.basicConfig(format=
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger('bot-batch')


Y = None if not STRING else __import__('shared_client').userbot
Z, P, UB, UC, emp = {}, {}, {}, {}, {}

ACTIVE_USERS = {}
ACTIVE_USERS_FILE = "active_users.json"

# fixed directory file_name problems 
def sanitize(filename):
    return re.sub(r'[<>:"/\\|?*\']', '_', filename).strip(" .")[:255]

def load_active_users():
    try:
        if os.path.exists(ACTIVE_USERS_FILE):
            with open(ACTIVE_USERS_FILE, 'r') as f:
                return json.load(f)
        return {}
    except Exception:
        return {}

async def save_active_users_to_file():
    try:
        with open(ACTIVE_USERS_FILE, 'w') as f:
            json.dump(ACTIVE_USERS, f)
    except Exception as e:
        print(f"Error saving active users: {e}")

async def add_active_batch(user_id: int, batch_info: Dict[str, Any]):
    ACTIVE_USERS[str(user_id)] = batch_info
    await save_active_users_to_file()

def is_user_active(user_id: int) -> bool:
    return str(user_id) in ACTIVE_USERS

async def update_batch_progress(user_id: int, current: int, success: int):
    if str(user_id) in ACTIVE_USERS:
        ACTIVE_USERS[str(user_id)]["current"] = current
        ACTIVE_USERS[str(user_id)]["success"] = success
        await save_active_users_to_file()

async def request_batch_cancel(user_id: int):
    if str(user_id) in ACTIVE_USERS:
        ACTIVE_USERS[str(user_id)]["cancel_requested"] = True
        await save_active_users_to_file()
        return True
    return False

def should_cancel(user_id: int) -> bool:
    user_str = str(user_id)
    return user_str in ACTIVE_USERS and ACTIVE_USERS[user_str].get("cancel_requested", False)

async def remove_active_batch(user_id: int):
    if str(user_id) in ACTIVE_USERS:
        del ACTIVE_USERS[str(user_id)]
        await save_active_users_to_file()

def get_batch_info(user_id: int) -> Optional[Dict[str, Any]]:
    return ACTIVE_USERS.get(str(user_id))

ACTIVE_USERS = load_active_users()

async def upd_dlg(c):
    try:
        async for _ in c.get_dialogs(limit=100): pass
        return True
    except Exception as e:
        print(f'Failed to update dialogs: {e}')
        return False

# fixed the old group of 2021-2022 extraction 🌝 (buy krne ka fayda nhi ab old group) ✅ 
async def get_msg(user_bot, user_client, i, d, link_type):
    """Fetch messages from a chat.

    Args:
        user_bot (pyrogram.Client): 用户绑定的个人机器人，如果没有绑定个人机器人，则使用官方机器人。
        user_client (pyrogram.Client): 每个登录用户的客户端。
        i (str): The chat ID or username.
        d (int): The message ID to start fetching from.
        link_type (str): The type of chat ('public' or 'private').

    Returns:
        Optional[Message]: The fetched message or None if not found.
    """
    try:
        if link_type == 'public':
            try:
                if str(i).lower().endswith('bot'):
                    emp[i] = False
                    ## 通过
                    xm = await user_client.get_messages(i, d)
                    emp[i] = getattr(xm, "empty", False)
                    if not emp[i]:
                        emp[i] = True
                        print(f"Bot chat found successfully...")
                        return xm

                ## 先尝试通过个人机器人获取消息（如果个人机器人已经绑定群组）
                xm = await user_bot.get_messages(i, d)
                logger.info(f"fetched by {user_bot.me.username}")

                ## message.empty 属性：
                # The message is empty. A message can be empty in case it was deleted or you tried to retrieve a message that doesn’t exist yet.
                
                # 用法：process_msg 中会根据 `not emp.get(i, False)` 来转发信息。
                emp[i] = getattr(xm, "empty", False)
                if emp[i]:
                    logger.info(f"Not fetched by {user_bot.me.username}")
                    try: 
                        ## 尝试通过个人客户端获取消息
                        chat_obj = await user_client.join_chat(i)
                        chat_id = chat_obj.id if hasattr(chat_obj, 'id') else None
                    except Exception as e:
                        logger.error(f"Error joining chat {i}: {e}")
                        pass
                    
                    if not chat_id:
                        chat_obj = await user_client.get_chat(f"{i}")
                        chat_id = chat_obj.id if hasattr(chat_obj, 'id') else None
                    
                    xm = await user_client.get_messages(chat_id, d)
                    emp[i] = getattr(xm, "empty", False)

                    logger.info(f"message.empty: {emp[i]}")
                
                return xm    
            except Exception as e:
                logger.error(f'Error fetching public message: {e}')
                return None
        else:
            if user_client:
                try:
                    async for _ in user_client.get_dialogs(limit=50): pass
                    
                    # Try with -100 prefix first
                    if str(i).startswith('-100'):
                        chat_id_100 = i
                        # For - prefix, remove -100 and add just -
                        base_id = str(i)[4:]  # Remove -100
                        chat_id_dash = f"-{base_id}"
                    elif i.isdigit():
                        chat_id_100 = f"-100{i}"
                        chat_id_dash = f"-{i}"
                    else:
                        chat_id_100 = i
                        chat_id_dash = i
                    
                    # Try -100 format first
                    try:
                        result = await user_client.get_messages(chat_id_100, d)
                        if result and not getattr(result, "empty", False):
                            return result
                    except Exception:
                        pass
                    
                    # Try - format second
                    try:
                        result = await user_client.get_messages(chat_id_dash, d)
                        if result and not getattr(result, "empty", False):
                            return result
                    except Exception:
                        pass
                    
                    # Final fallback - refresh dialogs and try original
                    try:
                        async for _ in user_client.get_dialogs(limit=200): pass
                        result = await user_client.get_messages(i, d)
                        if result and not getattr(result, "empty", False):
                            return result
                    except Exception:
                        pass
                    
                    return None
                            
                except Exception as e:
                    print(f'Private channel error: {e}')
                    return None
            return None
    except Exception as e:
        print(f'Error fetching message: {e}')
        return None


async def get_ubot(uid):
    """查询用户对应的个人机器人客户端

    Args:
        uid (_type_): _description_

    Returns:
        pyrogram.Client: 个人机器人客户端实例
    """
    bt = await get_user_data_key(uid, "bot_token", None)
    if not bt: return None
    if uid in UB: return UB.get(uid)
    try:
        bot = Client(f"user_{uid}", bot_token=bt, api_id=API_ID, api_hash=API_HASH)
        await bot.start()
        UB[uid] = bot
        return bot
    except Exception as e:
        print(f"Error starting bot for user {uid}: {e}")
        return None

async def get_uclient(uid):
    """查询用户的 client（对应每个实际登录的用户）

    Args:
        uid (_type_): _description_

    Returns:
        pyrogram.Client: 用户登录的客户端实例 或 共享 Telegram 客户端实例
    """
    ud = await get_user_data(uid)
    ubot = UB.get(uid)
    cl = UC.get(uid)
    if cl: return cl
    if not ud: return ubot if ubot else None
    xxx = ud.get('session_string')
    if xxx:
        try:
            ss = dcs(xxx)
            gg = Client(f'{uid}_client', api_id=API_ID, api_hash=API_HASH, device_model="v3saver", session_string=ss)
            await gg.start()
            await upd_dlg(gg)
            UC[uid] = gg
            return gg
        except Exception as e:
            print(f'User client error: {e}')
            return ubot if ubot else Y
    return Y

async def prog(c, t, C, h, m, st):
    global P
    p = c / t * 100
    interval = 10 if t >= 100 * 1024 * 1024 else 20 if t >= 50 * 1024 * 1024 else 30 if t >= 10 * 1024 * 1024 else 50
    step = int(p // interval) * interval
    if m not in P or P[m] != step or p >= 100:
        P[m] = step
        c_mb = c / (1024 * 1024)
        t_mb = t / (1024 * 1024)
        bar = '🟢' * int(p / 10) + '🔴' * (10 - int(p / 10))
        speed = c / (time.time() - st) / (1024 * 1024) if time.time() > st else 0
        eta = time.strftime('%M:%S', time.gmtime((t - c) / (speed * 1024 * 1024))) if speed > 0 else '00:00'
        await C.edit_message_text(h, m, f"__**处理中...**__\n\n{bar}\n\n⚡**__进度__**: {c_mb:.2f} MB / {t_mb:.2f} MB\n📊 **__百分比__**: {p:.2f}%\n🚀 **__速度__**: {speed:.2f} MB/s\n⏳ **__剩余时间__**: {eta}\n\n**__Powered by @baicaoyuan_001__**")
        if p >= 100: P.pop(m, None)

async def send_direct(c, m, tcid, ft=None, rtmid=None):
    try:
        if m.video:
            await c.send_video(tcid, m.video.file_id, caption=ft, duration=m.video.duration, width=m.video.width, height=m.video.height, reply_to_message_id=rtmid)
        elif m.video_note:
            await c.send_video_note(tcid, m.video_note.file_id, reply_to_message_id=rtmid)
        elif m.voice:
            await c.send_voice(tcid, m.voice.file_id, reply_to_message_id=rtmid)
        elif m.sticker:
            await c.send_sticker(tcid, m.sticker.file_id, reply_to_message_id=rtmid)
        elif m.audio:
            await c.send_audio(tcid, m.audio.file_id, caption=ft, duration=m.audio.duration, performer=m.audio.performer, title=m.audio.title, reply_to_message_id=rtmid)
        elif m.photo:
            photo_id = m.photo.file_id if hasattr(m.photo, 'file_id') else m.photo[-1].file_id
            await c.send_photo(tcid, photo_id, caption=ft, reply_to_message_id=rtmid)
        elif m.document:
            await c.send_document(tcid, m.document.file_id, caption=ft, file_name=m.document.file_name, reply_to_message_id=rtmid)
        else:
            return False
        return True
    except Exception as e:
        logger.error(f'Direct send error: {e}')
        return False

async def process_msg(c, u, m, d, lt, uid, i, msg_link):
    '''
    Process a message and send it to the specified chat.
    Args:
    - c: userbot，每个用户绑定一个
    - u: user client, 每个用户有一个客户端（使用用户的 session string 登录），pyrogram.Client
    - m: 获取的消息实体（即一个link对应的消息内容）
    - d: 消息 id
    - lt: 消息的访问类型 (e.g., 'public', 'private').
    - uid: 与机器人交互的用户 id
    - i: 消息所在的 chat id
    '''
    try:
        cfg_chat = await get_user_data_key(d, 'chat_id', None)
        tcid = d
        rtmid = None
        if cfg_chat:
            if '/' in cfg_chat:
                parts = cfg_chat.split('/', 1)
                tcid = int(parts[0])
                rtmid = int(parts[1]) if len(parts) > 1 else None
            else:
                tcid = int(cfg_chat)
        
        if m.media:
            logger.info('找到消息中的媒体资源')

            orig_text = m.caption.markdown if m.caption else ''
            proc_text = await process_text_with_rules(d, orig_text)
            user_cap = await get_user_data_key(d, 'caption', '')
            ft = f'{proc_text}\n\n{user_cap}' if proc_text and user_cap else user_cap if user_cap else proc_text
            
            if lt == 'public' and not emp.get(i, False):
                if not (await send_direct(c, m, tcid, ft, rtmid)):
                    # 如果个人机器人发送失败，则使用用户客户端发送
                    # 发送失败时，可能会遇到 400 MEDIA_EMPTY 错误，这可能是因为 file_id 是绑定生成的账户的
                    send_is_success = await send_direct(u, m, tcid, ft, rtmid) 
                    if send_is_success:
                        return '已直接发送'
                    else:
                        pass # 使用下载方法继续处理
            
            if m.video:
                if m.video.file_size:
                    if m.video.file_size > 2 * 1024 * 1024 * 1024: # 大于2GB
                        return '文件大于2GB，无法处理。请联系管理员 @Yezegg。'
            
            st = time.time()

            logger.info('给用户发送消息，提示下载：下载中...')
            p = await c.send_message(d, '下载中...')

            msg_name = f"{lt}{i}_{d}"
            # c_name = f"{time.time()}"
            c_name = msg_name

            if m.video:
                file_name = m.video.file_name
                if not file_name:
                    file_name = f"{msg_name}.mp4"
                c_name = sanitize(file_name)
            elif m.audio:
                file_name = m.audio.file_name
                if not file_name:
                    file_name = f"{msg_name}.mp3"
                c_name = sanitize(file_name)
            elif m.document:
                file_name = m.document.file_name
                if not file_name:
                    file_name = f"{msg_name}"
                c_name = sanitize(file_name)
            elif m.photo:
                file_name = m.photo.file_id # photo 没有 file_name 属性
                if not file_name:
                    file_name = f"{msg_name}.jpg"
                c_name = sanitize(file_name)
    
            logger.info(f'下载媒体(download_media), {c_name}')

            # 如果文件已存在，直接使用已存在的文件缓存
            if os.path.exists(c_name):
                logger.info(f'文件 {c_name} 已存在，直接使用')
                f = c_name
            else:
                f = await u.download_media(m, file_name=c_name, progress=prog, progress_args=(c, d, p.id, st))
            
            if not f:
                await c.edit_message_text(d, p.id, '失败.')
                return '失败.'

            await c.edit_message_text(d, p.id, '重命名中...')
            if (
                (m.video and m.video.file_name) or
                (m.audio and m.audio.file_name) or
                (m.document and m.document.file_name)
            ):
                f = await rename_file(f, d, p)
            
            fsize_byte = os.path.getsize(f)
            fsize = fsize_byte / (1024 * 1024 * 1024) # 转换为 GB
            th = thumbnail(d)
            
            if fsize > 2 and Y:
                st = time.time()
                await c.edit_message_text(d, p.id, '文件大于2GB，使用替代方法...')
                await upd_dlg(Y)
                mtd = await get_video_metadata(f)
                dur, w, h = mtd['duration'], mtd['width'], mtd['height']
                th = await screenshot(f, dur, d)
                
                send_funcs = {'video': Y.send_video, 'video_note': Y.send_video_note, 
                            'voice': Y.send_voice, 'audio': Y.send_audio, 
                            'photo': Y.send_photo, 'document': Y.send_document}
                
                for mtype, func in send_funcs.items():
                    if f.endswith('.mp4'): 
                        mtype = 'video'
                    if getattr(m, mtype, None):
                        sent = await func(LOG_GROUP, f, thumb=th if mtype == 'video' else None, 
                                        duration=dur if mtype == 'video' else None,
                                        height=h if mtype == 'video' else None,
                                        width=w if mtype == 'video' else None,
                                        caption=ft if m.caption and mtype not in ['video_note', 'voice'] else None, 
                                        reply_to_message_id=rtmid, progress=prog, progress_args=(c, d, p.id, st))
                        break
                else:
                    logger.info('使用 send_document 发送大文件')
                    sent = await Y.send_document(LOG_GROUP, f, thumb=th, caption=ft if m.caption else None,
                                                reply_to_message_id=rtmid, progress=prog, progress_args=(c, d, p.id, st))
                
                await c.copy_message(d, LOG_GROUP, sent.id)
                os.remove(f)
                await c.delete_messages(d, p.id)
                
                return 'Done (Large file).'
            
            await c.edit_message_text(d, p.id, '发送中...')
            st = time.time()

            try:
                if m.video or os.path.splitext(f)[1].lower() == '.mp4':
                    mtd = await get_video_metadata(f)
                    dur, w, h = mtd['duration'], mtd['width'], mtd['height']
                    th = await screenshot(f, dur, d)
                    await c.send_video(tcid, video=f, caption=ft if m.caption else None, 
                                    thumb=th, width=w, height=h, duration=dur, 
                                    progress=prog, progress_args=(c, d, p.id, st), 
                                    reply_to_message_id=rtmid)
                elif m.video_note:
                    await c.send_video_note(tcid, video_note=f, progress=prog, 
                                        progress_args=(c, d, p.id, st), reply_to_message_id=rtmid)
                elif m.voice:
                    await c.send_voice(tcid, f, progress=prog, progress_args=(c, d, p.id, st), 
                                    reply_to_message_id=rtmid)
                elif m.sticker:
                    await c.send_sticker(tcid, m.sticker.file_id)
                elif m.audio:
                    await c.send_audio(tcid, audio=f, caption=ft if m.caption else None, 
                                    thumb=th, progress=prog, progress_args=(c, d, p.id, st), 
                                    reply_to_message_id=rtmid)
                elif m.photo:
                    await c.send_photo(tcid, photo=f, caption=ft if m.caption else None, 
                                    progress=prog, progress_args=(c, d, p.id, st), 
                                    reply_to_message_id=rtmid)
                else:
                    await c.send_document(tcid, document=f, caption=ft if m.caption else None, 
                                        progress=prog, progress_args=(c, d, p.id, st), 
                                        reply_to_message_id=rtmid)
            except Exception as e:
                await c.edit_message_text(d, p.id, f'发送失败: {str(e)[:30]}')
                if os.path.exists(f): os.remove(f)
                return '失败.'
            
            # 更新用户的免费下载配额，高级用户不用更新免费配额
            if not await is_premium_user(uid):
                await update_user_free_quota_usage(uid, fsize_byte)
            
            # 添加下载记录
            await add_download_record(uid, msg_link, fsize_byte)

            os.remove(f)
            await c.delete_messages(d, p.id)
            
            
            return '已完成.'
            
        elif m.text:
            await c.send_message(tcid, text=m.text.markdown, reply_to_message_id=rtmid)
            return '已发送。'
    except Exception as e:
        logger.error(f'Error processing message: {e}')
        return f'Error: {str(e)[:37]}. 请联系管理员 @Yezegg。'

@X.on_message(filters.incoming & filters.command(['batch', 'single']))
async def process_cmd(c, m):
    uid = m.from_user.id
    cmd = m.command[0]

    await save_user_activity(uid, m.from_user, f"/{cmd}")

    # 查询用户的套餐身份
    if not await is_premium_user(uid):
        # /batch 命令没有免费额度
        if cmd == 'batch':
            await m.reply_text("免费用户无法使用 /batch 命令。请联系管理员 @Yezegg 了解更多信息。")
            return
        # 免费用户限制
        if await is_user_free_limit_exceeded(uid):
            await m.reply_text(f'您的免费用户下载次数或文件大小已用完（可以等第二天恢复）。可以使用 /status 查询状态。请联系管理员 @Yezegg 了解更多信息。')
            return

    # if FREEMIUM_LIMIT == 0 and not await is_premium_user(uid):
    #     await m.reply_text("This bot does not provide free servies, get subscription from OWNER")
    #     return
    
    if await sub(c, m) == 1: return
    pro = await m.reply_text('正在进行一些检查，请稍候...')
    
    if is_user_active(uid):
        await pro.edit('您有一个活动任务。使用 /stop 取消它。')
        return
    
    # ubot = await get_ubot(uid)
    # if not ubot:
    #     await pro.edit('请先使用 /setbot 添加您的机器人')
    #     return
    
    Z[uid] = {'step': 'start' if cmd == 'batch' else 'start_single'}
    await pro.edit(f'发送 {"第一个链接..." if cmd == "batch" else "链接（link）……"}.')

@X.on_message(filters.incoming & filters.command(['stopbatch']))
async def stop_batch_cmd(c, m):
    uid = m.from_user.id

    await save_user_activity(uid, m.from_user, "/stopbatch")

    if is_user_active(uid):
        if await request_batch_cancel(uid):
            await m.reply_text('Cancellation requested. The current batch will stop after the current download completes.')
        else:
            await m.reply_text('Failed to request cancellation. Please try again.')
    else:
        await m.reply_text('No active batch process found.')

@X.on_message(filters.text & filters.private & filters.incoming & ~login_in_progress & ~filters.command([
    'start', 'batch', 'cancel', 'login', 'logout', 'stopbatch', 'set', 
    'pay', 'redeem', 'gencode', 'single', 'generate', 'keyinfo', 'encrypt', 'decrypt', 'keys', 'setbot', 'rembot']))
async def text_handler(c, m):
    uid = m.from_user.id

    await save_user_activity(uid, m.from_user, "text_handler", {"text": m.text})

    if uid not in Z: return
    s = Z[uid].get('step')

    if s == 'start':
        L = m.text
        i, d, lt = extract_chat_and_message_id(L)
        if not i or not d:
            await m.reply_text('无效的链接格式。')
            Z.pop(uid, None)
            return
        Z[uid].update({'step': 'count', 'cid': i, 'sid': d, 'lt': lt})
        await m.reply_text('您想提取多少条消息？')

    elif s == 'start_single':
        L = m.text
        i, d, lt = extract_chat_and_message_id(L)
        if not i or not d:
            await m.reply_text('无效的链接格式。')
            Z.pop(uid, None)
            return

        Z[uid].update({'step': 'process_single', 'cid': i, 'sid': d, 'lt': lt})
        i, s, lt = Z[uid]['cid'], Z[uid]['sid'], Z[uid]['lt']
        pt = await m.reply_text('正在处理...')
        
        ubot = UB.get(uid)
        
        # if not ubot:
        #     await pt.edit('请使用 /setbot 添加您的机器人')
        #     Z.pop(uid, None)
        #     return
        if not ubot:
            ubot = X # 不使用个人机器人，直接使用官方入口机器人
        
        uc = await get_uclient(uid)
        if not uc:
            await pt.edit('无法在没有用户客户端的情况下继续。请使用 /login 登录您的账号。')
            Z.pop(uid, None)
            return
            
        if is_user_active(uid):
            await pt.edit('存在活动任务。请先使用 /stop。')
            Z.pop(uid, None)
            return

        try:
            msg = await get_msg(ubot, uc, i, s, lt)

            logger.info(f'Processing message: msg.id={msg.id}, msg.media={msg.media}, msg.chat.id={msg.chat.id}')
            if msg:
                res = await process_msg(ubot, uc, msg, str(m.chat.id), lt, uid, i)
                await pt.edit(f'1/1: {res}')
            else:
                await pt.edit('消息资源未找到')
        except Exception as e:
            await pt.edit(f'错误（请先通过 /login 登录您的账号）: {str(e)[:50]}')
        finally:
            Z.pop(uid, None)

    elif s == 'count':
        if not m.text.isdigit():
            await m.reply_text('请输入有效数字。')
            return
        
        count = int(m.text)
        maxlimit = PREMIUM_LIMIT if await is_premium_user(uid) else FREEMIUM_LIMIT

        if count > maxlimit:
            await m.reply_text(f'最大限制是 {maxlimit}.')
            return

        Z[uid].update({'step': 'process', 'did': str(m.chat.id), 'num': count})
        i, s, n, lt = Z[uid]['cid'], Z[uid]['sid'], Z[uid]['num'], Z[uid]['lt']
        success = 0

        pt = await m.reply_text('正在批量处理...')
        uc = await get_uclient(uid)
        ubot = UB.get(uid)
        
        if not uc or not ubot:
            await pt.edit('Missing client setup')
            Z.pop(uid, None)
            return
            
        if is_user_active(uid):
            await pt.edit('Active task exists')
            Z.pop(uid, None)
            return
        
        await add_active_batch(uid, {
            "total": n,
            "current": 0,
            "success": 0,
            "cancel_requested": False,
            "progress_message_id": pt.id
            })
        
        try:
            for j in range(n):
                
                if should_cancel(uid):
                    await pt.edit(f'取消位置 {j}/{n}. 成功: {success}')
                    break
                
                await update_batch_progress(uid, j, success)
                
                mid = int(s) + j
                
                try:
                    msg = await get_msg(ubot, uc, i, mid, lt)
                    if msg:
                        # Message.link 属性：Generate a link to this message, only for groups and channels.
                        res = await process_msg(ubot, uc, msg, str(m.chat.id), lt, uid, i, msg.link)
                        if '完成' in res or 'Copied' in res or '发送' in res:
                            success += 1
                    else:
                        pass
                except Exception as e:
                    try: await pt.edit(f'{j+1}/{n}: Error - {str(e)[:30]}')
                    except: pass
                
                await asyncio.sleep(10)
            
            if j+1 == n:
                await m.reply_text(f'已完成批量处理 ✅ 成功: {success}/{n}')

        finally:
            await remove_active_batch(uid)
            Z.pop(uid, None)
