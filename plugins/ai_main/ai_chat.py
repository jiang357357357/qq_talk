import json
import os
import random
import httpx
import re
import asyncio
from nonebot import on_message, logger
from nonebot.adapters.onebot.v11 import Message, MessageEvent, Bot, GroupMessageEvent, PrivateMessageEvent
from nonebot.exception import ActionFailed
from nonebot import require
from nonebot.rule import to_me
from plugins.ai_main.gpt_text import lovel_text, high_white



# 私聊的QQ号
ALLOWED_PRIVATE_QQ = [2740954024]

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

class OllamaWalk:
    def __init__(self):
        # 从环境变量中读取API密钥
        self.api = os.getenv("DEEPSEEK_API_KEY", "default-key-if-not-set")
        self.emoji_path = os.path.join("./repository", EMOJI_JSON_PATH)
        self.talk_path = "./repository/talk/"
        # 确保目录存在呢
        os.makedirs(self.talk_path, exist_ok=True)
        self.walk_num = 2
        self.user_name = "店长"
        self.sentence_separators = ["。", "！", "~", "？", "..."]
        # 消息记录会根据聊天对象分开存储哦~（轻笑）
        self.messages_dict = {}
        # 加载表情包数据，确保初始化
        self.load_emojis()
        # 表情包发送概率
        self.emoji_probability = 1


    def get_file_path(self, chat_id):
        # 以用户ID生成唯一的文件名
        return os.path.join(self.talk_path, f"messages_{chat_id}.json")

    def load_messages(self, chat_id):
        file_path = self.get_file_path(chat_id)
        try:
            if not os.path.exists(file_path):
                # 喵~如果没有记录，我就帮你初始化一个新的哦~（轻笑）
                messages_list = [
                    {"role": "system", "content": high_white},
                    {"role": "user", "content": lovel_text}
                ]
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(messages_list, f, ensure_ascii=False, indent=4)
                logger.debug(f"创建消息文件: {file_path}呢~")
                return messages_list
            else:
                # 读取已有的消息记录
                with open(file_path, "r", encoding="utf-8") as f:
                    messages_list = json.load(f)
                logger.debug(f"读取消息文件: {file_path}，内容是: {messages_list}呢~")
                return messages_list
        except Exception as e:
            # 哎呀~读取消息失败了
            logger.error(f"读取消息文件失败了呢: {e}，别生气好不好~")
            return [
                {"role": "system", "content": high_white},
                {"role": "user", "content": lovel_text}
            ]
    
    # 表情包相关部分
    def load_emojis(self):
        # 喵~读取表情包数据哦~（轻笑）
        default_emojis = {
            "摸摸": "[CQ:image,file=https://your-server/emojis/touch.gif]",
            "开心": "[CQ:image,file=https://your-server/emojis/heart.png]"
        }
        try:
            if not os.path.exists(self.emoji_path):
                # 如果文件不存在，创建默认文件
                logger.info(f"表情包文件不存在，创建默认文件: {self.emoji_path}呢~")
                with open(self.emoji_path, "w", encoding="utf-8") as f:
                    json.dump(default_emojis, f, ensure_ascii=False, indent=4)
            with open(self.emoji_path, "r", encoding="utf-8") as f:
                self.custom_emoji_dict = json.load(f)
            self.custom_emoji_list = list(self.custom_emoji_dict.values())
            logger.debug(f"偷偷加载表情包数据: {self.custom_emoji_dict}呢~")
        except Exception as e:
            logger.error(f"读取表情包文件失败了呢: {e}，用默认数据哦~")
            self.custom_emoji_dict = default_emojis
            self.custom_emoji_list = list(self.custom_emoji_dict.values())
            # 确保写入默认数据
            try:
                with open(self.emoji_path, "w", encoding="utf-8") as f:
                    json.dump(self.custom_emoji_dict, f, ensure_ascii=False, indent=4)
            except Exception as write_error:
                logger.error(f"写入默认表情包文件失败了呢: {write_error}，但我已经设置了默认数据哦~")

    def save_emojis(self):
        # 喵~保存表情包数据哦~（轻笑）
        try:
            with open(self.emoji_path, "w", encoding="utf-8") as f:
                json.dump(self.custom_emoji_dict, f, ensure_ascii=False, indent=4)
            logger.debug(f"悄悄保存表情包数据: {self.custom_emoji_dict}呢~")
        except Exception as e:
            logger.error(f"保存表情包文件失败了呢: {e}，别生气好不好~")

    def save_user_emoji(self, emoji_url, user_id):
        # 喵~保存用户发送的表情包URL哦~（眨眼）
        try:
            if not hasattr(self, 'custom_emoji_dict') or not hasattr(self, 'custom_emoji_list'):
                logger.warning("表情包数据未初始化，重新加载哦~")
                self.load_emojis()
            if any(emoji_url in emoji for emoji in self.custom_emoji_dict.values()):
                logger.debug(f"表情包URL已存在: {emoji_url}，不重复保存哦~")
                return False
            remark = f"用户表情_{user_id}_{random.randint(100, 999)}"
            self.custom_emoji_dict[remark] = f"[CQ:image,file={emoji_url}]"
            self.custom_emoji_list = list(self.custom_emoji_dict.values())
            self.save_emojis()
            logger.info(f"保存用户表情包URL成功: {emoji_url}，备注: {remark}呢~")
            return True
        except Exception as e:
            logger.error(f"保存用户表情包URL失败了呢: {e}，别生气哦~")
            return False

    def add_emoji(self, sentence, user_text, is_image_message=False):
        # 喵~如果用户发了表情包，我也回一个表情包哦~（眨眼）
        if is_image_message:
            return f"{sentence} {random.choice(self.custom_emoji_list)}"  # 随机回复一个表情包
        # 喵~看看你说了什么，挑个收藏表情给你哦~（眨眼）
        user_text = user_text.lower()  # 忽略大小写
        for keyword, emoji in self.custom_emoji_dict.items():
            if keyword.lower() in user_text:
                return f"{sentence} {emoji}"  # 匹配备注
        # 嗯哼~没找到匹配的备注，随机挑一个收藏表情吧~（轻笑）
        if random.random() < self.emoji_probability:
            emoji = random.choice(self.custom_emoji_list)
            return f"{sentence} {emoji}"
        return f"{sentence} {random.choice(self.custom_emoji_list)}"  # 强制表情


    def save_messages(self, chat_id, messages_list):
        file_path = self.get_file_path(chat_id)
        try:
            #保存消息记录
            logger.debug(f"保存消息文件: {file_path}，内容是: {messages_list}呢~")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(messages_list, f, ensure_ascii=False, indent=4)
        except Exception as e:
            # 哎呀~保存消息失败
            logger.error(f"保存消息文件失败了: {e}，")

    async def get_text(self, user_input):
        try:
            url = "https://api.deepseek.com/chat/completions"
            payload = json.dumps({
                "model": "deepseek-chat",
                "messages": user_input,
                "temperature": 0.7
            })
            headers = {
                "Authorization": f"Bearer {self.api}",
                "Content-Type": "application/json"
            }
            # 嗯哼~我要发送API请求啦，准备好了吗~（眨眼）
            logger.debug(f"悄悄发送API请求: {payload}，是不是很期待~")
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, content=payload, headers=headers)
                if resp.status_code != 200:
                    logger.error(f"API请求返回状态码: {resp.status_code}，内容: {resp.text}")
                resp.raise_for_status()
                data = resp.json()
                # 喵~API回应我啦，来看看是什么吧~（轻笑）
                logger.debug(f"API回应我啦: {data}，是不是很棒~")
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            # 哎呀~网络好像迷路了呢，稍后再试好不好~（轻声）
            logger.error(f"API请求失败了呢: {e.response.status_code} {e.response.text}，别生气哦~")
            return "喵~网络好像迷路了，稍后再试哦！"
        except Exception as e:
            # 嗯~我好像有点晕乎乎，等等我好不好~（轻笑）
            logger.error(f"API调用出错了呢: {e}，别怪我哦~")
            return "喵~我好像有点晕乎乎，等等我哦！"


    async def chat(self, chat_id, user_text):
        try:
            # 喵~加载对应聊天对象的消息记录哦~（轻笑）
            if chat_id not in self.messages_dict:
                self.messages_dict[chat_id] = self.load_messages(chat_id)
            messages_list = self.messages_dict[chat_id]

            # 嗯哼~限制消息轮次，保持最新对话呢~（眨眼）
            max_messages = 2 + self.walk_num * 2  # 2是初始system和user消息
            if len(messages_list) > max_messages:
                messages_list[2:] = messages_list[-self.walk_num * 2:]
            
            # 喵~添加你的消息到记录里哦~（轻笑）
            messages_list.append({"role": "user", "content": user_text})
            reply = await self.get_text(messages_list)
            messages_list.append({"role": "assistant", "content": reply})

            # 嗯~保存最新的消息记录呢~（眨眼）
            self.save_messages(chat_id, messages_list)
            return reply
        except Exception as e:
            # 喵~我好像踩到尾巴了，稍后再聊好不好~（轻笑）
            logger.error(f"聊天处理出错了呢: {e}，别怪我哦~")
            return "喵~我好像踩到尾巴了，稍后再聊哦！"

ollama = OllamaWalk()

@chat.handle()
async def handle_chat(bot: Bot, event: MessageEvent):
    user_msg = str(event.get_message()).strip()
    is_image_message = user_msg.startswith("[CQ:image")
    if not user_msg:
        return
    # 嗯哼~收到你的消息啦，开心得不得了呢~（眨眼）
    logger.debug(f"收到你的消息啦: {user_msg}，是不是很棒~")

    # 喵~根据群聊或私聊生成唯一的chat_id哦~（轻笑）
   
    chat_id = f"user_{event.user_id}"

    # 如果是表情包消息，保存表情包URL
    if is_image_message:
        match = re.search(r'url=(https?://[^,\]]+)', user_msg)
        if match:
            emoji_url = match.group(1)
            ollama.save_user_emoji(emoji_url, event.user_id)

    reply = await ollama.chat(chat_id, user_msg)
   # 喵~我要开始分句啦，慢慢说给你听哦~（轻笑）
    try:
        # 喵~我要开始分句啦，慢慢说给你听哦~（轻笑）
        # 先按换行符分割
        lines = reply.split("\n")
        sentences = []
        for line in lines:
            line = line.strip()  # 去除每行首尾空白
            if not line:
                continue  # 跳过空行
            # 按分隔符进一步分割每行
            escaped_separators = [re.escape(sep) for sep in ollama.sentence_separators]
            pattern = '|'.join(escaped_separators)
            line_sentences = re.split(pattern, line)
            # 保留分隔符
            for i, sentence in enumerate(line_sentences):
                sentence = sentence.strip()  # 去除每句首尾空白
                if not sentence:
                    continue  # 跳过空句
                orig_index = line.find(sentence)
                orig_end = orig_index + len(sentence)
                if i < len(line_sentences) - 1:
                    found_separator = None
                    for sep in ollama.sentence_separators:
                        if line.startswith(sep, orig_end):
                            found_separator = sep
                            break
                    if found_separator:
                        sentence += found_separator
                sentences.append(sentence)

        # 嘻嘻~一句一句发给你，每句间隔1秒，感觉怎么样~（眨眼）
        for sentence in sentences:
            # 嗯哼~慢慢发给你，别急哦~（轻笑）
            await bot.send(event, Message(sentence))
            # 喵~稍微停顿一下，1秒钟好不好~（眨眼）
            await asyncio.sleep(1)

        # 喵~话说完啦，送你一个收藏的专属表情包哦~（眨眼）
        if sentences:  # 确保有句子
            try:
                final_emoji = ollama.add_emoji("", user_msg, is_image_message)
                if final_emoji.strip():
                    await bot.send(event, Message(final_emoji))
            except ActionFailed as e:
                logger.error(f"发送表情包失败了呢: {e}，别生气哦~")
                await bot.send(event, Message("喵~表情包好像发不出去，稍后再试哦！"))
    except ActionFailed as e:
        # 哎呀~我好像被QQ拦住了，检查下我的权限好不好~（轻声）
        logger.error(f"发送消息失败了呢: {e}，别生气哦~")
        await bot.send(event, Message("喵~我好像被QQ拦住了，检查下我的权限哦！"))
    except Exception as e:
        # 喵~我好像出错了，等等我好不好~（轻笑）
        logger.error(f"发送消息出错了呢: {e}，别怪我哦~")
        await bot.send(event, Message("喵~我好像出错了，等等我哦！"))