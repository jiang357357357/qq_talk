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

    def save_user_emoji(self, emoji_url, remark):
        # 喵~保存用户发送的表情包URL哦~（眨眼）
        try:
            if not hasattr(self, 'custom_emoji_dict') or not hasattr(self, 'custom_emoji_list'):
                logger.warning("表情包数据未初始化，重新加载哦~")
                self.load_emojis()
            if any(emoji_url in emoji for emoji in self.custom_emoji_dict.values()):
                logger.debug(f"表情包URL已存在: {emoji_url}，不重复保存哦~")
                return False
            self.custom_emoji_dict[remark] = f"[CQ:image,file={emoji_url}]"
            self.custom_emoji_list = list(self.custom_emoji_dict.values())
            self.save_emojis()
            logger.info(f"保存表情包URL成功: {emoji_url}，备注: {remark}呢~")
            return True
        except Exception as e:
            logger.error(f"保存表情包URL失败了呢: {e}，别生气哦~")
            return False
    def find_best_emoji(self, reply_text):
        # 喵~根据回复内容找最匹配的表情包哦~（眨眼）
        try:
            if not hasattr(self, 'custom_emoji_dict') or not hasattr(self, 'custom_emoji_list'):
                logger.warning("表情包数据未初始化，重新加载哦~")
                self.load_emojis()
            if not self.custom_emoji_dict:
                logger.debug("表情包列表为空，用默认表情哦~")
                return "[CQ:image,file=https://your-server/emojis/default.gif]"

            reply_text = reply_text.lower()
            best_match = None
            best_score = -1

            # 简单匹配：计算回复与备注的公共子串长度
            for remark, emoji in self.custom_emoji_dict.items():
                remark = remark.lower()
                # 计算公共子串长度（简单方法）
                score = 0
                for i in range(len(remark)):
                    for j in range(i + 1, len(remark) + 1):
                        substring = remark[i:j]
                        if substring in reply_text:
                            score = max(score, len(substring))
                if score > best_score:
                    best_score = score
                    best_match = emoji

            if best_match:
                logger.debug(f"找到最匹配的表情包，备注相关性得分: {best_score}，表情: {best_match}呢~")
                return best_match
            else:
                logger.debug("没有找到匹配的备注，随机挑一个表情吧~")
                return random.choice(self.custom_emoji_list) if self.custom_emoji_list else "[CQ:image,file=https://your-server/emojis/default.gif]"
        except Exception as e:
            logger.error(f"选择表情包失败了呢: {e}，我先用默认表情哦~")
            return "[CQ:image,file=https://your-server/emojis/default.gif]"


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
    if not user_msg:
        return
    logger.debug(f"收到你的消息啦: {user_msg}，是不是很棒~")
    chat_id = f"user_{event.user_id}"

    # 喵~检查是不是保存指令哦~（眨眼）
    if user_msg.startswith("保存 "):
        for attempt in range(3):  # 重试3次
            try:
                # 提取备注和表情包URL，允许备注中包含换行符
                match_remark = re.match(r"保存\s+([\s\S]+?)\[CQ:image", user_msg)
                match_url = re.search(r'url=(https?://[^,\]]+)', user_msg)
                if match_remark and match_url:
                    remark = match_remark.group(1).strip()
                    emoji_url = match_url.group(1)
                    if ollama.save_user_emoji(emoji_url, remark):
                        await bot.send(event, Message("保存成功~"))
                        # 喵~提醒腾讯URL可能有有效期哦~（轻笑）
                        if "multimedia.nt.qq.com.cn" in emoji_url:
                            await bot.send(event, Message("喵~腾讯的表情包URL可能会有有效期哦，记得留意呢~"))
                    else:
                        await bot.send(event, Message("喵~这个表情包已经保存过了哦！"))
                else:
                    await bot.send(event, Message("喵~保存格式不对呢，应该是‘保存 备注[CQ:image...]’哦~"))
                return  # 不继续处理，直接返回
            except ActionFailed as e:
                logger.error(f"发送保存回复失败了呢: {e}，第 {attempt + 1} 次重试哦~")
                if attempt < 2:
                    await asyncio.sleep(2)  # 等待2秒后重试
                else:
                    await bot.send(event, Message("喵~保存回复发送失败了，可能是风控了哦，稍后再试呢~"))
                    return
            except Exception as e:
                logger.error(f"保存表情包失败了呢: {e}，别生气哦~")
                await bot.send(event, Message("喵~保存表情包失败了，稍后再试哦！"))
                return

    # 正常消息处理
    reply = await ollama.chat(chat_id, user_msg)
    try:
        lines = reply.split("\n")
        sentences = []
        for line in lines:
            line = line.strip()
            if not line:
                continue
            escaped_separators = [re.escape(sep) for sep in ollama.sentence_separators]
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
                    for sep in ollama.sentence_separators:
                        if line.startswith(sep, orig_end):
                            found_separator = sep
                            break
                    if found_separator:
                        sentence += found_separator
                sentences.append(sentence)
        for sentence in sentences:
            await bot.send(event, Message(sentence))
            await asyncio.sleep(1)
        if sentences:
            try:
                # 根据回复内容选择最匹配的表情包
                final_emoji = ollama.find_best_emoji(reply)
                if final_emoji.strip():
                    await bot.send(event, Message(final_emoji))
            except ActionFailed as e:
                logger.error(f"发送表情包失败了呢: {e}，别生气哦~")
                await bot.send(event, Message("喵~表情包好像发不出去，稍后再试哦！"))
    except ActionFailed as e:
        logger.error(f"发送消息失败了呢: {e}，别生气哦~")
        await bot.send(event, Message("喵~我好像被QQ拦住了，检查下我的权限哦！"))
    except Exception as e:
        logger.error(f"发送消息出错了呢: {e}，别怪我哦~")
        await bot.send(event, Message("喵~我好像出错了，等等我好不好~"))