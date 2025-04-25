from nonebot.plugin import PluginMetadata

from .ai_chat import MainWalk

__plugin_meta__ = PluginMetadata(
    name="示例插件",
    description="这是一个示例插件",
    usage="没什么用",
    type="application",
    config=MainWalk,
    extra={},
)