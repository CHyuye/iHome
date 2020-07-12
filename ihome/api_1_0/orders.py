import datetime
from . import api
from flask import request, g, current_app, jsonify
from ihome import redis_store, db
from ihome.models import House, Order
from ihome.utils.commons import login_required
from ihome.utils.response_code import RET


# 127.0.0.1:5000/api/v1.0/order/house_id  POST请求
@api.route("/order", methods=["POST"])
def save_order():
	"""
	保存订单
	需要参数：用户id，房屋id，入住日期
	数据格式：json
	:return:
	"""
	# 获取用户id
	user_id = g.user_id
	# 获取参数，房屋id，入住时间，结束时间
	order_data = request.get_json()
	if not order_data:
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

	house_id = order_data.get("house_id")  # 预订的房屋编号
	start_date_str = order_data.get("start_date")  # 入住时间
	end_date_str = order_data.get("end_date")  # 结束时间

	# 检验参数
	if not all([house_id, start_date_str, end_date_str]):
		return jsonify(errno=RET.PARAMERR, errmsg="参数不完整")

	# 处理时间
	try:
		# 转换时间格式，计算入住的天数
		start_date = datetime.datetime.strptime(start_date_str, "%Y-%m-%d")
		end_date = datetime.datetime.strptime(end_date_str, "%Y-%m-%d")
		assert start_date <= end_date

		# 计算入住天数，需额外加一
		days = (end_date - start_date).days + 1  # datetime.timedelta
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.PARAMERR, errmsg="日期格式错误")

	# 判断房子是否存在
	try:
		house = House.query.get(house_id)
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库异常")

	if not house:
		return jsonify(errno=RET.NODATA, errmsg="房屋信息不存在")

	# 判断预定用户是否是房东本人
	if user_id == house.user_id:
		return jsonify(errno=RET.ROLEERR, errmsg="不能预订自己的房屋")

	# 判断这段时间内房屋是否被下单
	try:
		# 查询时间冲突的订单数
		count = Order.query.filter(Order.house_id == house_id, Order.begin_date <= end_date, Order.end_date >= start_date).count()
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="检查出错，请稍后重试！")
	if count > 0:
		return jsonify(errno=RET.DATAERR, errmsg="房屋已被预订")

	# 计算总额
	amount = days * house.price

	# 保存数据
	order = Order(
		user_id=user_id,
		house_id=house_id,
		begin_data=start_date,
		end_date=end_date,
		days=days,
		house_price=house.price,
		amount=amount
	)

	try:
		db.session.add(order)
		db.session.commit()
	except Exception as e:
		current_app.logger.error(e)
		db.session.rollback()
		return jsonify(errno=RET.DBERR, errmsg="保存订单失败")

	# 返回结果
	return jsonify(errno=RET.OK, errmsg="OK", data={"order_id": order.id})


# /api/v1.0/user/orders?role=custom（顾客）     role=landlord（房东）
@api.route("/user/orders", methods=["GET"])
@login_required
def get_user_order():
	"""
	查询用户信息
	GET请求
	:return:
	"""
	# 获取用户id
	user_id = g.user_id
	# 获取用户点击的是“我的订单” 还是”用户订单“参数
	# 用户的身份，用户想要查询作为房客预订别人房子的订单，还是想要作为房东查询别人预订自己房子的订单
	role = request.args("role", "")

	# 查询订单信息
	try:
		# 如果是房主（客户订单）
		if "landlord" == role:
			# 以房东的身份查询，先查询自己的房子有哪些
			houses = House.query.filter(House.user_id == user_id).all()
			houses_ids = [house.id for house in  houses]  # 遍历取出所有房子id
			# 在查询预定了自己房子的订单
			orders = Order.query.filter(Order.house_id.in_(houses_ids)).order_by(Order.create_time.desc()).all()
		else:
			# 否则是客户（显示我的订单）
			orders = Order.query.filter(Order.user_id == user_id).order_by(Order.create_time.desc()).all()
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="订单查询失败！")

	# 将数据转换为字典
	orders_dict_list = []
	if orders:
		for order in orders:
			orders_dict_list.append(order.to_dict())
	# 返回结果
	return jsonify(errno=RET.OK, errmsg="OK", data={"orders": orders_dict_list})


# 接单和拒单是房东的权限，即在“客户订单”页面，如果有客户预定了该房东的房子，会显示在该页面，并显示接单和拒单的按钮
# URL：127.0.0.1:5000/api/v1.0/orders/orderId/status
# 请求方式：PUT
@api.route("/orders/<int:order_id>/status", methods=["PUT"])
@login_required
def accept_reject_order(order_id):
	"""
	接单，拒单
	:param order_id: 订单id
	:return:
	"""
	# 获取用户id
	user_id = g.user_id
	# 获取请求方式（接单，拒单）
	req_data = request.get_json()
	if not req_data:
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

	# action参数表名客户端是接单还是拒单行为
	action = req_data.get("action")
	if action not in ("accept", "reject"):
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

	try:
		# 根据订单号查询该订单（要求待接单状态）
		order = Order.query.filter(Order.id == order_id, Order.status == "WAIT_ACCEPT").first()
		house = order.house
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="无法获取该数据")

	# 判断用户是否是该房子的房东，确保房东只能修改自己房子的订单
	if not order or house.user_id != user_id:
		return jsonify(errno=RET.REQERR, errmsg="操作无效")

	# 根据请求方式，进行各自处理
	if action == "accept":
		# 接单，将订单状态更新为待支付状态
		order.status = "WAIT_PAYMENT"
	elif action == "reject":
		# 拒单，要求用户填写拒单原因
		reason = req_data.get("reason")
		if not reason:
			return jsonify(errno=RET.NODATA, errmsg="请填写拒单原因")
		order.status = "REJECTED"
		order.comment = reason

	# 提交数据库
	try:
		db.session.add(order)
		db.session.commit()
	except Exception as e:
		current_app.logger.error(e)
		db.session.rollback()
		return jsonify(errno=RET.DBERR, errmsg="数据库提交失败")

	# 返回结果
	return jsonify(errno=RET.OK, errmsg="OK")


@api.route("/orders/<int:order_id>/comment")
@login_required
def save_order_comment(order_id):
	"""
	保存订单评论信息
	:param order_id:
	:return:
	"""
	# 获取用户id
	user_id = g.user_id

	# 获取评论参数
	req_data = request.get_json()
	comment = req_data.get("comment")
	# 检验参数
	if not comment:
		return jsonify(errno=RET.PARAMERR, errmsg="参数错误")

	# 确保只能评论自己下的订单，而且订单处于待评价状态
	try:
		order = Order.query.filter(Order.id == order_id, Order.user_id == user_id, Order.status == "WAIT_COMMENT").first()
		house = order.house
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="无法获取订单数据")

	try:
		# 将订单状态设置为已完成
		order.status = "COMPLETE"
		# 保存订单的评论信息
		order.comment = comment
		# 保存，提交数据库
		db.session.add(order)
		db.session.add(house)
		db.session.commit()
	except Exception as e:
		current_app.logger.error(e)
		db.session.rollback()
		return jsonify(errno=RET.DBERR, errmsg="操作失败")

	# 因为房屋详情中有订单的评价信息，为了让最新的评价信息展示在房屋详情中，所以删除redis中关于本订单房屋的详情缓存
	try:
		redis_store.delete("house_info_%s" % order.house.id)
	except Exception as e:
		current_app.logger.error(e)

	# 返回结果
	return jsonify(errno=RET.OK, errmsg="OK")
