import os
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = os.environ['SECRET_KEY']
DEBUG = os.getenv('DEBUG', '0') == '1'
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1,web,testserver').split(',')
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', 'http://localhost:8088,http://127.0.0.1:8088').split(',')
INSTALLED_APPS = ['django.contrib.admin','django.contrib.auth','django.contrib.contenttypes','django.contrib.sessions','django.contrib.messages','django.contrib.staticfiles','catalog']
MIDDLEWARE = ['django.middleware.security.SecurityMiddleware','catalog.middleware.BodyLimitMiddleware','django.contrib.sessions.middleware.SessionMiddleware','django.middleware.common.CommonMiddleware','django.middleware.csrf.CsrfViewMiddleware','django.contrib.auth.middleware.AuthenticationMiddleware','catalog.middleware.RateLimitMiddleware','django.contrib.messages.middleware.MessageMiddleware','django.middleware.clickjacking.XFrameOptionsMiddleware']
ROOT_URLCONF = 'config.urls'
TEMPLATES = [{'BACKEND':'django.template.backends.django.DjangoTemplates','DIRS':[],'APP_DIRS':True,'OPTIONS':{'context_processors':['django.template.context_processors.request','django.contrib.auth.context_processors.auth','django.contrib.messages.context_processors.messages']}}]
WSGI_APPLICATION = 'config.wsgi.application'
if os.getenv('DB_ENGINE') == 'sqlite':
    DATABASES = {'default': {'ENGINE':'django.db.backends.sqlite3','NAME':os.getenv('SQLITE_PATH', str(BASE_DIR/'dev.sqlite3'))}}
else:
    DATABASES = {'default': {'ENGINE':'django.db.backends.postgresql','NAME':os.getenv('POSTGRES_DB','alcooltest'),'USER':os.getenv('POSTGRES_USER','alcooltest'),'PASSWORD':os.environ['POSTGRES_PASSWORD'],'HOST':os.getenv('POSTGRES_HOST','db'),'PORT':os.getenv('POSTGRES_PORT','5432'),'CONN_MAX_AGE':60,'OPTIONS':{'options':'-c statement_timeout=15000'}}}
AUTH_PASSWORD_VALIDATORS = [{'NAME':'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},{'NAME':'django.contrib.auth.password_validation.MinimumLengthValidator','OPTIONS':{'min_length':12}},{'NAME':'django.contrib.auth.password_validation.CommonPasswordValidator'},{'NAME':'django.contrib.auth.password_validation.NumericPasswordValidator'}]
PASSWORD_HASHERS = ['django.contrib.auth.hashers.Argon2PasswordHasher','django.contrib.auth.hashers.PBKDF2PasswordHasher']
LANGUAGE_CODE='en-us'
TIME_ZONE='UTC'
USE_TZ=True
STATIC_URL='/static/'
STATIC_ROOT=Path(os.getenv('STATIC_ROOT','/app/staticfiles'))
MEDIA_URL='/media/'
MEDIA_ROOT=Path(os.getenv('MEDIA_ROOT','/app/media'))
EXPORT_ROOT=Path(os.getenv('EXPORT_ROOT','/app/exports'))
SEED_FILE=Path(os.getenv('SEED_FILE',str(BASE_DIR.parent/'data/catalog/seed.json')))
SCHEMA_FILE=Path(os.getenv('SCHEMA_FILE',str(BASE_DIR.parent/'data/catalog/schema.json')))
DEFAULT_AUTO_FIELD='django.db.models.BigAutoField'
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE='Lax'
SESSION_COOKIE_AGE=43200
SESSION_COOKIE_SECURE=os.getenv('SECURE_COOKIES','0')=='1'
CSRF_COOKIE_SECURE=SESSION_COOKIE_SECURE
SECURE_CONTENT_TYPE_NOSNIFF=True
SECURE_REFERRER_POLICY='same-origin'
X_FRAME_OPTIONS='DENY'
SECURE_HSTS_SECONDS=31536000 if SESSION_COOKIE_SECURE else 0
SECURE_HSTS_INCLUDE_SUBDOMAINS=SESSION_COOKIE_SECURE
SECURE_HSTS_PRELOAD=SESSION_COOKIE_SECURE
DATA_UPLOAD_MAX_MEMORY_SIZE=6*1024*1024
FILE_UPLOAD_MAX_MEMORY_SIZE=2*1024*1024
REGISTRATION_OPEN=os.getenv('REGISTRATION_OPEN','1')=='1'
SETUP_TOKEN=os.getenv('SETUP_TOKEN','')
LOGGING={'version':1,'disable_existing_loggers':False,'handlers':{'console':{'class':'logging.StreamHandler'}},'root':{'handlers':['console'],'level':'INFO'}}
if os.getenv('REDIS_URL'):
    CACHES={'default':{'BACKEND':'django.core.cache.backends.redis.RedisCache','LOCATION':os.environ['REDIS_URL'],'TIMEOUT':60,'KEY_PREFIX':'alcooltest'}}
else:
    CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':'alcooltest-tests'}}

PUBLIC_BASE_URL=os.getenv('PUBLIC_BASE_URL','http://localhost:8088')
