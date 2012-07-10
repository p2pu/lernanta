from settings import *
import datetime

# Useful settings for running a local instance of batucada.

DEBUG = True
TEMPLATE_DEBUG = DEBUG


# Include at least one admin who will receive the reports of abuse.
ADMINS = (
    # ('Your Name', 'your_email@domain.com'),
)
MANAGERS = ADMINS
ADMIN_PROJECT_CREATE_EMAIL = tuple()


DATABASES = {

    # Uncomment the following lines to run on SQLite for development.
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'lernanta.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',  # An empty string means localhost.
        'PORT': ''  # An empty string means the default port.
    },

    # Uncomment the following lines to run with MySQL.
    # Remember to also comment the previous section which enables SQLite.
#    'default': {
#        'NAME': 'lernanta',
#        'ENGINE': 'django.db.backends.mysql',
#        'USER': 'lernanta',
#        'PASSWORD': '',
#        'HOST': '',  # An empty string means localhost.
#        'PORT': '',  # An empty string means the default port.
#        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
#    },

    # Uncomment the following lines to enable integration
    # with the old drupal site.
#    'drupal_db': {
#        'NAME': 'drupal_db',
#        'TEST_NAME': 'drupal_db',
#        'ENGINE': 'django.db.backends.mysql',
#        'USER': 'drupal_db_user',
#        'PASSWORD': '',
#        'HOST': '',  # An empty string means localhost.
#        'PORT': '',  # An empty string means the default port.
#        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
#    },

    # Uncomment the following lines to enable integration
    # with the badges pilot.
#    'badges_db': {
#        'NAME': 'badges_db',
#        'TEST_NAME': 'badges_db',
#        'ENGINE': 'django.db.backends.mysql',
#        'USER': 'badges_db_user',
#        'PASSWORD': '',
#        'HOST': '',  # An empty string means localhost.
#        'PORT': '',  # An empty string means the default port.
#        'OPTIONS': {'init_command': 'SET storage_engine=InnoDB'},
#    },

}

TIME_ZONE = 'America/Toronto'

# Set to True to use https
SESSION_COOKIE_SECURE = False

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'std3j$ropgs216z1aa#8+p3a2w2q06mns_%2vfx_#$$i!+6o+x'

# Make sure this is unique and random
INTERNAL_API_KEY = 'dmWfPniIMhkPRmiLosOEGmVVppfoyEFhpoIgElfyUpgxtJNCsDcdnFZIeYIUuiom'

DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

INSTALLED_APPS += (
    'debug_toolbar',
    'django_nose',
    'django.contrib.admindocs',
)

MIDDLEWARE_CLASSES += (
    'debug_toolbar.middleware.DebugToolbarMiddleware',
)
INTERNAL_IPS = ('127.0.0.1',)

# Sign up for an API key at https://www.google.com/recaptcha/admin/create
RECAPTCHA_PUBLIC_KEY = ''
RECAPTCHA_PRIVATE_KEY = ''
RECAPTCHA_USE_SSL = True
RECAPTCHA_URL = ('https://api-secure.recaptcha.net/challenge?k=%s' %
                 RECAPTCHA_PUBLIC_KEY)

# Embed.ly
EMBEDLY_KEY = ''
EMBEDLY_CACHE_EXPIRES = datetime.timedelta(weeks=4)

P2PU_EMBEDS= (
    'http://pad.p2pu.org/',
    'http://etherpad.p2pu.org/'
)

# Use dummy caching for development.
CACHE_BACKEND = 'dummy://'
CACHE_PREFIX = 'lernanta'
CACHE_COUNT_TIMEOUT = 60

# RabbitMQ Config
BROKER_HOST = "localhost"
BROKER_PORT = 5672
BROKER_USER = ""
BROKER_PASSWORD = ""
BROKER_VHOST = ""

# Execute celery tasks locally, so you don't have to be running an MQ
CELERY_ALWAYS_EAGER = True

# Path to ffmpeg. This will have to be installed to create video thumbnails
FFMPEG_PATH = '/usr/bin/ffmpeg'

# Set to True at production before upgrading lernanta.
# Remember to login as admin before activating maintenance mode.
MAINTENANCE_MODE = False

# Prefixes ignored by the ProfileExistMiddleware.
NO_PROFILE_URLS = ('/media/', '/admin-media/',)

# Drupal urls
DRUPAL_URL = 'http://archive.p2pu.org/'
DRUPAL_FILES_URL = DRUPAL_URL + 'sites/archive.p2pu.org/files/'
FILE_PATH_PREFIX = 'sites/archive.p2pu.org/files/'

# Badges pilot url
BADGE_URL = 'http://badges.p2pu.org/badges/%(badge_id)s/%(badge_tag)s'
BADGE_EVIDENCE_URL = BADGE_URL + '?user_filter=%(username)s#badge_data'
BADGE_IMAGES_DIR = path('media/images/pilotbadges/')
BADGE_IMAGES_URL = 'images/pilotbadges/'

INVALID_USERNAMES = ('webcraft', 'about', 'user', 'sosi', 'get-involved',
    'math-future', 'license', 'contact-us', 'values', 'privacy',
    'terms-of-use', 'news', 'create-draft-course', 'create-draft-course-panel',
    'supporters', 'about-p2pu', 'tag', 'tags','school-of-ed',)

# Pagination
PAGINATION_DEFAULT_ITEMS_PER_PAGE = 20

# Used for open badges integration.
MOZBADGES = {
    # location of badge hub. Currently this is the only public one
    'hub': 'http://beta.openbadges.org',

    # method for getting badges for a user. Called with user object.
    'badge_getter': 'badges.models.get_awarded_badges',
}

# Metrics
STATISTICS_CSV_DOWNLOADERS = ('kfasimpaur',)

BOT_NAMES =['Googlebot', 'Slurp', 'Twiceler', 'msnbot',
    'KaloogaBot', 'YodaoBot', 'Baiduspider', 'googlebot',
    'Speedy Spider', 'DotBot']

# Single Sign On (with multipass tender tokens)
SSO_REDIRECT_FIELD_NAMES = ['to']
SSO_EXTERNAL_REDIRECTS = {
    'http://help.p2pu.org/': {
        'site_key': 'p2pu',
        'api_key': ''
    },
}

# Statsd
STATSD_HOST = 'stats.p2pu.org'
STATSD_PORT = 8125

