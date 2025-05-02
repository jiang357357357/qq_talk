from nonebot.plugin import PluginMetadata

from .task import AiManager

__plugin_meta__ = PluginMetadata(
    name="任务插件",
    description="这是一个任务插件",
    usage="",
    type="application",
    config=AiManager,
    extra={},
)