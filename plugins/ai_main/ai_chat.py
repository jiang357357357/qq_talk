import json
import os
import httpx
import re
import asyncio
from nonebot import on_message, logger
from nonebot.adapters.onebot.v11 import Message, MessageEvent, Bot, GroupMessageEvent, PrivateMessageEvent
from nonebot.exception import ActionFailed
from nonebot import require
from nonebot.rule import to_me
from plugins.ai_main.gpt_text import lovel_text, high_white



# 嗯哼~允许私聊的QQ号我可是偷偷记下来了哦~（轻笑）
ALLOWED_PRIVATE_QQ = [2740954024]

# 喵~只有群聊被@或者指定QQ私聊时，我才会理你呢~（眨眼）
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
        # 喵~存储文件的目录我帮你定好了哦~（轻笑）
        self.base_path = "c:/code/python/qq_talk/qq_talk/src/plugins/messages/"
        # 嗯哼~确保目录存在呢，小心翼翼哦~（眨眼）
        os.makedirs(self.base_path, exist_ok=True)
        self.walk_num = 3
        self.user_name = "店长"
        self.sentence_separators = ["。", "！", "~", "？", "..."]
        # 喵~消息记录会根据聊天对象分开存储哦~（轻笑）
        self.messages_dict = {}

    def get_file_path(self, chat_id):
        # 嗯哼~根据聊天对象生成唯一的文件名呢~（眨眼）
        return os.path.join(self.base_path, f"messages_{chat_id}.json")

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
                logger.debug(f"小手一挥，创建消息文件: {file_path}呢~")
                return messages_list
            else:
                # 嗯~读取已有的消息记录给你看哦~（眨眼）
                with open(file_path, "r", encoding="utf-8") as f:
                    messages_list = json.load(f)
                logger.debug(f"偷偷读取消息文件: {file_path}，内容是: {messages_list}呢~")
                return messages_list
        except Exception as e:
            # 哎呀~读取消息失败了呢，我会乖乖告诉你哦~（轻声）
            logger.error(f"读取消息文件失败了呢: {e}，别生气好不好~")
            return [
                {"role": "system", "content": high_white},
                {"role": "user", "content": lovel_text}
            ]

    def save_messages(self, chat_id, messages_list):
        file_path = self.get_file_path(chat_id)
        try:
            # 嘻嘻~保存消息记录的时候，我可是小心翼翼的哦~（眨眼）
            logger.debug(f"悄悄保存消息文件: {file_path}，内容是: {messages_list}呢~")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(messages_list, f, ensure_ascii=False, indent=4)
        except Exception as e:
            # 哎呀~保存消息失败了呢，我会乖乖告诉你哦~（轻声）
            logger.error(f"保存消息文件失败了呢: {e}，别生气好不好~")

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
    if not user_msg:
        return
    # 嗯哼~收到你的消息啦，开心得不得了呢~（眨眼）
    logger.debug(f"收到你的消息啦: {user_msg}，是不是很棒~")

    # 喵~根据群聊或私聊生成唯一的chat_id哦~（轻笑）
    if isinstance(event, GroupMessageEvent):
        chat_id = f"group_{event.group_id}"
    else:
        chat_id = f"private_{event.user_id}"

    reply = await ollama.chat(chat_id, user_msg)
    try:
        # 喵~我要开始分句啦，慢慢说给你听哦~（轻笑）
        escaped_separators = [re.escape(sep) for sep in ollama.sentence_separators]
        pattern = '|'.join(escaped_separators)
        sentences = re.split(pattern, reply)
        sentences = [s.strip() for s in sentences if s.strip()]
        # 嘻嘻~一句一句发给你，每句间隔1秒，感觉怎么样~（眨眼）
        for i, sentence in enumerate(sentences):
            orig_index = reply.find(sentence)
            orig_end = orig_index + len(sentence)
            if i < len(sentences) - 1:
                found_separator = None
                for sep in ollama.sentence_separators:
                    if reply.startswith(sep, orig_end):
                        found_separator = sep
                        break
                if found_separator:
                    sentence += found_separator
            # 嗯哼~慢慢发给你，别急哦~（轻笑）
            await bot.send(event, Message(sentence))
            # 喵~稍微停顿一下，1秒钟好不好~（眨眼）
            await asyncio.sleep(1)
    except ActionFailed as e:
        # 哎呀~我好像被QQ拦住了，检查下我的权限好不好~（轻声）
        logger.error(f"发送消息失败了呢: {e}，别生气哦~")
        await bot.send(event, Message("喵~我好像被QQ拦住了，检查下我的权限哦！"))
    except Exception as e:
        # 喵~我好像出错了，等等我好不好~（轻笑）
        logger.error(f"发送消息出错了呢: {e}，别怪我哦~")
        await bot.send(event, Message("喵~我好像出错了，等等我哦！"))