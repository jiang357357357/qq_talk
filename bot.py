import nonebot
from nonebot.adapters.onebot.v11 import Adapter
import os
import sys
from nonebot.plugin import Plugin

from pathlib import Path




# 获取 bot.py 所在的目录
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 使用相对路径加载 .env 和 pyproject.toml
ENV_PATH = os.path.join(BASE_DIR, ".env")
TOML_PATH = os.path.join(BASE_DIR, "pyproject.toml")

# 检查文件是否存在
if not os.path.exists(ENV_PATH):
    raise FileNotFoundError(f".env file not found at {ENV_PATH}")
if not os.path.exists(TOML_PATH):
    raise FileNotFoundError(f"pyproject.toml file not found at {TOML_PATH}")

nonebot.init(_env_file=ENV_PATH)
app = nonebot.get_asgi()

driver = nonebot.get_driver()
driver.register_adapter(Adapter)

nonebot.load_from_toml(TOML_PATH)

if __name__ == "__main__":
    plugin: Plugin | None = nonebot.get_plugin("ai_main")
    from plugins.main.ai_chat import MainWalk
    nonebot.run()