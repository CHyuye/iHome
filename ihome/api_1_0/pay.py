from . import api
from ihome.utils.response_code import RET
from ihome.models import Order
from ihome.utils.commons import login_required
from flask import g, current_app, jsonify, request
from alipay import AliPay
from ihome import constants, db
import os


@api.route("/orders/<int:order_id>/payment", methods=["POST"])
@login_required
def order_pay(order_id):
	"""
	发起支付宝支付
	:param order_id: 订单编号
	:return:
	"""
	# 获取user_id
	user_id = g.user_id

	# 判断订单状态
	try:
		order = Order.query.filter(Order.id == order_id, Order.user_id == user_id, Order.status == "WAIT_PAYMENT").first()
	except Exception as e:
		current_app.logger.error(e)
		return jsonify(errno=RET.DBERR, errmsg="数据库异常")

	if order is None:
		return jsonify(errno=RET.NODATA, errmsg="订单数据有误")

	# 创建支付宝SDK工具对象
	alipay_client = AliPay(
		appid="2016101900724274",
		app_notify_url=None,  # 默认回调url
		app_private_key_string=os.path.join(os.path.dirname(__file__), "keys/app_private_key.pem"),  # 私钥
		# 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
		alipay_public_key_string=os.path.join(os.path.dirname(__file__), "keys/alipay_public_key.pem"),
		sign_type="RSA2",  # RSA 或者 RSA2
		debug=True  # 默认False
	)

	# 手机网站支付，沙箱环境支付需要跳转到https://openapi.alipaydev.com/gateway.do? + order_string
	order_string = alipay_client.api_alipay_trade_wap_pay(
		out_trade_no=order_id,  # 订单编号
		total_amount=str(order.amount/100.0),  # 总金额，需要转换为字符串
		subject=u"爱家租房 %s" % order_id,  # 订单标题
		return_url="http://127.0.0.1:5000/payComplete.html",  # 返回的链接地址
		notify_url=None  # 可选, 不填则使用默认notify url
	)

	# 构建让用户跳转的支付链接地址
	pay_url = constants.ALIPAY_URL_PREFIX + order_string

	return jsonify(errno=RET.OK, errmsg="OK", data={"pay_url": pay_url})


@api.route("/order/payment", methods=["PUT"])
def save_order_payment_result():
	"""
	保存订单支付结果
	:return:
	"""
	# 获取支付宝支付返回的表单提交参数
	alipay_data = request.form.to_dict()
	# 对支付宝的数据进行分离，提取出支付宝的签名参数sign
	alipay_sign = alipay_data.pop("sign")

	# 创建支付宝sdk的工具对象
	alipay_client = AliPay(
		appid="2016101900724274",
		app_notify_url=None,  # 默认回调url
		app_private_key_string=os.path.join(os.path.dirname(__file__), "keys/app_private_key.pem"),  # 私钥
		# 支付宝的公钥，验证支付宝回传消息使用，不是你自己的公钥,
		alipay_public_key_string=os.path.join(os.path.dirname(__file__), "keys/alipay_public_key.pem"),
		sign_type="RSA2",  # RSA 或者 RSA2
		debug=True  # 默认False
	)

	# 借助工具验证验证参数的合法性
	result = alipay_client.verify(alipay_data, alipay_sign)

	# 如果确定参数是支付宝返回True，否则为False
	if result:
		order_id = alipay_data.get("out_trade_no")  # 订单编号
		trade_no = alipay_data.get("trade_no")  # 支付宝支付流水号
		# 修改数据库的订单状态信息
		try:
			Order.query.filter_by(id=order_id).update({"status": "WAIT_COMMENT", "trade_no": trade_no})
			db.session.commit()
		except Exception as e:
			db.sesion.rollback()
			current_app.logger.error(e)

	return jsonify(errno=RET.OK, errmsg="OK")

