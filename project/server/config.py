# project/server/config.py
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))

load_dotenv()


class Config(object):
    """Base configuration."""

    APP_NAME = os.getenv("APP_NAME", "Force")
    BCRYPT_LOG_ROUNDS = 4
    DEBUG_TB_ENABLED = False
    SECRET_KEY = os.getenv("SECRET_KEY", "0Vsj6UyLhN6vBvkxVKz7BxdOrTvBx8UT")
    WTF_CSRF_ENABLED = False
    DEBUG_TB_ENABLED = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "sqlite:///{0}".format(os.path.join(basedir, "force.db"))
    )


# class DevelopmentConfig(BaseConfig):
#     """Development configuration."""

#     DEBUG_TB_ENABLED = True
#     DEBUG_TB_INTERCEPT_REDIRECTS = False
#     SQLALCHEMY_DATABASE_URI = os.environ.get(
#         "DATABASE_URL", "sqlite:///{0}".format(os.path.join(basedir, "dev.db"))
#     )


# class TestingConfig(BaseConfig):
#     """Testing configuration."""

#     PRESERVE_CONTEXT_ON_EXCEPTION = False
#     DATABASE_URL = os.environ.get("DATABASE_TEST_URL", "sqlite:///")
#     SQLALCHEMY_DATABASE_URI = "sqlite:///"
#     SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_TEST_URL", "sqlite:///")
#     TESTING = True


# class ProductionConfig(BaseConfig):
#     """Production configuration."""

#     BCRYPT_LOG_ROUNDS = 13
#     SQLALCHEMY_DATABASE_URI = os.environ.get(
#         "DATABASE_URL",
#         "sqlite:///{0}".format(os.path.join(basedir, "prod.db")),
#     )
#     WTF_CSRF_ENABLED = True
