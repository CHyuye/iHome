from . import api
from ihome.utils.captcha.captcha import captcha
from ihome.utils.response_code import RET
from ihome import redis_store, constants, db
from flask import current_app, make_response, jsonify, request
from ihome.models import User
from ihome.libs.yuntongxun.sms import CCP
from ihome.tasks.task_sms import send_sms
import random

# RESTful后端接口命名风格
# GET 127.0.0.1:5000/api/v1.0/image_codes/<image_code_id>
@api.route("/image_codes/<image_code_id>")
def get_image_code(image_code_id):
	"""
	获取图片验证码
	:param image_code_id: 前端传递的图片验证编号
	:return: 正常：验证码图片， 异常：返回json
	"""
	# 1.获取参数
	# 2.检验参数
	# 3.业务逻辑处理，前两步已在前端请求后端接口，肯定的先完成前两步
	# 4.生成验证码图片
	# 名字，真实文本 图片数据
	name, text, image_data = captcha.generate_captcha()
	# 5.将验证码真实值与编号存入redis中,设置有效期
	# redis类型： 字符串，列表，哈希，set
	# "key": xxxx
	# 使用哈希维护有效期的时候只能整体设置，所以达不到要求，故使用字符串
	# "image_codes" {"id1":"abc", "":""} 哈希 hset("image_codes":"id1")

	# 单条维护记录，选用字符串
	# "image_code_编号": "真实值"
	# redis_store.set("image_code_%s" % image_code_id, text)
	# redis_store.expire("image_code_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES)

	# 合并为一步，setex方法    记录名字                     有效期                             真实文本
	try:
		redis_store.setex("image_code_%s" % image_code_id, constants.IMAGE_CODE_REDIS_EXPIRES, text)
	except Exception as e:
		# 记录日志，发生的数据库错误信息
		current_app.logger.error(e)
		# 数据库发生异常的话，需传递json错误参数给前端，本来使用该用英文的
		# return jsonify(error=RET.DBERR, errmsg="Save image code id is failed.")
		return jsonify(errno=RET.DBERR, errmsg="保存图片验证码失败")

	# 6.返回图片
	# 设置图片返回的格式
	resp = make_response(image_data)
	resp.headers["Content-Type"] = "image/jpg"
	return resp


# GET /api/v1.0/sms_codes/<mobile>?image_code=xxx&image_code_id=xxx
# @api.route("/sms_codes/<re(r'1[345789]\d{9}'):mobile>")
# def get_sms_code(mobile):
# 	"""
# 	根据用户输入的手机号，获取短信验证码
# 	:param mobile: 用户输入的手机号
# 	:return: 短信验证码
# 	"""
# 	# 获取参数
# 	image_code = request.args.get("image_code")
# 	image_code_id = request.args.get("image_code_id")
#
# 	# 校验参数
# 	if not all([image_code_id, image_code]):
# 		# 表示参数不完整
# 		return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")
#
# 	# 业务逻辑处理
# 	# 从redis中取出真实的图片验证码
# 	try:
# 		real_image_code = redis_store.get("image_code_%s" % image_code_id)
# 	except Exception as e:
# 		current_app.logger.error(e)
# 		return jsonify(errno=RET.DBERR, errmsg="redis数据库异常")
#
# 	# 与用户填写的值进行对比
# 	if real_image_code.lower().decode() != image_code.lower():
# 		# 表示用户填写错误
# 		return jsonify(errno=RET.DATAERR, errmsg="图片验证码错误")
#
# 	# 判断验证码是否过期
# 	if real_image_code is None:
# 		#  表示图片验证码没有或过期
# 		return jsonify(errno=RET.NODATA, errmsg="图片验证码失效")
#
# 	# 删除redis中的图片验证码，防止用户使用一个验证码验证多次
# 	try:
# 		redis_store.delete("image_code_%s" % image_code_id)
# 	except Exception as e:
# 		current_app.logger.error(e)
#
# 	# 判断对于这个手机号的操作，在60秒内有没有之前的记录，如果有则认为该用户操作频繁，不接受处理
# 	try:
# 		send_flag = redis_store.get("send_sms_code_%s" % mobile)
# 	except Exception as e:
# 		current_app.logger.error(e)
# 	else:
# 		if send_flag is not None:
# 			# 表示在60秒内之前有发送的记录
# 			return jsonify(errno=RET.REQERR, errmsg="请求过于频繁，请60秒后重试")
#
# 	# 判断手机号是否存在
# 	try:
# 		user = User.query.filter_by(mobile=mobile).first()
# 	except Exception as e:
# 		current_app.logger.error(e)
# 	else:
# 		if user is not None:
# 			# 表示手机号已存在
# 			return jsonify(errno=RET.DATAEXIST, errmsg="手机号已注册")
#
# 	# 如果手机号不存在，则生成短信验证码
# 	sms_code = "%06d" % random.randint(0, 999999)  # 随机生成6位数,不够的前面补零
#
# 	# 保存真实的短信验证码
# 	try:
# 		redis_store.setex("sms_code_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
# 		# 保存发送给这个手机号的记录，防止用户在60s内再次发送短信的操作
# 		# redis_store.setex("send_sms_code_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
# 	except Exception as e:
# 		current_app.logger.error(e)
# 		return jsonify(errno=RET.DBERR, errmsg="保存短信验证码异常")
#
# 	# 发送短信
# 	try:
# 		ccp = CCP()
# 		result = ccp.send_template_sms(mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES/60)], 1)
# 	except Exception as e:
# 		current_app.logger.error(e)
# 		return jsonify(errno=RET.THIRDERR, errmsg="发送异常")
#
# 	# 返回值
# 	if result == 0:
# 		# 发送成功
# 		return jsonify(errno=RET.OK, errmsg="发送成功")
# 	else:
# 		# 发送失败
# 		return jsonify(errno=RET.THIRDERR, errmsg="发送失败")


@api.route("/sms_codes/<re(r'1[345789]\d{9}'):mobile>")
def get_sms_code(mobile):
	"""
	根据用户输入的手机号，获取短信验证码
	:param mobile: 用户输入的手机号
	:return: 短信验证码
	"""
	# 获取参数
	image_code = request.args.get("image_code")
	image_code_id = request.args.get("image_code_id")

	# 校验参数
	if not all([image_code_id, image_code]):
		# 表示参数不完整
		return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

	# 业务逻辑处理
	# 从redis中取出真实的图片验证码
	try:
		real_image_code = redis_store.get("image_code_%s" % image_code_id)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="redis数据库异常")

	# 与用户填写的值进行对比
	if real_image_code.lower().decode() != image_code.lower():
		# 表示用户填写错误
		return jsonify(errno=RET.DATAERR, errmsg="图片验证码错误")

	# 判断验证码是否过期
	if real_image_code is None:
		#  表示图片验证码没有或过期
		return jsonify(errno=RET.NODATA, errmsg="图片验证码失效")

	# 删除redis中的图片验证码，防止用户使用一个验证码验证多次
	try:
		redis_store.delete("image_code_%s" % image_code_id)
	except Exception as e:
		current_app.logger.error(e)

	# 判断对于这个手机号的操作，在60秒内有没有之前的记录，如果有则认为该用户操作频繁，不接受处理
	try:
		send_flag = redis_store.get("send_sms_code_%s" % mobile)
	except Exception as e:
		current_app.logger.error(e)
	else:
		if send_flag is not None:
			# 表示在60秒内之前有发送的记录
			return jsonify(errno=RET.REQERR, errmsg="请求过于频繁，请60秒后重试")

	# 判断手机号是否存在
	try:
		user = User.query.filter_by(mobile=mobile).first()
	except Exception as e:
		current_app.logger.error(e)
	else:
		if user is not None:
			# 表示手机号已存在
			return jsonify(errno=RET.DATAEXIST, errmsg="手机号已注册")

	# 如果手机号不存在，则生成短信验证码
	sms_code = "%06d" % random.randint(0, 999999)  # 随机生成6位数,不够的前面补零

	# 保存真实的短信验证码
	try:
		redis_store.setex("sms_code_%s" % mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_code)
		# 保存发送给这个手机号的记录，防止用户在60s内再次发送短信的操作
		# redis_store.setex("send_sms_code_%s" % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="保存短信验证码异常")

	# 发送短信
	# try:
	# 	ccp = CCP()
	# 	result = ccp.send_template_sms(mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES/60)], 1)
	# except Exception as e:
	# 	current_app.logger.error(e)
	# 	return jsonify(errno=RET.THIRDERR, errmsg="发送异常")

	# 通过引入celery异步发送短信，delay函数调用后立即返回
	send_sms.delay(mobile, [sms_code, int(constants.SMS_CODE_REDIS_EXPIRES/60)], 1)

	# 返回值
	# if result == 0:
	# 通过celery发送异步消息，保证它一定发送成功
	return jsonify(errno=RET.OK, errmsg="发送成功")
	# else:
	# 	# 发送失败
	# 	return jsonify(errno=RET.THIRDERR, errmsg="发送失败")
