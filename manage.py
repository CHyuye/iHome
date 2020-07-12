from ihome import create_app, db
from flask_script import Manager
from flask_migrate import Migrate, MigrateCommand


# 创建flask的应用对象
app = create_app("develop")  # 因为创建的app运行在开发模式配置DEBUG=True，所以日志级别会被覆盖，需调product


manager = Manager(app)
Migrate(app, db)
manager.add_command("db", MigrateCommand)


if __name__ == '__main__':
    manager.run()


