 # 表情包相关部分
import os
import json
import random
from nonebot import on_message, logger

# 表情包存储的JSON文件路径
EMOJI_JSON_PATH = "emojis.json"

class EmojiManager:
    def __init__(self):
        # 初始化表情包管理器哦
        # 表情包发送概率
        self.emoji_probability = 1
        self.emoji_file_path = os.path.join("./repository", EMOJI_JSON_PATH)  # 表情包存储的JSON文件路径
        self.custom_emoji_dict = {}
        # 加载表情包数据，确保初始化
        self.load_emojis()

    def load_emojis(self):
        # 喵~读取表情包数据哦~（轻笑）
        default_emojis = {
            "摸摸": "[CQ:image,file=https://your-server/emojis/touch.gif]",
            "开心": "[CQ:image,file=https://your-server/emojis/heart.png]"
        }
        try:
            if not os.path.exists(self.emoji_file_path):
                # 如果文件不存在，创建默认文件
                logger.info(f"表情包文件不存在，创建默认文件: {self.emoji_file_path}")
                with open(self.emoji_file_path, "w", encoding="utf-8") as f:
                    json.dump(default_emojis, f, ensure_ascii=False, indent=4)
            with open(self.emoji_file_path, "r", encoding="utf-8") as f:
                self.custom_emoji_dict = json.load(f)
            self.custom_emoji_list = list(self.custom_emoji_dict.values())
            logger.debug(f"加载表情包数据: {self.custom_emoji_dict}")
        except Exception as e:
            logger.error(f"读取表情包文件失败了呢: {e}，用默认数据")
            self.custom_emoji_dict = default_emojis
            self.custom_emoji_list = list(self.custom_emoji_dict.values())
            # 确保写入默认数据
            try:
                with open(self.emoji_file_path, "w", encoding="utf-8") as f:
                    json.dump(self.custom_emoji_dict, f, ensure_ascii=False, indent=4)
            except Exception as write_error:
                logger.error(f"写入默认表情包文件失败: {write_error},但是已经设置默认数据")

    def save_emojis(self):
        # 保存表情包数据
        try:
            with open(self.emoji_file_path, "w", encoding="utf-8") as f:
                json.dump(self.custom_emoji_dict, f, ensure_ascii=False, indent=4)
            logger.debug(f"保存表情包数据: {self.custom_emoji_dict}")
        except Exception as e:
            logger.error(f"保存表情包文件失败: {e}")

    def save_user_emoji(self, emoji_url, remark):
        # 保存用户发送的表情包URL
        try:
            if not hasattr(self, 'custom_emoji_dict') or not hasattr(self, 'custom_emoji_list'):
                logger.warning("表情包数据未初始化，重新加载哦")
                self.load_emojis()
            if any(emoji_url in emoji for emoji in self.custom_emoji_dict.values()):
                logger.debug(f"表情包URL已存在: {emoji_url}，不重复保存")
                return False
            self.custom_emoji_dict[remark] = f"[CQ:image,file={emoji_url}]"
            self.custom_emoji_list = list(self.custom_emoji_dict.values())
            self.save_emojis()
            logger.info(f"保存表情包URL成功: {emoji_url}，备注: {remark}")
            return True
        except Exception as e:
            logger.error(f"保存表情包URL失败了: {e}")
            return False
        

    def find_best_emoji(self, reply_text):
        # 根据回复内容找最匹配的表情包
        try:
            if not hasattr(self, 'custom_emoji_dict') or not hasattr(self, 'custom_emoji_list'):
                logger.warning("表情包数据未初始化，重新加载")
                self.load_emojis()
            if not self.custom_emoji_dict:
                logger.debug("表情包列表为空，用默认表情")
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
                logger.debug(f"找到最匹配的表情包，备注相关性得分: {best_score}，表情: {best_match}")
                return best_match
            else:
                logger.debug("没有找到匹配的备注，随机挑一个表情")
                return random.choice(self.custom_emoji_list) if self.custom_emoji_list else "[CQ:image,file=https://your-server/emojis/default.gif]"
        except Exception as e:
            logger.error(f"选择表情包失败了: {e}，先用默认表情")
            return "[CQ:image,file=https://your-server/emojis/default.gif]"


    def add_emoji(self, sentence, user_text, is_image_message=False):
        # 如果用户发了表情包，则也回一个表情包
        if is_image_message:
            return f"{sentence} {random.choice(self.custom_emoji_list)}"  # 随机回复一个表情包
        # 分析用户话语，找出最匹配的表情包
        user_text = user_text.lower()  # 忽略大小写
        for keyword, emoji in self.custom_emoji_dict.items():
            if keyword.lower() in user_text:
                return f"{sentence} {emoji}"  # 匹配备注
        # 没找到匹配的备注，随机挑一个收藏表情
        if random.random() < self.emoji_probability:
            emoji = random.choice(self.custom_emoji_list)
            return f"{sentence} {emoji}"
        return f"{sentence} {random.choice(self.custom_emoji_list)}"  # 强制表情


  