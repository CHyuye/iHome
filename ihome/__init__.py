from flask import Flask
from config import config_map
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from flask_wtf import CSRFProtect
from .utils.commons import ReConverter

import logging
from logging.handlers import RotatingFileHandler
import redis


# 数据库
db = SQLAlchemy()

# 创建redis数据库链接对象
redis_store = None

# 配置日志功能
# 设置日志信息的记录等级
# 该处日志级别设置需更改Config配置的运行模式
logging.basicConfig(level=logging.DEBUG)  # 调试DEBUG级别，有四种级别error,warn,info,debug
# 创建日志记录器，指明日志保存的路径，每个日志文件的最大大小，保存的日志文件的个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
# 创建日志记录的格式
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录的格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日志记录器
logging.getLogger().addHandler(file_log_handler)


# 工厂模式
def create_app(config_name):
	"""
	创建flask的应用对象
	:param config_name:str 配置模式的模式名字 ("develop", "product")
	:return: app创建
	"""
	app = Flask(__name__)

	# 根据配置模式的名字获取配置参数的类
	config_class = config_map.get(config_name)
	app.config.from_object(config_class)

	# init_app()方法，初始化db
	db.init_app(app)

	# 初始化redis工具
	global redis_store
	redis_store = redis.StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT)

	# 利用flask-session，将session中的数据保存到redis中
	Session(app)

	# 为flask补充csrf防护, 其实使用了一个钩子，在页面请求之前，执行钩子
	# csrf防护机制：从cookie中获取一个csrf_token的值，从请求体中获取一个csrf_token的值
	# 对两个值进行对比，检验通过则进入视图函数中执行，否则，向前端返回状态码400错误
	CSRFProtect(app)

	# 为flask添加自定义转换器
	app.url_map.converters["re"] = ReConverter

	# 注册蓝图
	from ihome import api_1_0
	app.register_blueprint(api_1_0.api, url_prefix="/api/v1.0")

	# 注册提供静态文件的蓝图
	from ihome import web_html
	app.register_blueprint(web_html.html)

	return app