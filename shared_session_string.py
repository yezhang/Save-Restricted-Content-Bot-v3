# 源码地址：https://replit.com/@AssadAli/String-Session-Generator?forkRepl=d3685031-0c6f-4dc5-98c4-ef6836c4c5f9&forkContext=coverPage&redirecting=1#main.py

import os
import pyrogram

os.system('clear')


API_ID = '25449359' #input("Enter your API_ID : ")
API_HASH = 'b7c580efea9a931d9c40a479baa558b0' #input("Enter your API_HASH : ")

pyrogram_proxy = {
    "scheme": "socks5",  # 可以是 "http", "https", "socks4", "socks5"
    "hostname": "127.0.0.1",
    "port": 7890,
}

# system_version=4.16.30-vxCUSTOMBot
client = pyrogram.Client("temp_session", 
                        #  proxy=pyrogram_proxy,
                         api_id=API_ID, 
                         api_hash=API_HASH,
                         device_model="SaverSession", 
                         in_memory=True, # =True, 将会在内存中保存会话字符串，不会生成 .session 文件
                         phone_number='+8613401157658', # 手机号，避免手动输入
                         password='qiounosahaqi') # 密码，避免手动输入

async def main():
    async with client:
        session_str = await client.export_session_string()
        me = await client.get_me()
        fname = me.first_name
        print(f"SessionString 1: {fname}")
        print(session_str)
        

client.run(main())

## session string
## BQGEU48AEcIqU0HrndF5Zps7abM2bJnETN4Q0vQOR55XJihuaurEscJk82liv9LKv5AkkILNr9S2YvyEse9P9h9dBf3bLeO7jeHDDLm4JNVPjUGiQflU1gz9LrU1j500Gjg93CB9CJWzoRiC9oH-UP6yi5QGf4ip4Bes6qGB0W5XDzeDAMiEOT-Flva_s_RXOUyVqRxm0u0r3ghvjSZXHEORvewZN9OkClATzxXKrW3tP1KWyeMX0FZr1bKaaVCh8uT_p8La1ea9BjTYbx5ed8xKoYJo_nN2RxrxsmiFWjyKK3GnBc_ne-mmzYD7RnZBXZ_90qby3poHkj78kg9y2cUgdPelOwAAAAA7RK65AA