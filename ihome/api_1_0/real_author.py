from . import api
from flask import g, current_app, session, jsonify, request
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET
from ihome.models import User
from ihome import db, constants


@api.route("/user", methods=["GET"])
def get_user_info():
	"""
	个人主页中获取用户信息
	包括：用户头像，
	要求：json格式
	:return:
	"""
	# 获取参数,装饰器login_required中已经保存了user_id，所以g对象直接取
	user_id = g.user_id

	# 如果用户已登录