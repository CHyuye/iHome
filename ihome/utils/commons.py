from werkzeug.routing import BaseConverter
from flask import session, jsonify, g
from ihome.utils.response_code import RET
import functools


# 定义一个正则转换器
class ReConverter(BaseConverter):
	"""自定义正则转换器"""
	def __init__(self, url_map, regex):
		# 调用父类的初始化方法
		super(ReConverter, self).__init__(url_map)
		# 保存正则表达式
		self.regex = regex


# xrange
def xrange(start, end=None, step=1):
	if end == None:
		end = start
		start = 0
	if step > 0:
		while start < end:
			yield start
			start += step
	elif step < 0:
		while start > end:
			yield start
			start += step
	else:
		return 'step can not be zero'


# 定义验证登录状态的装饰器
def login_required(view_func):
	# todo:坚持使用@functools.wraps()装饰器
	# 这一层装饰起作用是：保证我们自己定义的装饰器被调用时，调用的函数信息不会被改变
	@functools.wraps(view_func)
	def wrapper(*args, **kwargs):
		# 判断用户的登录状态
		user_id = session.get("user_id")
		# 如果用户是登录的，则执行视图函数
		if user_id is not None:
			# 将user_id保存到g对象中，在视图函数中可以通过g对象获取保存的数据
			g.user_id = user_id
			return view_func(*args, **kwargs)
		else:
			# 如果未登录，则返回未登录的状态
			return jsonify(errno=RET.SESSIONERR, errmsg="用户未登录")
	return wrapper


# @login_required
# def set_user_avatar():
# 	# 调用的视图函数获取g对象中的数据
# 	user_id = g.user_id
#   return json ""


# def demo_required(func):
# 	@functools.wraps(func)
# 	def wrapper(*args, **kwargs):
# 		pass
# 	return wrapper
#
#
# @demo_required
# def deal_demo():
# 	"""view demo python"""
# 	pass
#
#
# print(deal_demo.__name__)  # 获取视图名字，未使用functools是返回 装饰器wrapper函数名
# print(deal_demo.__doc__)  # 获取视图函数文档信息，未使用functools返回 装饰器wrapper函数信息
