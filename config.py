from __future__ import unicode_literals

SOURCE_URL = 'http://habrahabr.ru/interesting/'
# you can use ('body',) for whole body parsing
# CONTENT_TAG_FOR_PARSING = ('body',)
CONTENT_TAG_FOR_PARSING = ('div', ('class', 'content html_format'))
EXCLUDE_TAGS = ('script', 'code')
DEFAULT_ENCODING = 'utf-8'
SERVER_ADDRESS = '127.0.0.1'
SERVER_PORT = 8081
OPEN_AT_STARTUP = True
