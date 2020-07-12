# coding=gbk

# coding=utf-8

# -*- coding: UTF-8 -*-

from ihome.libs.yuntongxun.CCPRestSDK import REST
import configparser

# ���ʺ�
accountSid = '8aaf07087172a6ee017178f9ff3d03c0'

# ���ʺ�Token
accountToken = 'af110de6457a446c8bd554a08e13a186'

# Ӧ��Id
appId = '8aaf07087172a6ee017178f9ffa103c7'

# �����ַ����ʽ���£�����Ҫдhttp://
serverIP = 'app.cloopen.com'

# ����˿�
serverPort = '8883'

# REST�汾��
softVersion = '2013-12-26'


# ����ģ�����
# @param to �ֻ�����
# @param datas �������� ��ʽΪ���� ���磺['12','34']���粻���滻���� ''
# @param $tempId ģ��Id


class CCP(object):
	"""�Լ���װ���Ͷ��ŵĸ�����"""
	# ������������������
	instance = None

	def __new__(cls):
		"""��������������ԭ������REST�Ĵ���������һ�Σ�֮��ֱ�ӷ���"""
		# �ж�CCP����û���Ѿ������Ķ������û�У�����һ�����󣬲��ұ���
		if cls.instance is None:
			obj = super(CCP, cls).__new__(cls)

			# ��ʼ��REST SDK
			obj.rest = REST(serverIP, serverPort, softVersion)
			obj.rest.setAccount(accountSid, accountToken)
			obj.rest.setAppId(appId)

			# ���������Դ��������
			cls.instance = obj
		# ����У��򽫱���Ķ���ֱ�ӷ���
		return cls.instance

	# sendTemplateSMS(�ֻ�����,��������,ģ��Id)
	def send_template_sms(self, to, datas, temp_id):
		"""���Ͷ���"""
		# ���յ�һ���ֵ�
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
			# ��ʾ���ͳɹ�
			return 0
		else:
			# ������Ϣʧ��
			return -1


if __name__ == '__main__':
	ccp = CCP()
	ccp.send_template_sms("19946238583", ["1025", "1"], 1)
