import json
import os
import aiohttp
import re
import asyncio
from nonebot import on_message, logger,get_driver
import nonebot
from nonebot.adapters.onebot.v11 import Message, MessageEvent, Bot, GroupMessageEvent, PrivateMessageEvent
from nonebot.exception import ActionFailed
from nonebot import require,on_metaevent
from nonebot.rule import to_me
from datetime import datetime, timedelta

from plugins.Emoji.emojis import EmojiManager
from plugins.AI_talk.ai_talk import AiManager
from plugins.Task.task import ScheduledMessage
from plugins.Task.execute import *

from nonebot.exception import NetworkError


# 私聊的QQ号
ALLOWED_PRIVATE_QQ = [1657172041,2740954024]

# 表情包存储的JSON文件路径
EMOJI_JSON_PATH = "emojis.json"

# 只有群聊被@或者指定QQ私聊时触发
chat = on_message(
    priority=99,
    block=False,
    rule=lambda event: (
        (isinstance(event, GroupMessageEvent) and event.is_tome()) or
        (isinstance(event, PrivateMessageEvent) and event.user_id in ALLOWED_PRIVATE_QQ)
    )
)

class MainWalk:
    def __init__(self):
        
        nonebot.load_plugins("AI_talk.ai_talk")
        nonebot.load_plugins("Emoji.emojis")
        nonebot.logger.info("插件加载完成，开始运行")
        self.emoji_manager = EmojiManager()
        self.ai_manager = AiManager()

    

    async def get_mes_deal(self, user_msg, bot: Bot, event: MessageEvent):  # 改为 async
        if user_msg.startswith("保存 "):
            await self.save_emojis(user_msg, bot, event)  # 添加 await
        else:
            await self.send_talk(user_msg, bot, event)  # 添加 await

    async def save_emojis(self, user_msg, bot: Bot, event: MessageEvent):
        for attempt in range(3):  # 重试3次
            try:
                # 提取备注、图片CQ码和是否压缩
                match_remark = re.match(r"保存\s+([\s\S]+?)(?:\[CQ:image.*?\])(?:\s*压缩)?$", user_msg)
                match_file = re.search(r'\[CQ:image,file=([^,\]]+)', user_msg)
                compress = "压缩" in user_msg  # 检查是否要求压缩
                if match_remark and match_file:
                    remark = match_remark.group(1).strip()
                    file_id = match_file.group(1)  # 获取 CQ:image 的 file 参数

                    # 下载图片
                    local_path = None
                    try:
                        # 尝试使用 bot.get_image 获取图片 URL
                        logger.debug(f"尝试获取图片: file_id={file_id}")
                        image_info = await bot.get_image(file=file_id)
                        image_url = image_info.get("url")
                        if not image_url:
                            await bot.send(event, Message("喵~获取图片信息失败了，可能是权限问题哦~"))
                            return

                        # 下载图片到本地
                        async with aiohttp.ClientSession() as session:
                            async with session.get(image_url, timeout=10) as resp:
                                if resp.status != 200:
                                    await bot.send(event, Message("喵~下载图片失败了，稍后再试哦~"))
                                    return
                                # 保存到本地
                                file_ext = os.path.splitext(image_url)[1] or ".png"
                                file_name = f"{remark}_{int(event.time)}{file_ext}"
                                local_path = os.path.join(self.emoji_manager.emoji_file_path, file_name)
                                with open(local_path, "wb") as f:
                                    f.write(await resp.read())
                                logger.debug(f"图片下载成功: {local_path}")
                    except (ActionFailed, NetworkError) as e:
                        logger.error(f"获取图片信息失败: {e}")
                        await bot.send(event, Message("喵~获取图片信息失败了，检查协议端配置哦~"))
                        return
                    except Exception as e:
                        logger.error(f"下载图片失败: {e}")
                        await bot.send(event, Message("喵~下载图片失败了，检查网络或权限哦~"))
                        return

                    # 保存到 EmojiManager
                    if self.emoji_manager.save_user_emoji(local_path, remark, compress=compress):
                        try:
                            await bot.send(event, f"保存成功~{'（已压缩）' if compress else ''}")
                            await bot.send(event, "喵~图片已保存到本地，再也不怕失效啦~")
                        except ActionFailed as e:
                            logger.warning(f"发送文本消息失败: {e}, 尝试简化为纯文本")
                            await bot.send(event, Message("保存成功！图片已保存到本地~"))
                    else:
                        await bot.send(event, Message("喵~这个表情包已经保存过了哦！"))
                else:
                    await bot.send(event, Message("喵~保存格式不对呢，应该是‘保存 备注[CQ:image...] [压缩]’哦~"))
                return
            except ActionFailed as e:
                logger.error(f"发送保存回复失败: {e}，第 {attempt + 1} 次重试哦~")
                if attempt < 2:
                    await asyncio.sleep(2)
                else:
                    await bot.send(event, Message("喵~保存回复发送失败了，可能是风控或协议端问题哦，稍后再试呢~"))
                    return
            except Exception as e:
                logger.error(f"保存表情包失败: {e}")
                await bot.send(event, Message("喵~保存表情包失败了，稍后再试哦！"))
                return

    async def send_talk(self, user_msg, bot: Bot, event: MessageEvent):
        chat_id = f"user_{event.user_id}"
        # 正常消息处理
        reply = await self.ai_manager.chat(chat_id, user_msg)
        try:
            sentences = self.ai_manager.slice_talk(reply)
            for sentence in sentences:
                await bot.send(event, Message(sentence))
                await asyncio.sleep(1)
            if sentences:
                try:
                    # 根据回复内容选择最匹配的表情包
                    final_emoji = self.emoji_manager.find_best_emoji(reply)
                    await bot.send(event, final_emoji)  # 直接发送 MessageSegment
                except ActionFailed as e:
                    logger.error(f"发送表情包失败了呢: {e}，别生气哦~")
                    await bot.send(event, Message("喵~表情包好像发不出去，稍后再试哦！"))
        except ActionFailed as e:
            logger.error(f"发送消息失败了呢: {e}，别生气哦~")
            await bot.send(event, Message("喵~我好像被QQ拦住了，检查下我的权限哦！"))
        except Exception as e:
            logger.error(f"发送消息出错了呢: {e}，别怪我哦~")
            await bot.send(event, Message("喵~我好像出错了，等等我好不好~"))

main_bot = MainWalk()

# 在 NoneBot 启动时初始化 ScheduledMessage 并启动调度器
scheduled_message = ScheduledMessage()



@chat.handle()
async def handle_chat(bot: Bot, event: MessageEvent):
    user_msg = str(event.get_message()).strip()
    logger.debug(f"收到你的消息啦: {user_msg}，是不是很棒~")
    await main_bot.get_mes_deal(user_msg, bot, event)


# # 监听 Bot 连接事件（通过 meta_event 的 connect 类型）
# bot_connect = on_metaevent()
# # 在 Bot 连接时安排测试任务
# @bot_connect.handle()
# async def schedule_test_task(bot: Bot):
#     if not scheduled_message.running:
#         scheduled_message.scheduler.start()
#         scheduled_message.running = True
#         logger.info("定时任务调度器已启动")


#     test_qq_number = "2740954024"  # 测试用 QQ 号（在 ALLOWED_PRIVATE_QQ 中）
#     send_time = datetime.now() + timedelta(minutes=1)  # 1 分钟后发送
#     await scheduled_message.schedule_message(test_qq_number, send_time)
#     logger.info(f"测试任务已安排: 在 {send_time} 向 {test_qq_number} 发送消息")
   