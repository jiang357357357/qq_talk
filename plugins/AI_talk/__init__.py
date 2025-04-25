from nonebot.plugin import PluginMetadata

from .ai_talk import AiManager

__plugin_meta__ = PluginMetadata(
    name="聊天插件",
    description="这是一个聊天插件",
    usage="",
    type="application",
    config=AiManager,
    extra={},
)