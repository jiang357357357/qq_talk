import random
from nonebot import require,on_metaevent
from nonebot.adapters.onebot.v11 import MetaEvent
from datetime import datetime, timedelta
from plugins.Task.task import ScheduledMessage
from nonebot import logger,get_bot

from nonebot_plugin_apscheduler import scheduler

logger.info("主要任务插件载入完成")

# 在 NoneBot 启动时初始化 ScheduledMessage
scheduled_message = ScheduledMessage()

pro_ids = []

# 定义随机的主任务
# 设置定时器
# 定义每天触发的任务
async def my_main_task(pro_qq="2740954024"):
    random_hours = random.randint(0, 24)
    random_minutes = random.randint(0, 59)
    await scheduled_message.send_and_store_message(pro_qq,user_text='')

    logger.info(f"测试任务已安排: 向 {pro_qq} 发送消息")



# 设置定时器
# 定义每天触发的任务
async def schedule_test_task(pro_qq="2740954024",user_text="(用户已经八小时未回你)"):
    return_text = await scheduled_message.send_and_store_message(pro_qq,user_text)
    if not return_text:
        logger.info(f"最近 {pro_qq} 刚刚聊过")
    logger.info(f"测试任务已安排: 向 {pro_qq} 发送消息")

scheduler.add_job(
    schedule_test_task, "cron",hour='11', minute='12', id="job_1"
)


    