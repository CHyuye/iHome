import redis


class Config(object):
	"""配置信息"""
	SECRET_KEY = "jfcioanweo209gjr"

	# 数据库
	# SQLALCHEMY_DATABASE_URI = "mysql+pymsql"此处的mysql和pymsql都是链接MySQL的
	# SQLALchemy只是用来将模型类转换为sql语句，mysql+pymsql将sql语句添加到数据库，前提创建一个对应的数据库author
	SQLALCHEMY_DATABASE_URI = "mysql+pymysql://root:mysql@192.168.232.141:3306/ihome"

	# 设置sqlalchemy自动更跟踪数据库
	SQLALCHEMY_TRACK_MODIFICATIONS = True

	# redis数据库
	REDIS_HOST = "192.168.232.141"
	REDIS_PORT = 6379

	# celery实现任务队列（broker）和存放数据结果（backend)
	# BROKER_URL = "redis://192.168.232.141:6379/1"
	# CELERY_RESULT_BACKEND = "redis://192.168.232.141:6379/2"

	# flask_session配置redis数据库
	SESSION_TYPE = "redis"
	SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
	SESSION_USE_SIGNER = True  # 对cookie中的session_id进行隐藏处理
	PERMANENT_SESSION_LIFETIME = 86400  # session的有效期，7天


# 使用类继承的方式，创建多个模式，为了后期好维护
class DevelopmentConfig(Config):
	"""开发模式的配置信息"""
	DEBUG = True


class ProductConfig(object):
	"""生产环境的配置信息"""
	pass


# 建立映射关系
config_map = {
	"develop": DevelopmentConfig,
	"product": ProductConfig
}