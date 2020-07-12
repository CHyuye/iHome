from . import api
from ihome import db, models # 此时会发生循环导包问题，需检查整体导包，推迟部分导包操作
from flask import current_app  # 间接使用日志全局功能


api.route("/index")
def index():
	current_app.logger.error("error msg")  # 错误级别，设置为此级别，以下三种将不显示
	current_app.logger.warn("warn msg")  # 警告级别
	current_app.logger.info("info msg")  # 信息提示级别
	current_app.logger.debug("debug msg")  # 调试级别
	return "this is index page"

