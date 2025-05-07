import re
import os
import json
import httpx
from nonebot import on_message, logger

from plugins.AI_talk.gpt_text import lovel_text, high_white
from nonebot.adapters.onebot.v11 import Message, MessageEvent, Bot, GroupMessageEvent, PrivateMessageEvent

# 私聊的QQ号
ALLOWED_PRIVATE_QQ = [1657172041,2740954024]

# 只有群聊被@或者指定QQ私聊时触发
chat = on_message(
    priority=99,
    block=False,
    rule=lambda event: (
        (isinstance(event, GroupMessageEvent) and event.is_tome()) or
        (isinstance(event, PrivateMessageEvent) and event.user_id in ALLOWED_PRIVATE_QQ)
    )
)

class AiManager:
    def __init__(self):
        # 从环境变量中读取API密钥
        self.api = os.getenv("GROK_KEY", "default-key-if-not-set")
        #  key os.getenv("DEEPSEEK_API_KEY", "default-key-if-not-set")
        # 聊天目录
        self.talk_path = "./repository/talk/"
        # 确保目录存在呢
        os.makedirs(self.talk_path, exist_ok=True)
        # 聊天轮数
        self.talk_num = 2
        self.user_name = "店长"
        self.sentence_separators = ["。", "！", "~", "？", "..."]
        # 消息记录会根据聊天对象分开存储哦~（轻笑）
        self.messages_dict = {}


    def get_file_path(self, chat_id):
    # 以用户ID生成唯一的文件名
        return os.path.join(self.talk_path, f"messages_{chat_id}.json")
        
    # 载入聊天消息
    def load_messages(self, chat_id):
        file_path = self.get_file_path(chat_id)
        try:
            if not os.path.exists(file_path):
                # 如果没有记录，初始化
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
            # 读取消息失败
            logger.error(f"读取消息文件失败: {e}")
            return [
                {"role": "system", "content": high_white},
                {"role": "user", "content": lovel_text}
            ]
            
    def save_messages(self, chat_id, messages_list):
        file_path = self.get_file_path(chat_id)
        try:
            #保存消息记录
            logger.debug(f"保存消息文件: {file_path}，内容是: {messages_list}呢~")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(messages_list, f, ensure_ascii=False, indent=4)
        except Exception as e:
            # 保存消息失败
            logger.error(f"保存消息文件失败: {e}，")

    async def get_text(self, user_input):
        try:
            url = "https://api.xgrok.club/v1/chat/completions"
            # desk https://api.deepseek.com/chat/completions
            payload = json.dumps({
                "model": "grok-3",
                # deepseek-chat
                "messages": user_input,
                "temperature": 0.7
            })
            headers = {
                "Authorization": f"Bearer {self.api}",
                "Content-Type": "application/json"
            }
            #发送API请求
            logger.debug(f"发送API请求: {payload}")
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(url, content=payload, headers=headers)
                if resp.status_code != 200:
                    logger.error(f"API请求返回状态码: {resp.status_code}，内容: {resp.text}")
                resp.raise_for_status()
                data = resp.json()
                # API回应
                logger.debug(f"API回应: {data}")
                return data["choices"][0]["message"]["content"]
        except httpx.HTTPStatusError as e:
            # 网络链接失败
            logger.error(f"API请求失败: {e.response.status_code} {e.response.text}，别生气哦~")
            return "喵~网络好像迷路了，稍后再试哦！"
        except Exception as e:
            # 嗯~我好像有点晕乎乎，等等我好不好~（轻笑）
            logger.error(f"API调用出错: {e}，别怪我哦~")
            return "喵~我好像有点晕乎乎，等等我哦！"
        
    async def chat(self, chat_id, user_text):
        try:
            # 喵~加载对应聊天对象的消息记录哦~（轻笑）
            if chat_id not in self.messages_dict:
                self.messages_dict[chat_id] = self.load_messages(chat_id)
            messages_list = self.messages_dict[chat_id]

            # 嗯哼~限制消息轮次，保持最新对话呢~（眨眼）
            max_messages = 2 + self.talk_num * 2  # 2是初始system和user消息
            if len(messages_list) > max_messages:
                messages_list[2:] = messages_list[-self.talk_num * 2:]
            
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

    def slice_talk(self,reply):
        lines = reply.split("\n")
        sentences = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            escaped_separators = [re.escape(sep) for sep in self.sentence_separators]
            pattern = '|'.join(escaped_separators)
            line_sentences = re.split(pattern, line)
            for i, sentence in enumerate(line_sentences):
                sentence = sentence.strip()
                if not sentence:
                    continue
                orig_index = line.find(sentence)
                orig_end = orig_index + len(sentence)
                if i < len(line_sentences) - 1:
                    found_separator = None
                    for sep in self.sentence_separators:
                        if line.startswith(sep, orig_end):
                            found_separator = sep
                            break
                    if found_separator:
                        sentence += found_separator
                sentences.append(sentence)
        return sentences