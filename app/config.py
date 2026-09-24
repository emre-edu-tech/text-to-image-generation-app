import os


class Config:
    SECRET_KEY = os.environ["SECRET_KEY"]
    APP_USERNAME = os.environ["APP_USERNAME"]
    APP_PASSWORD = os.environ["APP_PASSWORD"]
    CF_ACCOUNT_ID = os.environ["CF_ACCOUNT_ID"]
    CF_API_TOKEN = os.environ["CF_API_TOKEN"]
    SESSION_COOKIE_SECURE = os.environ.get("FLASK_ENV") != "development"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 24 * 7  # 7 days
