from . import api
from flask import request, jsonify, current_app, session
from ihome.utils.response_code import RET
from ihome import redis_store, db, constants
from ihome.models import User
from sqlalchemy.exc import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
import re


@api.route("/users", methods=["POST"])
def register():
	"""
	注册函数
	请求的参数：手机号 短信验证码 密码 确认密码
	前端参数的格式：json
	:return:
	"""
	# 获取请求的json数据，返回字典
	req_dict = request.get_json()

	mobile = req_dict.get("mobile")  # 手机号
	sms_code = req_dict.get("sms_code")  # 短信验证码
	password = req_dict.get("password")  # 密码
	check_pwd = req_dict.get("check_pwd")  # 确认密码

	# 检验参数完整性
	if not all([mobile, sms_code, password, check_pwd]):
		return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

	# 判断手机号格式
	if not re.match(r"1[345789]\d{9}", mobile):
		# 表示手机格式不对
		return jsonify(errno=RET.PARAMERR, errmsg="手机格式错误")

	# 判断两次密码是否一致
	if password != check_pwd:
		return jsonify(errno=RET.PARAMERR, errmsg="两次密码不一致")

	# 从redis中取出短信验证码
	try:
		real_sms_code = redis_store.get("sms_code_%s" % mobile)
	except Exception as e:
		current_app.logger(e)
		return jsonify(errno=RET.DBERR, errmsg="获取短信验证码失败")

	# 判断短信验证码是否过期
	if real_sms_code is None:
		return jsonify(errno=RET.NODATA, errmsg="短信验证码失效")

	# 删除redis中的短信验证码，防止重复使用
	try:
		redis_store.delete("sms_code_%s" % mobile)
	except Exception as e:
		current_app.logger(e)

	# 判断用户填写的短信验证码是否正确
	print(real_sms_code)
	print(sms_code)
	if real_sms_code != sms_code:
		return jsonify(RET.DATAERR, errmsg="短信验证码输入错误")

	# 判断用户的手机号是否注册过 -- 这步可以省略，因为User模型类创建时，mobile就是不可重复的
	# try:
	# 	user = User.query.filter_by(mobile=mobile).first()
	# except Exception as e:
	# 	current_app.logger(e)
	# 	return jsonify(RET.DBERR, errmsg="数据库异常")
	# else:
	# 	if user is not None:
	# 		# 表示手机号已存在
	# 		return jsonify(RET.DATAEXIST, errmsg="手机号已存在")

	# 密码加密 盐值 salt
	#        用户密码              盐值   加密算法   加密后的数
	# 用户1  password="123456" + 'abc' sha1 --> abc$coawenfoijaohanuif

	# 用户登录解密过程：password="123456"(密码)  'abc'(盐值) sha256(加密算法)  djfioawovhaoe(结果值)

	# 保存用户的注册数据到数据库 -- 节省到这一步，在保存时，mobile重复报错，减少mysql1操作
	# todo:密码加密
	user = User(name=mobile, mobile=mobile)
	# user.generate_password_hash(password)

	user.password = password  # 设置属性

	try:
		db.session.add(user)
		db.session.commit()
	except IntegrityError as e:
		# 数据库操作错误后，后滚
		db.session.rollback()
		# 表示手机号出现了重复值
		current_app.logger(e)
		return jsonify(RET.DATAEXIST, errmsg="手机号已存在")
	except Exception as e:
		# 其他异常
		current_app.logger(e)
		return jsonify(RET.DBERR, errmsg="数据库操作异常")

	# 保存用户的登录状态到session中
	session["name"] = mobile
	session["mobile"] = mobile
	session["user_id"] = user.id

	# 返回结果
	return jsonify(errno=RET.OK, errmsg="注册成功")


@api.route("/sessions", methods=["POST"])
def login():
	"""
	登录函数——实现用户登录操作
	请求参数:手机号, 密码
	前端传递参数格式：json （后端数据库手机号和密码进行比对）
	:return:成功会失败的结果
	"""
	# 获取参数
	req_dict = request.get_json()
	mobile = req_dict.get("mobile")
	password = req_dict.get("password")

	# 业务逻辑处理
	# 检验数据完整
	if not all([mobile, password]):
		return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

	# 检验手机号格式
	if not re.match(r"1[34689]\d{9}", mobile):
		return jsonify(errno=RET.PARAMERR, errmsg="手机号格式不正确")

	# 判断用户登录错误次数，超过限制，则返回停止一下操作
	# 使用redis存储用户登录次数，String类型 redis次数："access_num_%s": 次数
	user_ip = request.remote_addr  # 获取用户IP地址
	try:
		access_nums = redis_store.get("access_num_%s" % user_ip)
	except Exception as e:
		current_app.logger.error(e)
	else:
		# 用户登录次数不是None而且错误次数超过限制数
		if access_nums is not None and int(access_nums) >= constants.LOGIN_ERROR_MAX_TIMES:
			return jsonify(errno=RET.REQERR, errmsg="错误次数过多，请稍后重试")

	# 从数据库中根据手机号查询用户对象
	try:
		user = User.query.filter_by(mobile=mobile).first()
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

	# 用数据库中的密码对比用户输入的密码，但不能对前端透露太多
	# if user is None or user.check_password(password) is False:
	if user is None or not user.check_password(password):
		try:
			redis_store.incr("access_num_%s" % user_ip)
			redis_store.expire("access_num_%s" % user_ip, constants.LOGIN_ERROR_FORBID_TIMES)
		except Exception as e:
			current_app.logger.error(e)

		return jsonify(errno=RET.DATAERR, errmsg="用户名或密码错误")

	# 如果验证通过，保存用户状态，返回结果
	session["name"] = user.name
	session["mobile"] = user.mobile
	session["user_id"] = user.id

	return jsonify(errno=RET.OK, errmsg="登录成功")


@api.route("/session", methods=["GET"])
def check_login():
	"""
	检查用户的登录状态
	:return: 返回登录信息
	"""
	# 尝试从session中获取用户的名字
	name = session.get("name")
	# 如果session中name存在，则表示用户已登录，否则未登录
	if name is not None:
		return jsonify(errno=RET.OK, errmsg="true", data={"name": name})
	else:
		return jsonify(errno=RET.SESSIONERR, errmsg="false")


@api.route("/session", methods=["DELETE"])
def logout():
	"""
	用户退出登录
	:return:
	"""
	# 解决退出登录后，csrf_token登录缺失的bug问题，因为Flask会给csrf_token设置到session中
	# 所以一次性全部清除，就会给下一次登录留下csrf_token缺失
	csrf_token = session.get("csrf_token")
	# 清除session数据
	session.clear()
	session["csrf_token"] = csrf_token
	# 返回结果
	return jsonify(errno=RET.OK, errmsg="退出成功")
