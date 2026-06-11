from pathlib import Path
import os
from django.contrib.messages import constants as messages_constants
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")
STATICFILES_DIRS = [os.path.join(BASE_DIR, "static")]

# 取込対象のコンテンツ置き場（保管庫から同期した md）
CONTENT_DIR = os.path.join(BASE_DIR, "content")

SECRET_KEY = os.getenv("SECRET_KEY", "dummy-development-secret")

DEBUG = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

ALLOWED_HOSTS = [
    "localhost",
    "127.0.0.1",
    "household-app-bacon.net",
]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "notes",
    "quiz",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "SNproject.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATE_DIR],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "SNproject.wsgi.application"


# Bootstrap 5 用に messages のタグを調整（error → danger）
MESSAGE_TAGS = {
    messages_constants.ERROR: "danger",
}


# Database
# 本番（Raspberry Pi）は .env に dbname 等を設定して PostgreSQL を使う。
# ローカル開発で dbname が無い場合は SQLite にフォールバックする。
if os.getenv("dbname"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("dbname"),
            "USER": os.getenv("user"),
            "PASSWORD": os.getenv("password"),
            "HOST": os.getenv("host"),
            "PORT": os.getenv("port"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


LANGUAGE_CODE = "ja"
TIME_ZONE = "Asia/Tokyo"
USE_I18N = True
USE_TZ = True


STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# 認証（シングルユーザー。ユーザー作成は createsuperuser で行う）
LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "login"


# サブパス /study でのデプロイ設定
# Nginx 側で /study プレフィックスを除去してから Gunicorn に転送する構成
# ローカル開発時は .env に FORCE_SCRIPT_NAME を書かない（空 = 無効）
# 本番（Raspberry Pi）の .env に FORCE_SCRIPT_NAME=/study を設定する
_script_name = os.getenv("FORCE_SCRIPT_NAME", "")
if _script_name:
    FORCE_SCRIPT_NAME = _script_name
    STATIC_URL = f"{_script_name}/static/"
else:
    STATIC_URL = "/static/"


# プロキシ経由のHTTPS判定（Cloudflare Tunnel 共通）
CSRF_TRUSTED_ORIGINS = [
    "https://household-app-bacon.net",
]
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# 他アプリ（/budget, /cooking, /travel）とCookieが競合しないよう分離
SESSION_COOKIE_NAME = "sessionid_study"
CSRF_COOKIE_NAME = "csrftoken_study"
