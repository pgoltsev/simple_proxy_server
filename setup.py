SOURCE_URL = 'http://habrahabr.ru/interesting/'
# you can use (u'body',) for whole body parsing
# CONTENT_TAG_FOR_PARSING = (u'body',)
CONTENT_TAG_FOR_PARSING = (u'div', (u'class', u'content html_format'))
EXCLUDE_TAGS = (u'script', u'code')
DEFAULT_ENCODING = 'utf-8'
SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 8081
OPEN_AT_STARTUP = True
