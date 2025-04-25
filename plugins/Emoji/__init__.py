from nonebot.plugin import PluginMetadata

from .emojis import EmojiManager

__plugin_meta__ = PluginMetadata(
    name="表情包插件",
    description="这是一个表情包插件",
    usage="没什么用",
    type="application",
    config=EmojiManager,
    extra={},
)