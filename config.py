import redis
import os
from dotenv import load_dotenv

load_dotenv()


class Config(object):
    SECRET_KEY = "LLUUOOYYII"
    DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SQLALCHEMY_DATABASE_URI = DATABASE_URI
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    REDIS_HOST = "127.0.0.1"
    REDIS_PORT = 6378

    SESSION_TYPE = "redis"
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True
    PERMANENT_SESSION_LIFETIME = 86400  # 1 day


class DevelopmentConfig(Config):
    DEBUG = True


class ProductConfig(Config):
    pass


config_map = {
    "develop": DevelopmentConfig,
    "product": ProductConfig
}
