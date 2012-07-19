# -*- coding: utf-8 -*-
# Django settings for batucada project.

import os
import logging
import djcelery

import l10n.locales

djcelery.setup_loader()

# Make filepaths relative to settings.
ROOT = os.path.dirname(os.path.abspath(__file__))
path = lambda *a: os.path.join(ROOT, *a)

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'lernanta.db',
    }
}

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Toronto'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en'

SUPPORTED_LANGUAGES = tuple([(i.lower(), l10n.locales.LOCALES[i].native)
    for i in l10n.locales.LOCALES])

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

SUPPORTED_NONLOCALES = (
    'media', 'static', '.well-known', 'pubsub', 'broadcasts', 'ajax'
)

# Absolute path to the directory that holds media.
# Example: "/home/media/media.lawrence.com/"
MEDIA_ROOT = path('media')

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash if there is a path component (optional in other cases).
# Examples: "http://media.lawrence.com", "http://example.com/media/"
MEDIA_URL = '/media/'

# URL prefix for admin media -- CSS, JavaScript and images. Make sure to use a
# trailing slash.
# Examples: "http://foo.com/media/", "/media/".
#ADMIN_MEDIA_PREFIX = '/admin-media/'

# Absolute path to the directory that holds static files.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = path('static_serv')

# URL that handles the static files served from STATIC_ROOT.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# Directories containing static files
STATICFILES_DIRS = (
    path('static'),
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)

# Set HttpOnly flag on session cookies
SESSION_COOKIE_HTTPONLY = True

# Hack to get HttpOnly flag set on session cookies. This can be removed when
# http://code.djangoproject.com/changeset/14707 makes it into a release.
SESSION_COOKIE_PATH = '/; HttpOnly'

MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'

MIDDLEWARE_CLASSES = (
    'drumbeat.middleware.NotFoundMiddleware',
    'django.contrib.redirects.middleware.RedirectFallbackMiddleware',
    'l10n.middleware.LocaleURLRewriter',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'maintenancemode.middleware.MaintenanceModeMiddleware',
    'commonware.middleware.ScrubRequestOnException',
    'commonware.middleware.FrameOptionsHeader',
    'django.middleware.locale.LocaleMiddleware',
    'users.middleware.ProfileExistMiddleware',
    'tracker.middleware.PageViewTrackerMiddleware',
)

ROOT_URLCONF = 'lernanta.urls'

TEMPLATE_DIRS = (
    path('templates'),
)

# Use the fully qualified name for our apps so django_nose does not
# add duplicates on INSTALLED_APPS.
INSTALLED_APPS = (
    'django.contrib.sites',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.redirects',
    'django.contrib.staticfiles',
    'south',
    'robots',
    'wellknown',
    'lernanta.apps.pagination',
    'lernanta.apps.users',
    'lernanta.apps.search',
    'lernanta.apps.chat',
    'lernanta.apps.l10n',
    'lernanta.apps.dashboard',
    'lernanta.apps.relationships',
    'lernanta.apps.activity',
    'lernanta.apps.statuses',
    'messages',
    'taggit',
    'lernanta.apps.preferences',
    'lernanta.apps.drumbeatmail',
    'lernanta.apps.links',
    'django_push.subscriber',
    'djcelery',
    'django_openid_auth',
    'ckeditor',
    'lernanta.apps.richtext',
    'lernanta.apps.replies',
    'lernanta.apps.signups',
    'lernanta.apps.content',
    'lernanta.apps.schools',
    'voting',
    'lernanta.apps.news',
    'lernanta.apps.pages',
    'lernanta.apps.projects',
    'lernanta.apps.badges',
    'lernanta.apps.drumbeat',
    'django_obi',
    'lernanta.apps.tags',
    'lernanta.apps.tracker',
    'lernanta.apps.reviews',
    'lernanta.apps.notifications',
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.core.context_processors.static',
    'django.contrib.messages.context_processors.messages',
    'drumbeat.context_processors.django_conf',
    'messages.context_processors.inbox',
    'users.context_processors.messages',
    'users.context_processors.redirect_urls',
)

TEST_RUNNER = 'test_utils.runner.RadicalTestSuiteRunner'

WELLKNOWN_HOSTMETA_HOSTS = ('localhost:8000',)

# Auth settings
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/dashboard/'

ACCOUNT_ACTIVATION_DAYS = 7

AUTHENTICATION_BACKENDS = (
    'users.backends.DrupalUserBackend',
    'users.backends.DrupalOpenIDBackend',
    'users.backends.CustomUserBackend',
    'django_openid_auth.auth.OpenIDBackend',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_PROFILE_MODULE = 'users.UserProfile'

MAX_IMAGE_SIZE = 1024 * 700
MAX_UPLOAD_SIZE = 1024 * 1024 * 50
MAX_PROJECT_FILES = 6

CACHE_BACKEND = 'caching.backends.memcached://localhost:11211'
CACHE_PREFIX = 'lernanta'
CACHE_COUNT_TIMEOUT = 60

# Email goes to the console by default.  s/console/smtp/ for regular delivery
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'admin@p2pu.org'
REPLY_EMAIL_DOMAIN = 'reply.p2pu.org'

CELERY_RESULT_BACKEND = "amqp"

# SuperFeedr settings
SUPERFEEDR_URL = 'http://superfeedr.com/hubbub'
SUPERFEEDR_USERNAME = ''
SUPERFEEDR_PASSWORD = ''

# django-push settings
PUSH_CREDENTIALS = 'links.utils.hub_credentials'
PUSH_HUB = 'http://pubsubhubbub.appspot.com/'
SOUTH_TESTS_MIGRATE = False

FEED_URLS = {
    'splash': 'http://info.p2pu.org/feed/',
}

# Ckeditor
CKEDITOR_MEDIA_PREFIX = "/static/ckeditor/"
CKEDITOR_UPLOAD_PATH = path("media/uploads/images")
CKEDITOR_FILE_UPLOAD_PATH = path("media/uploads/files")
CKEDITOR_RESTRICT_BY_USER = True
CKEDITOR_IMAGE_UPLOAD_EXTENSIONS = [
    '.jpg', '.jpeg', '.gif', '.png', '.tif', '.tiff'
]
CKEDITOR_FILE_UPLOAD_EXTENSIONS = CKEDITOR_IMAGE_UPLOAD_EXTENSIONS + ['.pdf',
    '.doc', '.rtf', '.txt', '.xls', '.csv', '.mov', '.wmv', '.mpeg', '.mpg',
    '.avi', '.rm', '.mp3', '.mp4', '.wav', '.aiff', '.midi', '.m4p']

# Where the default image for sending to Gravatar
DEFAULT_PROFILE_IMAGE = 'https://p2pu.org/static/images/member-missing.png'

# When set to True, if the request URL does not match any
# of the patterns in the URLconf and it doesn't end in a slash,
# an HTTP redirect is issued to the same URL with a slash appended.
APPEND_SLASH = True

# Django logging configuration.
# The default logging configuration. This sends an email to
# the site admins on every HTTP 500 error. All other log
# records are sent to the bit bucket.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': path('lernanta.log'),
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
        },
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': False,
        },
        'caching': {
            'handlers': ['null'],
            'propagate': False,
            'level': 'DEBUG',
        },
        '': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        }
    }
}

TRACKING_PREFIXES = [
    r'^/\w{2}/groups/[\w-]+/content/[\w-]+/$',
    r'^/\w{2}/groups/[\w-]+/$',
    r'^/\w{2}/schools/[\w-]+/sets/[\w-]+/$',
    r'^/\w{2}/schools/[\w-]+/$',
]

BOT_NAMES =['Googlebot', 'Slurp', 'Twiceler', 'msnbot',
    'KaloogaBot', 'YodaoBot', 'Baiduspider', 'googlebot',
    'Speedy Spider', 'DotBot']
