# coding=gbk

# coding=utf-8

# -*- coding: UTF-8 -*-

from ihome.libs.yuntongxun.CCPRestSDK import REST
import configparser

# 主帐号
accountSid = '8aaf07087172a6ee017178f9ff3d03c0'

# 主帐号Token
accountToken = 'af110de6457a446c8bd554a08e13a186'

# 应用Id
appId = '8aaf07087172a6ee017178f9ffa103c7'

# 请求地址，格式如下，不需要写http://
serverIP = 'app.cloopen.com'

# 请求端口
serverPort = '8883'

# REST版本号
softVersion = '2013-12-26'


# 发送模板短信
# @param to 手机号码
# @param datas 内容数据 格式为数组 例如：['12','34']，如不需替换请填 ''
# @param $tempId 模板Id


class CCP(object):
	"""自己封装发送短信的辅助类"""
	# 用来保存对象的类属性
	instance = None

	def __new__(cls):
		"""单例方法，减少原有请求REST的次数，请求一次，之后直接返回"""
		# 判断CCP类有没有已经创建的对象，如果没有，创建一个对象，并且保存
		if cls.instance is None:
			obj = super(CCP, cls).__new__(cls)

			# 初始化REST SDK
			obj.rest = REST(serverIP, serverPort, softVersion)
			obj.rest.setAccount(accountSid, accountToken)
			obj.rest.setAppId(appId)

			# 设置类属性创建类对象
			cls.instance = obj
		# 如果有，则将保存的对象直接返回
		return cls.instance

	# sendTemplateSMS(手机号码,内容数据,模板Id)
	def send_template_sms(self, to, datas, temp_id):
		"""发送短信"""
		# 接收到一个字典
		result = self.rest.sendTemplateSMS(to, datas, temp_id)
		# for k, v in result.items():
		# 	if k == 'templateSMS':
		# 		for k, s in v.items():
		# 			print('%s:%s' % (k, s))
		# 	else:
		# 		print('%s:%s' % (k, v))
		# 	statusCode: 000000
		# 	smsMessageSid: 4
		# 	c58fa97aaf1415c84cfb5d8a2ae3a69
		# 	dateCreated: 20200414223133
		status_code = result.get("statusCode")
		if status_code == '000000':
			# 表示发送成功
			return 0
		else:
			# 发送信息失败
			return -1


if __name__ == '__main__':
	ccp = CCP()
	ccp.send_template_sms("19946238583", ["1025", "1"], 1)
