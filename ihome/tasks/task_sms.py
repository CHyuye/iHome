from celery import Celery
from ihome.libs.yuntongxun.sms import CCP


celery_app = Celery("ihome", broker="redis://192.168.232.141:6379/1")


@celery_app.task
def send_sms(to, datas, temp_id):
	"""celery实现异步发送消息"""
	ccp = CCP()
	ccp.send_template_sms(to, datas, temp_id)
