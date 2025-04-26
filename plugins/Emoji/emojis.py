import os
import random
import aiohttp
from PIL import Image
from nonebot import on_message, logger
from nonebot.adapters.onebot.v11 import MessageSegment
from nonebot.adapters import Bot, Event

class EmojiManager:
    def __init__(self):
        # 初始化表情包管理器哦
        self.emoji_probability = 1
        # 动态设置根路径
        self.is_windows = os.name == "nt"
        self.base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")) if self.is_windows else "/home/web/qq_ai/code/qq_talk"
        self.emoji_base_path = os.path.join(self.base_path, "repository", "emojis")
        self.temp_path = os.path.join(os.getenv("USERPROFILE") if self.is_windows else "/home/web", ".config", "QQ", "NapCat", "temp")
        # 确保临时目录存在
        os.makedirs(self.temp_path, exist_ok=True)
        os.makedirs(self.emoji_base_path, exist_ok=True)
        # 动态获取表情包文件夹
        self.all_folders = self.get_emoji_folders()

    def get_emoji_folders(self):
        # 动态读取 emojis 文件夹下的子文件夹
        
        if not os.path.exists(self.emoji_base_path):
            logger.error(f"表情包根目录不存在: {self.emoji_base_path}")
            return []
        folders = [f for f in os.listdir(self.emoji_base_path) if os.path.isdir(os.path.join(self.emoji_base_path, f))]
        logger.error(f"folders:{folders}")
        logger.debug(f"找到的表情包文件夹: {folders}")
        return folders

    def match_folder(self, reply_text, folders):
        # 匹配文件夹的独立方法，方便后续修改
        reply_text = reply_text.lower()
        for folder in folders:
            if folder.lower() in reply_text:
                logger.debug(f"匹配到文件夹: {folder}")
                return folder
        return None

    def select_emoji_folder(self, reply_text):
        # 根据回复内容选择表情包文件夹
        matched_folder = self.match_folder(reply_text, self.all_folders)
        if matched_folder:
            return matched_folder
        # 如果无法匹配，随机选择一个文件夹
        chosen_folder = random.choice(self.all_folders) if self.all_folders else None
        logger.debug(f"未匹配到文件夹，随机选择: {chosen_folder}")
        return chosen_folder

    def _get_file_url(self, filepath):
        # 使用标准化的 file:// 路径
        filepath = os.path.abspath(filepath)
        filepath = filepath.replace("\\", "/")  # 统一使用正斜杠
        file_url = f"file:///{filepath}"
        logger.debug(f"生成表情包路径: {file_url}")
        return file_url

    def _process_image(self, src_path, scale_factor=0.5, quality=80):
        try:
            # 确保临时目录存在
            if not os.path.exists(self.temp_path):
                os.makedirs(self.temp_path, exist_ok=True)

            # 规范化路径
            src_path = os.path.abspath(src_path.replace("/", os.sep))
            logger.debug(f"规范化后的路径: {src_path}")

            # 临时文件路径
            filename = os.path.basename(src_path)
            temp_filename = f"temp_{random.randint(1000, 9999)}_{filename}"
            temp_path = os.path.join(self.temp_path, temp_filename)

            # 检查原始文件是否存在
            if not os.path.exists(src_path):
                logger.error(f"原始表情包文件不存在: {src_path}")
                return None

            # 检查文件是否可读
            if not os.access(src_path, os.R_OK):
                logger.error(f"文件不可读: {src_path}")
                return None

            # 使用 Pillow 处理图片
            with Image.open(src_path) as img:
                # 按比例缩放
                new_width = int(img.width * scale_factor)
                new_height = int(img.height * scale_factor)
                img = img.resize((new_width, new_height), Image.LANCZOS)
                # 转换为 RGB（如果需要保存为 JPEG）
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                # 保存并降低画质
                img.save(temp_path, "JPEG", quality=quality)
                logger.info(f"表情包已缩放并降低画质: {temp_path}, 缩放比例: {scale_factor}, 画质: {quality}")
            return temp_path
        except Exception as e:
            logger.error(f"处理图片失败: {e}")
            return None

    def get_random_emoji(self, folder_name):
        # 从指定文件夹中随机选择一张图片
        folder_path = os.path.join(self.emoji_base_path, folder_name)
        if not os.path.exists(folder_path):
            logger.error(f"表情包文件夹不存在: {folder_path}")
            return None

        # 获取文件夹中的所有图片文件
        image_extensions = (".jpg", ".jpeg", ".png", ".gif")
        images = [f for f in os.listdir(folder_path) if f.lower().endswith(image_extensions)]
        if not images:
            logger.warning(f"文件夹 {folder_name} 中没有图片")
            return None

        # 随机选择一张图片
        chosen_image = random.choice(images)
        image_path = os.path.join(folder_path, chosen_image)
        logger.debug(f"从 {folder_name} 文件夹中选择图片: {image_path}")
        return image_path

    async def download_image(self, url, filename, folder_name):
        try:
            folder_path = os.path.join(self.emoji_base_path, folder_name)
            os.makedirs(folder_path, exist_ok=True)

            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    if resp.status != 200:
                        logger.error(f"下载表情包失败，状态码: {resp.status}")
                        return None
                    file_path = os.path.join(folder_path, filename)
                    with open(file_path, "wb") as f:
                        f.write(await resp.read())
                    logger.info(f"表情包下载成功: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"下载表情包失败: {e}")
            return None

    async def save_user_emoji(self, emoji_url, folder_name, bot: Bot, event: Event):
        try:
            if folder_name not in self.all_folders:
                logger.error(f"无效的表情包文件夹: {folder_name}")
                return False
            filename = f"emoji_{random.randint(1000, 9999)}.png"
            file_path = await self.download_image(emoji_url, filename, folder_name)
            if not file_path:
                return False
            logger.info(f"保存表情包成功: {file_path}，文件夹: {folder_name}")
            return True
        except Exception as e:
            logger.error(f"保存表情包失败了: {e}")
            return False

    def find_best_emoji(self, reply_text):
        try:
            if not self.all_folders:
                logger.error(self.all_folders)
                return None

            # 根据回复选择文件夹
            folder_name = self.select_emoji_folder(reply_text)
            if not folder_name:
                return None

            # 从文件夹中随机选择一张图片
            image_path = self.get_random_emoji(folder_name)
            if not image_path:
                return None

            # 预处理图片
            processed_path = self._process_image(image_path, scale_factor=0.5, quality=80)
            if processed_path:
                return MessageSegment.image(self._get_file_url(processed_path))
            logger.warning(f"图片处理失败，尝试使用原始图片: {image_path}")
            return MessageSegment.image(self._get_file_url(image_path))
        except Exception as e:
            logger.error(f"选择表情包失败了: {e}，跳过表情包发送")
            return None

    def add_emoji(self, sentence, user_text, is_image_message=False):
        if is_image_message:
            # 对于图片消息，随机选择一个文件夹
            folder_name = random.choice(self.all_folders) if self.all_folders else None
            if not folder_name:
                return sentence

            image_path = self.get_random_emoji(folder_name)
            if not image_path:
                return sentence

            processed_path = self._process_image(image_path, scale_factor=0.5, quality=80)
            if processed_path:
                emoji = MessageSegment.image(self._get_file_url(processed_path))
            else:
                logger.warning(f"图片处理失败，尝试使用原始图片: {image_path}")
                emoji = MessageSegment.image(self._get_file_url(image_path))
            return f"{sentence} {emoji}" if emoji else sentence

        # 根据回复选择文件夹
        folder_name = self.select_emoji_folder(sentence)
        if not folder_name:
            return sentence

        image_path = self.get_random_emoji(folder_name)
        if not image_path:
            return sentence

        processed_path = self._process_image(image_path, scale_factor=0.5, quality=80)
        if processed_path:
            emoji = MessageSegment.image(self._get_file_url(processed_path))
        else:
            logger.warning(f"图片处理失败，尝试使用原始图片: {image_path}")
            emoji = MessageSegment.image(self._get_file_url(image_path))
        return f"{sentence} {emoji}" if emoji else sentence