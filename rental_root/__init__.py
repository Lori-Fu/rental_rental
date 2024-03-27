from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import redis
import logging
from logging.handlers import RotatingFileHandler
from flask_session import Session
from flask_wtf import CSRFProtect

from config import config_map
from rental_root.utils.common import ReConverter

db = SQLAlchemy()
migrate = Migrate()
redis_store = None

logging.basicConfig(level=logging.INFO)
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024*1024*100, backupCount=10)
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
file_log_handler.setFormatter(formatter)
logging.getLogger().addHandler(file_log_handler)


def create_app(config_name):
    app = Flask(__name__)
    config_class = config_map[config_name]
    app.config.from_object(config_class)

    db.init_app(app)
    migrate.init_app(app=app, db=db)

    global redis_store
    redis_store = redis.StrictRedis(host=config_class.REDIS_HOST, port=config_class.REDIS_PORT, health_check_interval=30)
    Session(app)
    CSRFProtect(app)


    app.url_map.converters["re"] = ReConverter
    from rental_root import api_1_0
    app.register_blueprint(api_1_0.api, url_prefix="/api/v1.0")
    from rental_root import web_html
    app.register_blueprint(web_html.html)
    from rental_root import db_init
    app.register_blueprint(db_init.db_init)

    return app

