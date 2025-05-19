from datetime import datetime, timezone
import re
import os
import json
import httpx
from nonebot import on_message, logger

from plugins.AI_talk.gpt_text import lovel_text, high_white
from nonebot.adapters.onebot.v11 import Message, MessageEvent, Bot, GroupMessageEvent, PrivateMessageEvent

# 单独创造一个切分类
from pygments import highlight
from pygments.lexers import PythonLexer
from pygments.formatters import HtmlFormatter
import imgkit
from PIL import Image, ImageDraw, ImageFont
import uuid


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
        #self.api = os.getenv("GROK_KEY", "default-key-if-not-set")
        # self.api =  os.getenv("DEEPSEEK_API_KEY", "default-key-if-not-set")
        self.api =  os.getenv("GJLD_API_KEY", "default-key-if-not-set")
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
                current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                messages_list = [
                    {"role": "system", "content": high_white, "timestamp": current_time},
                    {"role": "user", "content": lovel_text, "timestamp": current_time}
                ]
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(messages_list, f, ensure_ascii=False, indent=4)
                logger.debug(f"创建消息文件: {file_path}呢~")
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
                    {"role": "system", "content": high_white, "timestamp": current_time},
                    {"role": "user", "content": lovel_text, "timestamp": current_time}
            ]
            
    def save_messages(self, chat_id, messages_list):
        file_path = self.get_file_path(chat_id)
        try:
            logger.debug(f"保存消息文件: {file_path}，内容是: {messages_list}呢~")
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(messages_list, f, ensure_ascii=False, indent=4)
        except Exception as e:
            # 保存消息失败
            logger.error(f"保存消息文件失败: {e}，")

    async def get_text(self, user_input):
        try:
            url = "https://api.siliconflow.cn/v1/chat/completions"
            # url = "https://api.xgrok.club/v1/chat/completions"
            # url = "https://api.deepseek.com/chat/completions"
            payload = json.dumps({
                "model": "deepseek-ai/DeepSeek-V3",
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
            
            # 添加用户消息，记录创建时间
            messages_list.append({
                "role": "user",
                "content": user_text,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            })
            # 为 API 调用准备消息（只传递 role 和 content）
            api_messages = [{"role": msg["role"], "content": msg["content"]} for msg in messages_list]
            reply = await self.get_text(api_messages)
            # 添加 AI 回复，记录创建时间
            messages_list.append({
                "role": "assistant",
                "content": reply,
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
            })

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
    


# 单独创造一个切分类
class SentenceSlicer:
    def __init__(self, min_chars=10, max_chars=50, sentence_separators=['.', '!', '?', '。', '！', '？']):
        self.min_chars = min_chars
        self.max_chars = max_chars
        self.sentence_separators = sentence_separators
        self.code_block_pattern = r'```[\w]*\n([\s\S]*?)\n```'  # 改进：捕获代码内容
        self.code_blocks = []  # 存储提取的代码块

    def slice_talk(self, reply, output_dir="output"):
        # 确保输出目录存在
        os.makedirs(output_dir, exist_ok=True)
        self.code_blocks = []

        # 提取代码块，替换为占位符
        def replace_code_block(match):
            code_content = match.group(1)  # 只取```内的代码
            self.code_blocks.append(code_content)
            return f"__CODE_BLOCK_{len(self.code_blocks)-1}__"
        
        text = re.sub(self.code_block_pattern, replace_code_block, reply)

        # 分句
        sentences = []
        escaped_separators = [re.escape(sep) for sep in self.sentence_separators]
        pattern = '|'.join(escaped_separators)
        
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        for line in lines:
            raw_sentences = re.split(f'({pattern})', line)
            current_sentence = ""
            
            for i, chunk in enumerate(raw_sentences):
                chunk = chunk.strip()
                if not chunk:
                    continue
                if re.fullmatch(pattern, chunk):
                    current_sentence += chunk
                    continue
                
                current_sentence += chunk
                while len(current_sentence) > self.max_chars:
                    split_pos = self._find_split_pos(current_sentence)
                    if split_pos == -1:
                        split_pos = self.max_chars
                    sentences.append(current_sentence[:split_pos].strip())
                    current_sentence = current_sentence[split_pos:].strip()
                
                if len(current_sentence) >= self.min_chars or i == len(raw_sentences)-1:
                    if current_sentence:
                        sentences.append(current_sentence)
                        current_sentence = ""

            if current_sentence and len(current_sentence) >= self.min_chars:
                sentences.append(current_sentence)

        # 恢复代码块或转为图片/文件
        final_sentences = []
        for sentence in sentences:
            if "__CODE_BLOCK_" in sentence:
                for i, code in enumerate(self.code_blocks):
                    placeholder = f"__CODE_BLOCK_{i}__"
                    if sentence == placeholder:
                        # 直接返回代码块（或其处理结果）
                        sentence = f"[Code block {i} processed]"
                    else:
                        sentence = sentence.replace(placeholder, f"[Code block {i} processed]")
            final_sentences.append(sentence)

        # 处理代码块：生成图片和文件
        code_results = []
        for i, code in enumerate(self.code_blocks):
            # 保存为文件
            file_path = os.path.join(output_dir, f"code_block_{i}.py")
            self.code_to_file(code, file_path)
            
            # 生成图片
            image_path = os.path.join(output_dir, f"code_block_{i}.png")
            self.code_to_image(code, image_path)
            
            code_results.append({"file": file_path, "image": image_path})

        return final_sentences, code_results

    def _find_split_pos(self, text):
        for i in range(self.max_chars, self.min_chars-1, -1):
            if text[i-1] in [' ', '，', '。', ',', '.', '!', '?']:
                return i
        return -1

    def code_to_file(self, code, file_path):
        """将代码保存为文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(code.strip())
        return file_path

    def code_to_image(self, code, image_path, theme="monokai"):
        """将代码转为高亮图片（使用imgkit）"""
        # 用Pygments高亮代码
        formatter = HtmlFormatter(style=theme, full=True, cssclass="source")
        html_code = highlight(code, PythonLexer(), formatter)
        
        # 用imgkit将HTML转为图片
        imgkit.from_string(html_code, image_path, options={'quiet': ''})
        return image_path

    def code_to_image_pillow(self, code, image_path, font_path=None, font_size=14):
        """备用方案：用Pillow直接渲染代码为图片"""
        lines = code.split('\n')
        max_width = max(len(line) for line in lines) * font_size // 2
        line_height = font_size + 5
        height = len(lines) * line_height + 20

        # 创建图像
        image = Image.new('RGB', (max_width + 20, height), color=(30, 30, 30))
        draw = ImageDraw.Draw(image)
        
        # 加载字体（默认用Pillow自带，或指定路径）
        try:
            font = ImageFont.truetype(font_path or "arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # 绘制代码
        for i, line in enumerate(lines):
            draw.text((10, 10 + i * line_height), line, font=font, fill=(255, 255, 255))

        image.save(image_path)
        return image_path