from .base import * 


DEBUG = config("DJANGO_DEBUG", default=True, cast=bool)


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


CORS_ALLOW_ALL_ORIGINS = True


MEDIA_ROOT =  BASE_DIR / "media"

ALLOWED_HOSTS = ['*',]
