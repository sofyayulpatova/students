import os

basedir = os.path.abspath(os.path.dirname(__file__))


class Config(object):
    # ...
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              'sqlite:///' + os.path.join(basedir, 'app.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SECRET_KEY = 'a really really really really long secret key'
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 25)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') is not None
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    UPLOAD_FOLDER = '/uploads'
    ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'pptx', 'ppt', 'txt', 'jpeg', 'jpg', 'txt'}
    CLIENT_SECRETS_FILE = "client_secret.json"

    REDIS_URL = os.environ.get('REDIS_URL') or 'redis://'

    # This OAuth 2.0 access scope allows for full read/write access to the
    # authenticated user's account and requires requests to use an SSL connection.
    SCOPES = ['https://www.googleapis.com/auth/calendar']
    API_SERVICE_NAME = 'calendar'
    API_VERSION = 'v3'

    LANGUAGES = ['ru', 'en', 'lv']

    '''
    
    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = ''
    MAIL_DEFAULT_SENDER = ''
    MAIL_PASSWORD = ''
    '''
    ADMINS = ['dvkrrrr@gmail.com']
