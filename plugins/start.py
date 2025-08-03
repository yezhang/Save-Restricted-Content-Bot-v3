# Copyright (c) 2025 devgagan : https://github.com/devgaganin.  
# Licensed under the GNU General Public License v3.0.  
# See LICENSE file in the repository root for full license text.
from itertools import islice


from shared_client import app
from pyrogram import filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from utils.func import save_user_activity
from config import LOG_GROUP, OWNER_ID, FORCE_SUB

async def subscribe(app, message):
    if FORCE_SUB:
        try:
          user = await app.get_chat_member(FORCE_SUB, message.from_user.id)
          if str(user.status) == "ChatMemberStatus.BANNED":
              await message.reply_text("您已被禁止。请联系 -- https://t.me/Yezegg")
              return 1
        except UserNotParticipant:
            link = await app.export_chat_invite_link(FORCE_SUB)
            caption = f"加入我们的频道以使用机器人"
            await message.reply_photo(photo="https://graph.org/file/d44f024a08ded19452152.jpg",caption=caption, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("加入...", url=f"{link}")]]))
            return 1
        except Exception as ggn:
            await message.reply_text(f"出错了。请联系管理员并告知该信息 {ggn}")
            return 1 
     
@app.on_message(filters.command("set"))
async def set(_, message):
    if message.from_user.id not in OWNER_ID:
        await message.reply("You are not authorized to use this command.")
        return
     
    await app.set_bot_commands([
        BotCommand("start", "🚀 启动机器人"),
        # BotCommand("batch", "🫠 Extract in bulk"),
        BotCommand("single", "🫠 提取单个文件"),
        BotCommand("login", "🔑 登录你的个人机器人"),
        BotCommand("setbot", "🧸 添加你的个人机器人用来接收文件"),
        BotCommand("logout", "🚪 退出机器人"),
        # BotCommand("adl", "👻 Download audio from 30+ sites"),
        # BotCommand("dl", "💀 Download videos from 30+ sites"),
        BotCommand("status", "⟳ 刷新账户状态"),
        # BotCommand("transfer", "💘 将会员送给他人"),
        # BotCommand("add", "➕ Add user to premium"),
        # BotCommand("rem", "➖ Remove from premium"),
        BotCommand("rembot", "🤨 移除你的自定义机器人"),
        # BotCommand("settings", "⚙️ Personalize things"),
        # BotCommand("plan", "🗓️ 查看会员套餐"),
        BotCommand("terms", "🥺 服务条款"),
        BotCommand("help", "❓ 如果你是新手，仍然可以使用！"),
        BotCommand("cancel", "🚫 取消\"登录/批处理/设置\"过程"),
        BotCommand("stop", "🚫 停止批处理过程")
    ])
 
    await message.reply("✅ Commands configured successfully!")



help_pages = []


def split_iter(lst):
    mid = len(lst) // 2
    return list(islice(lst, mid)), list(islice(lst, mid, None))

def build_help_page():
    """Builds the help page with commands and descriptions."""

    cmd_settings_description = (
        "> 1. SETCHATID : To directly upload in channel or group or user's dm use it with -100[chatID]\n"
        "> 2. SETRENAME : To add custom rename tag or username of your channels\n"
        "> 3. CAPTION : To add custom caption\n"
        "> 4. REPLACEWORDS : Can be used for words in deleted set via REMOVE WORDS\n"
        "> 5. RESET : To set the things back to default\n\n"
        "> You can set CUSTOM THUMBNAIL, PDF WATERMARK, VIDEO WATERMARK, SESSION-based login, etc. from settings\n\n"
    )
    command_list = [
        # {"command": "/add userID", "description": "Add user to premium (Owner only)"},
        # {
        #     "command": "/rem userID",
        #     "description": "Remove user from premium (Owner only)",
        # },
        # {
        #     "command": "/transfer userID",
        #     "description": "Transfer premium to your beloved major purpose for resellers (Premium members only)",
        # },
        # {"command": "/get", "description": "Get all user IDs (Owner only)"},
        # {
        #     "command": "/lock",
        #     "description": "Lock channel from extraction (Owner only)",
        # },
        # {
        #     "command": "/dl link",
        #     "description": "Download videos (Not available in v3 if you are using)",
        # },
        # {
        #     "command": "/adl link",
        #     "description": "Download audio (Not available in v3 if you are using)",
        # },
        {
            "command": "/single",
            "description": "提取单个文件。先点击该命令给机器人，然后发送链接",
        },
        {
            "command": "/login",
            "description": "登录后可以访问私有频道和群组",
        },
        # {"command": "/batch", "description": "Bulk extraction for posts (After login)"},
        {"command": "/logout", "description": "退出机器人"},
        # {"command": "/stats", "description": "Get bot stats"},
        # {"command": "/plan", "description": "查看会员套餐"},
        # {
        #     "command": "/speedtest",
        #     "description": "Test the server speed (not available in v3)",
        # },
        # {"command": "/terms", "description": "Terms and conditions"},
        {"command": "/cancel", "description": "取消进行中的批处理"},
        # {"command": "/myplan", "description": "获取有关您计划的详细信息"},
        # {"command": "/session", "description": "Generate Pyrogram V2 session"},
        # {
        #     "command": "/settings",
        #     "description": cmd_settings_description,
        # },
    ]

    # 将命令列表分为数量相等的两页
    command_list_page1, command_list_page2 = split_iter(command_list)

    # 需要分为两页的帮助页面，每个页面是一个大字符串
    help_pages = []

    page1_content = ["📝 **命令清单 (1/2)**:\n\n"]
    # 将命令列表转换为帮助页面格式
    cmd_index = 1
    for cmd in command_list_page1:
        page1_content.append(
            f"{cmd_index}. **{cmd['command']}**\n> {cmd['description']}\n\n"
        )
        cmd_index += 1

    help_pages.append("".join(page1_content))

    page2_content = ["📝 **命令清单 (2/2)**:\n\n"]
    for cmd in command_list_page2:
        page2_content.append(
            f"{cmd_index}. **{cmd['command']}**\n> {cmd['description']}\n\n"
        )
        cmd_index += 1

    help_pages.append("".join(page2_content))

    return help_pages


help_pages = build_help_page()
 
 
async def send_or_edit_help_page(_, message, page_number):
    if page_number < 0 or page_number >= len(help_pages):
        return
 
     
    prev_button = InlineKeyboardButton("◀️ 上一页", callback_data=f"help_prev_{page_number}")
    next_button = InlineKeyboardButton("下一页 ▶️", callback_data=f"help_next_{page_number}")
 
     
    buttons = []
    if page_number > 0:
        buttons.append(prev_button)
    if page_number < len(help_pages) - 1:
        buttons.append(next_button)
 
     
    keyboard = InlineKeyboardMarkup([buttons])
 
     
    await message.delete()
 
     
    await message.reply(
        help_pages[page_number],
        reply_markup=keyboard
    )
 
 
@app.on_message(filters.command("help"))
async def help(client, message):

    user_id = message.from_user.id
    await save_user_activity(user_id, message.from_user, "/help")

    join = await subscribe(client, message)
    if join == 1:
        return
     
    await send_or_edit_help_page(client, message, 0)
 
 
@app.on_callback_query(filters.regex(r"help_(prev|next)_(\d+)"))
async def on_help_navigation(client, callback_query):
    action, page_number = callback_query.data.split("_")[1], int(callback_query.data.split("_")[2])
 
    if action == "prev":
        page_number -= 1
    elif action == "next":
        page_number += 1

    await send_or_edit_help_page(client, callback_query.message, page_number)
     
    await callback_query.answer()

 
@app.on_message(filters.command("terms") & filters.private)
async def terms(client, message):
    terms_text = (
        "> 📜 **条款与条件** 📜\n\n"
        "✨ 我们不对用户行为负责，也不推广受版权保护的内容。如果任何用户参与此类活动，完全由其自行承担责任。\n"
        "✨ 购买后，我们不保证计划的正常运行、停机或有效性。__用户的授权和禁令由我们自行决定；我们保留随时禁止或授权用户的权利。__\n"
        "✨ 向我们付款**__并不保证__**获得批量命令的授权。所有关于授权的决定均由我们自行决定。\n"
    )
     
    buttons = InlineKeyboardMarkup(
        [
            # [InlineKeyboardButton("📋 查看套餐", callback_data="see_plan")],
            [InlineKeyboardButton("💬 立即联系", url="https://t.me/Yezegg")],
        ]
    )
    await message.reply_text(terms_text, reply_markup=buttons)
 
 
# @app.on_message(filters.command("plan") & filters.private)
async def plan(client, message):
    plan_text = (
        "> 💰 **Premium Price**:\n\n Starting from $2 or 200 INR accepted via **__Amazon Gift Card__** (terms and conditions apply).\n"
        "📥 **Download Limit**: Users can download up to 100,000 files in a single batch command.\n"
        "🛑 **Batch**: You will get two modes /bulk and /batch.\n"
        "   - Users are advised to wait for the process to automatically cancel before proceeding with any downloads or uploads.\n\n"
        "📜 **Terms and Conditions**: For further details and complete terms and conditions, please send /terms.\n"
    )
     
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📜 查看条款", callback_data="see_terms")],
            [InlineKeyboardButton("💬 立即联系", url="https://t.me/Yezegg")],
        ]
    )
    await message.reply_text(plan_text, reply_markup=buttons)
 
 
# @app.on_callback_query(filters.regex("see_plan"))
async def see_plan(client, callback_query):
    plan_text = (
        "> 💰**Premium Price**\n\n Starting from $2 or 200 INR accepted via **__Amazon Gift Card__** (terms and conditions apply).\n"
        "📥 **Download Limit**: Users can download up to 100,000 files in a single batch command.\n"
        "🛑 **Batch**: You will get two modes /bulk and /batch.\n"
        "   - Users are advised to wait for the process to automatically cancel before proceeding with any downloads or uploads.\n\n"
        "📜 **Terms and Conditions**: For further details and complete terms and conditions, please send /terms or click See Terms👇\n"
    )
     
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📜 See Terms", callback_data="see_terms")],
            [InlineKeyboardButton("💬 Contact Now", url="https://t.me/Yezegg")],
        ]
    )
    await callback_query.message.edit_text(plan_text, reply_markup=buttons)
 
 
# @app.on_callback_query(filters.regex("see_terms"))
async def see_terms(client, callback_query):
    terms_text = (
        "> 📜 **Terms and Conditions** 📜\n\n"
        "✨ We are not responsible for user deeds, and we do not promote copyrighted content. If any user engages in such activities, it is solely their responsibility.\n"
        "✨ Upon purchase, we do not guarantee the uptime, downtime, or the validity of the plan. __Authorization and banning of users are at our discretion; we reserve the right to ban or authorize users at any time.__\n"
        "✨ Payment to us **__does not guarantee__** authorization for the /batch command. All decisions regarding authorization are made at our discretion and mood.\n"
    )
     
    buttons = InlineKeyboardMarkup(
        [
            [InlineKeyboardButton("📋 See Plans", callback_data="see_plan")],
            [InlineKeyboardButton("💬 Contact Now", url="https://t.me/Yezegg")],
        ]
    )
    await callback_query.message.edit_text(terms_text, reply_markup=buttons)
 
 
