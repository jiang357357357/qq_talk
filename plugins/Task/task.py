import asyncio
import os
import json
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from nonebot import logger,get_bot
from plugins.AI_talk.gpt_text import lovel_text, high_white  # 导入预定义文本
from plugins.AI_talk.ai_talk import AiManager  # 导入 AiManager 类

print("task部件载入完成")

class ScheduledMessage:
    def __init__(self):
        # 动态设置根路径
        self.is_windows = os.name == "nt"
        self.base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) if self.is_windows else "/home/web/qq_ai"
        # 初始化 AI 管理器
        self.ai_manager = AiManager()
        # 初始化定时任务调度器
        self.scheduler = AsyncIOScheduler()
        self.running = False

    async def generate_message(self, qq_number: str,user_text):
        # 根据用户的聊天记录生成消息
        try:
            # 加载用户的聊天记录
            chat_id = f"user_{qq_number}"  # 使用 QQ 号作为 chat_id
            messages = self.ai_manager.load_messages(chat_id)
            # 添加一个默认用户输入，触发 AI 回复
            prompt = user_text
            messages.append({"role": "user", "content": prompt})
            reply = await self.ai_manager.get_text(messages)
            messages.append({"role": "assistant", "content": reply})
            # 保存更新后的聊天记录
            self.ai_manager.save_messages(chat_id, messages)
            return reply
        except Exception as e:
            logger.error(f"生成消息失败: {e}")
            return "喵~我踩到尾巴了，稍后再试哦！"

    async def send_and_store_message(self, bot, qq_number: str,user_text):
        # 发送消息并保存到聊天记录
        try:

            # 生成消息
            message = await self.generate_message(qq_number,user_text)
            # 发送消息
            await bot.send_private_msg(user_id=qq_number, message=message)
            logger.info(f"成功发送消息给 {qq_number}: {message}")

            # 记录到 chat_history.json
            chat_entry = {
                "qq": qq_number,
                "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "message": message
            }
            chat_history_path = os.path.join(self.base_path, "repository", f"{qq_number}_chat_history.json")
            chat_history = []
            if os.path.exists(chat_history_path):
                with open(chat_history_path, "r", encoding="utf-8") as f:
                    chat_history = json.load(f)
            chat_history.append(chat_entry)
            with open(chat_history_path, "w", encoding="utf-8") as f:
                json.dump(chat_history, f, ensure_ascii=False, indent=4)
            logger.info(f"消息已存储到聊天记录: {chat_entry}")
        except Exception as e:
            logger.error(f"发送或存储消息失败: {e}")

    async def schedule_message(self, qq_number: str, send_time: datetime,user_text):
        # 定时发送消息，等待直到获取到 Bot 实例
        try:
            # 等待直到获取到 Bot 实例
            timeout = 30  # 最大等待时间（秒）
            start_time = datetime.now()
            while True:
                bot = get_bot()
                if bot:
                    break
                elapsed = (datetime.now() - start_time).total_seconds()
                if elapsed >= timeout:
                    logger.error(f"等待 Bot 超时 ({timeout} 秒)，无法安排任务给 {qq_number}")
                    return
                logger.debug(f"等待 Bot 实例，elapsed: {elapsed} 秒...")
                await asyncio.sleep(1)  # 每秒检查一次

            # 安排定时任务
            self.scheduler.add_job(
                self.send_and_store_message,
                trigger=DateTrigger(run_date=send_time),
                args=[bot, qq_number,user_text]
            )
            logger.info(f"已安排定时任务: 在 {send_time} 向 {qq_number} 发送消息")
        except Exception as e:
            logger.error(f"安排定时任务失败: {e}")

    def text_use(self,time,user_text):
        self.scheduler.start()

        # 安排指定时间发送消息
        send_time = datetime.now() + timedelta(minutes=time)
        qq_number = "2740954024"  # 目标 QQ 号

        self.schedule_message(qq_number, send_time,user_text)