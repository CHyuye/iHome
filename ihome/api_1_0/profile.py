from . import api
from ihome.utils.commons import login_required
from flask import g, request, jsonify, current_app, session
from ihome.utils.response_code import RET
from ihome.utils.image_storage import storage
from ihome.models import User
from ihome import db, constants


@api.route("/users/avatar", methods=["POST"])
@login_required
def set_user_avatar():
	"""
	设置用户头像
	前端传递参数：图片（多媒体表单），用户ID
	:return:
	"""
	# 获取参数,装饰器login_required中已经保存了user_id，所以g对象直接取
	user_id = g.user_id

	# 获取图片
	image_file = request.files.get("avatar")

	if image_file is None:
		return jsonify(errno=RET.PARAMERR, errmsg="未上传图片")

	# 调用七牛上传图片，返回文件名
	try:
		file_name = storage(image_file)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.THIRDERR, errmsg="上传图片失败")

	# 保存文件名到数据库中
	try:
		User.query.filter_by(id=user_id).update({"avatar_url": file_name})
		# 数据库提交
		db.session.commit()
	except Exception as e:
		# 失败数据库回滚
		db.session.rollback()
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="保存图片失败")

	avatar_url = constants.QINIU_URL_DOMAIN + file_name
	# 保存成功，返回给前端图片地址
	return jsonify(errno=RET.OK, errmsg="上传成功", data={"avatar_url": avatar_url})


@api.route("/users/name", methods=["POST"])
@login_required
def set_user_name():
	"""
	设置用户名
	前端传递参数，用户名，json格式
	:return:
	"""
	# 获取参数,装饰器login_required中已经保存了user_id，所以g对象直接取
	user_id = g.user_id

	# 获取用户名
	rep_dict = request.get_json()
	name = rep_dict.get("name")

	# 检验参数是否填写
	if not all([name]):
		return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

	# 业务逻辑处理
	# 添加更新用户名到数据库中
	try:
		User.query.filter_by(id=user_id).updata({"name": name})
		# 数据库提交
		db.session.commit()
	except Exception as e:
		# 数据库回滚
		db.session.rollback()
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="保存失败")
	# 查询用户名是否已存在，判断重名
	# 保存成功，返回结果
	return jsonify(errno=RET.OK, errmsg="保存成功", data={"name": name})


@api.route("/user", methods=["GET"])
@login_required
def get_user_profile():
	"""
	在个人信息页面展示用户信息
	从后端数据库查询用户名和手机号参数，传递给前端展示，json格式
	:return:
	"""
	# 获取参数,装饰器login_required中已经保存了user_id，所以g对象直接取
	user_id = g.user_id

	# 根据user_id获取用户信息
	try:
		user = User.query.get(user_id)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

	# 判断一下user是否为空
	if user is None:
		return jsonify(errno=RET.NODATA, errmsg="无效操作")

	return jsonify(errno=RET.OK, errmsg="OK", data=user.to_dict())


@api.route("/users/name", methods=["PUT"])
@login_required
def change_user_name():
	"""修改用户名"""
	# 获取user的id
	user_id = g.user_id
	# 获取用户名参数
	resp_dict = request.get_json()

	# 判断数据完整性
	if resp_dict is None:
		return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

	# 判断用户名输入是否为空
	name = resp_dict.get("name")
	if not name:
		return jsonify(errnp=RET.PARAMERR, errmsg="用户名不能为空")

	# 更新到数据库，同时利用数据库的唯一索引，判断是否重复
	try:
		User.query.filter_by(id=user_id).update({"name": name})
		db.session.commit()
	except Exception as e:
		db.session.rollback()
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="设置用户名失败")

	# 更新session用户名状态
	session["name"] = name
	# 返回结果
	return jsonify(errno=RET.OK, errmsg="修改成功")


@api.route("/users/auth", methods=["GET"])
@login_required
def get_user_author():
	"""
	获取用户真实信息认证
	:return:
	"""
	# 获取参数,装饰器login_required中已经保存了user_id，所以g对象直接取
	user_id = g.user_id

	# 根据user_id获取用户信息
	try:
		user = User.query.get(user_id)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="获取用户信息失败")

	# 判断一下user是否为空
	if user is None:
		return jsonify(errno=RET.NODATA, errmsg="无效操作")

	# 返回查询结果
	return jsonify(errno=RET.OK, errmsg="OK", data=user.auth_to_dict())


@api.route("/users/auth", methods=["POST"])
@login_required
def set_user_auth():
	"""
	保存用户实名认证信息
	参数：真实姓名，身份证
	格式：json
	:return:
	"""
	# 获取用户id
	user_id = g.user_id

	# 获取真实姓名，身份证
	req_dict = request.get_json()
	if not req_dict:
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

	real_name = req_dict.get("real_name")  # 真实姓名
	id_card = req_dict.get("id_card")  # 身份证

	# 检验参数完整性
	if not all([real_name, id_card]):
		return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

	# 保存到数据库
	try:
		# 只有当真实姓名和身份证为空时，才允许设置
		User.query.filter_by(id=user_id, real_name=None, id_card=None).\
			update({"real_name": real_name, "id_card": id_card})
		db.session.commit()
	except Exception as e:
		db.session.rollback()
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="保存实名信息失败")

	# 返回结果
	return jsonify(errno=RET.OK, errmsg="OK")


