import logging

from pyrogram import Client, filters
from pyrogram import errors

from shared_client import app

logging.basicConfig(format=
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger('bot-errors')


@app.on_error()
async def global_error_handler(client, error):
    error_type = type(error).__name__
    error_code = getattr(error, "CODE", None)
    error_id = getattr(error, "ID", None)
    error_name = getattr(error, "NAME", None)
    error_id_or_name = error_id or error_name or "Unknown"
    error_msg = error.MESSAGE if hasattr(error, "MESSAGE") else str(error)
    logger.error(f"捕获异常: {error_type} | 错误代码: {error_code} | 错误ID/名称: {error_id_or_name} | 详情: {error_msg}")
    # 可扩展：记录日志或发送警报到指定渠道