import os
import json
import random
import aiohttp
from nonebot import on_message, logger
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters import Bot, Event

# 表情包存储的JSON文件路径
EMOJI_JSON_PATH = "emojis.json"
# 表情包存储的文件夹路径
EMOJI_FILE_PATH = "emojis"

class EmojiManager:
    def __init__(self):
        # 初始化表情包管理器哦
        self.emoji_probability = 1
        self.local_emoji_file_path = "repository/emojis"  # Windows 本地路径，仅用于开发
        self.server_emoji_file_path = "/home/web/qq_ai/repository/emojis"  # 阿里云服务器路径
        self.emoji_json_path = "repository/emojis.json"
        self.custom_emoji_dict = {}
        self.custom_emoji_list = []
        self.load_emojis()

    def _get_file_url(self, filename):
        # 直接使用阿里云服务器路径
        file_path = os.path.join(self.server_emoji_file_path, filename)
        file_path = file_path.replace("\\", "/")  # 确保路径分隔符是 /
        logger.debug(f"生成表情包路径: {file_path}")
        return f"file://{file_path}"

    def load_emojis(self):
        # 喵~读取表情包数据哦~（轻笑）
        default_emojis = {
            "摸摸": "touch.gif",
            "开心": "开心.jpg"  # 与实际文件匹配
        }
        try:
            if not os.path.exists(self.emoji_json_path):
                logger.info(f"表情包JSON文件不存在，创建默认文件: {self.emoji_json_path}")
                with open(self.emoji_json_path, "w", encoding="utf-8") as f:
                    json.dump(default_emojis, f, ensure_ascii=False, indent=4)
            with open(self.emoji_json_path, "r", encoding="utf-8") as f:
                emoji_dict = json.load(f)
                # 将文件名转为 MessageSegment.image
                self.custom_emoji_dict = {}
                for k, v in emoji_dict.items():
                    file_url = self._get_file_url(v)
                    if file_url:
                        self.custom_emoji_dict[k] = MessageSegment.image(file_url)
                    else:
                        logger.warning(f"表情包 {v} 路径生成失败，跳过")
                self.custom_emoji_list = list(self.custom_emoji_dict.values())
                logger.debug(f"加载表情包数据: {self.custom_emoji_dict}")
        except Exception as e:
            logger.error(f"读取表情包文件失败了呢: {e}，用默认数据")
            self.custom_emoji_dict = {}
            for k, v in default_emojis.items():
                file_url = self._get_file_url(v)
                if file_url:
                    self.custom_emoji_dict[k] = MessageSegment.image(file_url)
            self.custom_emoji_list = list(self.custom_emoji_dict.values())
            try:
                with open(self.emoji_json_path, "w", encoding="utf-8") as f:
                    json.dump(default_emojis, f, ensure_ascii=False, indent=4)
            except Exception as write_error:
                logger.error(f"写入默认表情包文件失败: {write_error}, 但是已经设置默认数据")

    def save_emojis(self):
        # 保存表情包数据到JSON，只存文件名
        try:
            emoji_dict = {k: str(v).split("/")[-1] for k, v in self.custom_emoji_dict.items()}
            with open(self.emoji_json_path, "w", encoding="utf-8") as f:
                json.dump(emoji_dict, f, ensure_ascii=False, indent=4)
            logger.debug(f"保存表情包数据: {emoji_dict}")
        except Exception as e:
            logger.error(f"保存表情包文件失败: {e}")

    async def download_image(self, url, filename):
        # 下载图片到本地（Windows）
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status == 200:
                        file_path = os.path.join(self.local_emoji_file_path, filename)
                        with open(file_path, "wb") as f:
                            f.write(await resp.read())
                        logger.info(f"表情包下载成功: {file_path}")
                        return file_path
                    else:
                        logger.error(f"下载表情包失败，状态码: {resp.status}")
                        return None
        except Exception as e:
            logger.error(f"下载表情包失败: {e}")
            return None

    async def save_user_emoji(self, emoji_url, remark, bot: Bot, event: Event):
        # 保存用户发送的表情包到本地，并上传到阿里云
        try:
            if not hasattr(self, 'custom_emoji_dict') or not hasattr(self, 'custom_emoji_list'):
                logger.warning("表情包数据未初始化，重新加载哦")
                self.load_emojis()
            # 检查是否已存在
            if any(emoji_url in str(emoji) for emoji in self.custom_emoji_dict.values()):
                logger.debug(f"表情包URL已存在: {emoji_url}，不重复保存")
                return False
            # 生成唯一文件名
            filename = f"emoji_{len(self.custom_emoji_dict)}_{random.randint(1000, 9999)}.png"
            # 下载图片到 Windows 本地
            file_path = await self.download_image(emoji_url, filename)
            if not file_path:
                return False
            # 保存到表情包字典，只存文件名
            self.custom_emoji_dict[remark] = MessageSegment.image(self._get_file_url(filename))
            self.custom_emoji_list = list(self.custom_emoji_dict.values())
            self.save_emojis()
            logger.info(f"保存表情包成功: {file_path}，备注: {remark}")
            return True
        except Exception as e:
            logger.error(f"保存表情包失败了: {e}")
            return False

    def find_best_emoji(self, reply_text):
        # 根据回复内容找最匹配的表情包
        try:
            if not hasattr(self, 'custom_emoji_dict') or not hasattr(self, 'custom_emoji_list'):
                logger.warning("表情包数据未初始化，重新加载")
                self.load_emojis()
            if not self.custom_emoji_dict:
                logger.debug("表情包列表为空，跳过表情包发送")
                return None

            reply_text = reply_text.lower()
            best_match = None
            best_score = -1

            for remark, emoji in self.custom_emoji_dict.items():
                remark = remark.lower()
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
                logger.debug(f"找到最匹配的表情包，备注相关性得分: {best_score}，表情: {best_match}")
                return best_match
            else:
                logger.debug("没有找到匹配的备注，随机挑一个表情")
                return random.choice(self.custom_emoji_list) if self.custom_emoji_list else None
        except Exception as e:
            logger.error(f"选择表情包失败了: {e}，跳过表情包发送")
            return None

    def add_emoji(self, sentence, user_text, is_image_message=False):
        # 如果用户发了表情包，则也回一个表情包
        if is_image_message:
            emoji = random.choice(self.custom_emoji_list) if self.custom_emoji_list else None
            return f"{sentence} {emoji}" if emoji else sentence
        # 分析用户话语，找出最匹配的表情包
        user_text = user_text.lower()
        for keyword, emoji in self.custom_emoji_dict.items():
            if keyword.lower() in user_text:
                return f"{sentence} {emoji}"  # 匹配备注
        # 没找到匹配的备注，随机挑一个收藏表情
        if random.random() < self.emoji_probability:
            emoji = random.choice(self.custom_emoji_list) if self.custom_emoji_list else None
            return f"{sentence} {emoji}" if emoji else sentence
        return sentence