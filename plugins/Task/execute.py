import random
from nonebot import require,on_metaevent
from nonebot.adapters.onebot.v11 import MetaEvent
from datetime import datetime, timedelta
from plugins.Task.task import ScheduledMessage
from nonebot import logger,get_bot

from nonebot_plugin_apscheduler import scheduler
from plugins.Task.text import conversation_topics

logger.info("主要任务插件载入完成")

# 在 NoneBot 启动时初始化 ScheduledMessage
scheduled_message = ScheduledMessage()

pro_ids = []


# 定义随机的主任务,然后在主任务里随机触发子任务
async def my_main_task(pro_qq="2740954024"):
    job_id = f"sub_task_{datetime.now().strftime('%Y%m%d%H%M%S')}"
    random_hours = random.randint(0, 24)
    random_minutes = random.randint(0, 59)
    logger.info(f"测试任务已安排: 向 {pro_qq} 发送消息")
    scheduler.add_job(
        my_sub_task, "cron",
        hour=str(random_hours),
        minute=str(random_minutes), 
        max_instances=1,
        id=job_id,
        name=f"RandomMessageTask_{job_id}",
    )
    logger.info(f"测试任务已安排: {random_hours}小时{random_minutes}分钟后向 {pro_qq} 发送消息")

#子任务的内容
async def my_sub_task(pro_qq="2740954024"):
    # 获取新话题
    category = random.choice(conversation_topics)
    # 随机选择该分类下的一个问题
    question = random.choice(category["questions"])
    input_question = f"(你想到了一个问题:'{question}',想要与用户交流)"
    return_text = await scheduled_message.send_and_store_message(pro_qq,input_question)
    if not return_text:
        logger.info(f"最近 {pro_qq} 刚刚聊过")
    else:
        logger.info(f"测试任务已安排: 向 {pro_qq} 发送消息")

# 发布主任务
# 设置定时任务，每八小时触发一次
scheduler.add_job(
    my_main_task,
    "cron",
    hour='17', 
    minute='24', 
    id="job_1"
)


# # 设置定时器
# # 定义每天触发的任务
# async def schedule_test_task(pro_qq="2740954024",user_text="(用户已经八小时未回你)"):
#     return_text = await scheduled_message.send_and_store_message(pro_qq,user_text)
#     if not return_text:
#         logger.info(f"最近 {pro_qq} 刚刚聊过")
#     else:
#         logger.info(f"测试任务已安排: 向 {pro_qq} 发送消息")


# # 测试用
# scheduler.add_job(
#     my_sub_task, "cron",hour='17', minute='20', id="job_1"
# )
# # my_sub_task