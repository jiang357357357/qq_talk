from nonebot import require,on_metaevent
from nonebot.adapters.onebot.v11 import MetaEvent
from datetime import datetime, timedelta
from plugins.Task.task import ScheduledMessage
from nonebot import logger,get_bot

from nonebot_plugin_apscheduler import scheduler

logger.info("主要任务插件载入完成")

# 在 NoneBot 启动时初始化 ScheduledMessage
scheduled_message = ScheduledMessage()


# 设置定时器
# 定义每天触发的任务
async def schedule_test_task(pro_qq="2740954024",user_text="(用户已经八小时未回你)"):
    test_qq_number = "2740954024"  # 测试用 QQ 号
    await scheduled_message.send_and_store_message(pro_qq,user_text)
    logger.info(f"测试任务已安排: 向 {test_qq_number} 发送消息")

scheduler.add_job(
    schedule_test_task, "cron",hour='17', minute='27', id="job_1"
)


    