# -*- coding: utf-8 -*-
# Django settings for batucada project.

import os
import logging
import djcelery

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

SUPPORTED_LANGUAGES = (
		(u'en', u'English'),
		(u'es', u'Español'),
		)

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

SUPPORTED_NONLOCALES = ('media', '.well-known', 'pubsub', 'broadcasts', 'ajax')

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
ADMIN_MEDIA_PREFIX = '/admin-media/'

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'std3j$ropgs216z1aa#8+p3a2w2q06mns_%2vfx_#$$i!+6o+x'

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
    'l10n.middleware.LocaleURLRewriter',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'maintenancemode.middleware.MaintenanceModeMiddleware',
    'commonware.middleware.HidePasswordOnException',
    'commonware.middleware.FrameOptionsHeader',
    'jogging.middleware.LoggingMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'users.middleware.ProfileExistMiddleware',
)

ROOT_URLCONF = 'lernanta.urls'

TEMPLATE_DIRS = (
    path('templates'),
)

INSTALLED_APPS = (
    'django.contrib.sites',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.comments',
    'south',
    'jogging',
    'wellknown',
    'users',
    'l10n',
    'dashboard',
    'relationships',
    'activity',
    'projects',
    'statuses',
    'messages',
    'drumbeat',
    'taggit',
    'preferences',
    'drumbeatmail',
    'links',
    'challenges',
    'django_push.subscriber',
    'djcelery',
    'events',
    'django_openid_auth',
    'ckeditor',
    'content',
    'schools',
    'voting'
)

TEMPLATE_CONTEXT_PROCESSORS = (
    'django.contrib.auth.context_processors.auth',
    'django.core.context_processors.debug',
    'django.core.context_processors.i18n',
    'django.core.context_processors.media',
    'django.contrib.messages.context_processors.messages',
    'drumbeat.context_processors.django_conf',
    'messages.context_processors.inbox',
    'users.context_processors.messages',
    'users.context_processors.login_with_redirect_url',
)

TEST_RUNNER = 'test_utils.runner.RadicalTestSuiteRunner'

WELLKNOWN_HOSTMETA_HOSTS = ('localhost:8000',)

# Auth settings
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

ACCOUNT_ACTIVATION_DAYS = 7

AUTHENTICATION_BACKENDS = (
    'users.backends.CustomUserBackend',
    'django_openid_auth.auth.OpenIDBackend',
    'users.backends.DrupalUserBackend',
    'users.backends.DrupalOpenIDBackend',
    'django.contrib.auth.backends.ModelBackend',
)

AUTH_PROFILE_MODULE = 'users.UserProfile'

MAX_IMAGE_SIZE = 1024 * 700
MAX_UPLOAD_SIZE = 1024 * 1024 * 50
MAX_PROJECT_FILES = 6

GLOBAL_LOG_LEVEL = logging.DEBUG
GLOBAL_LOG_HANDLERS = [logging.FileHandler(path('lernanta.log'))]

CACHE_BACKEND = 'caching.backends.memcached://localhost:11211'
CACHE_PREFIX = 'lernanta'
CACHE_COUNT_TIMEOUT = 60

# Email goes to the console by default.  s/console/smtp/ for regular delivery
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
DEFAULT_FROM_EMAIL = 'admin@p2pu.org'

# RabbitMQ Config
BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = ""
BROKER_PASSWORD = ""
BROKER_VHOST = ""

CELERY_RESULT_BACKEND = "amqp"

# SuperFeedr settings
SUPERFEEDR_URL = 'http://superfeedr.com/hubbub'
SUPERFEEDR_USERNAME = ''
SUPERFEEDR_PASSWORD = ''

# django-push settings
PUSH_CREDENTIALS = 'links.utils.hub_credentials'
PUSH_HUB = 'http://pubsubhubbub.appspot.com/'
SOUTH_TESTS_MIGRATE = False

# Feed to show contents of on the splash page
SPLASH_PAGE_FEED = 'http://blogs.p2pu.org/feed/'

# Ckeditor
CKEDITOR_MEDIA_PREFIX = "/media/ckeditor/"
CKEDITOR_UPLOAD_PATH = path("uploads")
CKEDITOR_CONFIGS = {
    'rich': {
        'toolbar': [
            ['Source'],
            ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript', 'Superscript'],
            ['JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['NumberedList', 'BulletedList', 'HorizontalRule', 'Outdent', 'Indent', 'SyntaxHighlighting', 'Blockquote'],
            ['Maximize'],
            ['Link', 'Unlink', 'Image', 'YouTube', 'SlideShare', 'Smiley', 'SpecialChar', 'Table'],
            ['Format','Font','FontSize', 'TextColor','BGColor'],
        ],
        'skin': 'kama',
        'width': '568',
        'height': '255',
        'removePlugins': 'resize, elementspath',
        'toolbarCanCollapse': False,
        'extraPlugins': 'youtube,slideshare,prettify',
        'format_tags': 'p;h1;h2;h3;h4;h5;h6',
        'prettify': { 'element' : 'pre', 'attributes' : { 'class' : 'prettyprint' }},
    },
    'reduced': {
        'toolbar': [
            ['Source', '-' , 'Bold', 'Italic', '-', 'Link', 'Unlink'],
        ],
        'skin': 'kama',
        'width': '420',
        'height': '110',
        'removePlugins': 'resize, elementspath',
        'toolbarCanCollapse': False,
        'extraPlugins': 'youtube,slideshare,prettify',
        'format_tags': 'p;h1;h2;h3;h4;h5;h6',
        'prettify': { 'element' : 'pre', 'attributes' : { 'class' : 'prettyprint' }},
    }
}

# Constants for cleaning ckeditor html.

REDUCED_ALLOWED_TAGS = ('a', 'b', 'em', 'i', 'strong', 'p', 'u', 'strike', 'sub', 'sup', 'br')
RICH_ALLOWED_TAGS = REDUCED_ALLOWED_TAGS + ('h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ol', 'ul', 'li', 'hr', 'blockquote',
        'span', 'pre', 'code', 'div', 'img',
        'table', 'thead', 'tr', 'th', 'caption', 'tbody', 'td', 'br')

REDUCED_ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title'],
}
RICH_ALLOWED_ATTRIBUTES = REDUCED_ALLOWED_ATTRIBUTES.copy()
RICH_ALLOWED_ATTRIBUTES.update({
    'img': ['src', 'alt', 'style', 'title'],
    'p': ['style'],
    'table': ['align', 'border', 'cellpadding', 'cellspacing',
        'style', 'summary'],
    'th': ['scope'],
    'span': ['style'],
    'pre': ['class'],
    'code': ['class'],
})

RICH_ALLOWED_STYLES = ('text-align', 'margin-left', 'border-width',
    'border-style', 'margin', 'float', 'width', 'height',
    'font-family', 'font-size', 'color', 'background-color')

# Where the default image for sending to Gravatar
DEFAULT_PROFILE_IMAGE = 'http://new.p2pu.org/media/images/member-missing.png'

# When set to True, if the request URL does not match any of the patterns in the URLconf and
# it doesn't end in a slash, an HTTP redirect is issued to the same URL with a slash appended.
APPEND_SLASH = True


