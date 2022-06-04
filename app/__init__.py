from flask import Flask
from config import Config
from flask_sqlalchemy import SQLAlchemy
from redis import Redis
import rq
from flask_migrate import Migrate
from flask_login import LoginManager
from flask_mail import Mail

from flask_babel import Babel





db = SQLAlchemy()
migrate = Migrate()
login = LoginManager()
login.login_view = 'main.login'
mail = Mail()
babel = Babel()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    app.redis = Redis.from_url(app.config['REDIS_URL'])
    app.task_queue = rq.Queue('students', connection=app.redis)

    db.init_app(app)
    migrate.init_app(app, db)
    login.init_app(app)
    mail.init_app(app)
    babel.init_app(app)

    from app.errors import bp as errors_bp
    app.register_blueprint(errors_bp)

    from app.student import bp as student_bp
    app.register_blueprint(student_bp)

    from app.main import bp as main_bp
    app.register_blueprint(main_bp)

    return app


from app import models
