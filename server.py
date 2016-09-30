try:
    from BaseHTTPServer import BaseHTTPRequestHandler, HTTPServer
except ImportError:
    from http.server import BaseHTTPRequestHandler, HTTPServer
try:
    from HTMLParser import HTMLParser
except ImportError:
    from html.parser import HTMLParser
try:
    from StringIO import StringIO
except ImportError:
    from io import BytesIO as StringIO
import gzip

try:
    from urllib2 import urlopen, Request
except ImportError:
    from urllib.request import urlopen, Request
import collections

try:
    import urlparse
except ImportError:
    import urllib.parse as urlparse
import webbrowser

import re
import setup


class Transformer(object):
    search_word = re.compile(r'\b([\S]{6})\b', re.IGNORECASE | re.UNICODE)
    replace_word = r'\1&#8482;'

    def __call__(self, *args, **kwargs):
        return self.transform_func(*args, **kwargs)

    def transform_func(self, text):
        return self.search_word.sub(self.replace_word, text)


transformer = Transformer()


class ContentParser(HTMLParser):
    # content in those tags excluded from replacement
    exclude_text_in_tags = setup.EXCLUDE_TAGS
    content_tag = setup.CONTENT_TAG_FOR_PARSING[0]
    content_tag_params = list(setup.CONTENT_TAG_FOR_PARSING[1:])

    def __init__(self, transform_func):
        self.transform_func = transform_func
        self.no_replace = False
        self.tags_fifo = collections.deque()
        self.content_tag_counter = 0
        self.buffer = collections.deque()
        HTMLParser.__init__(self)

    @property
    def result_html(self):
        return u''.join(self.buffer)

    def append_text(self, text):
        self.buffer.append(text)

    def handle_startendtag(self, tag, attrs):
        self.append_text(self.get_starttag_text())

    def handle_starttag(self, tag, attrs):
        self.append_text(self.get_starttag_text())
        if tag == self.content_tag:
            self.content_tag_counter += 1
            if not self.content_tag_params or attrs == self.content_tag_params:
                self.tags_fifo.append({'attrs': attrs, 'depth': self.content_tag_counter})

        self.no_replace = tag in self.exclude_text_in_tags

    def handle_comment(self, data):
        self.append_text(u'<!--%s-->' % data)

    def handle_entityref(self, name):
        self.append_text(u'&%s;' % name)

    def handle_decl(self, decl):
        self.append_text(u'<!%s>' % decl)

    def handle_charref(self, name):
        self.append_text(u'&#%s;' % name)

    def handle_endtag(self, tag):
        if tag == self.content_tag:
            if len(self.tags_fifo) > 0:
                last_tag = self.tags_fifo[-1]
                if (not self.content_tag_params or last_tag['attrs'] == self.content_tag_params) and \
                        last_tag['depth'] == self.content_tag_counter:
                    self.tags_fifo.pop()
            self.content_tag_counter -= 1

        self.append_text(u'</%s>' % tag)

    def handle_data(self, data):
        if not self.no_replace and self.tags_fifo:
            data = self.transform_func(data)
        self.append_text(data)


class HttpProcessor(BaseHTTPRequestHandler):
    def send_headers(self, code, params):
        self.send_response(code)
        for key, value in params.items():
            self.send_header(key, value)
        self.end_headers()

    @staticmethod
    def get_encoding(headers):
        content_type = headers['content-type']
        enc_list = content_type.split('charset=')
        return enc_list[-1] if len(enc_list) > 1 else setup.DEFAULT_ENCODING

    @staticmethod
    def unzip_response(response):
        if response.info().get('Content-Encoding') == 'gzip':
            buffer = StringIO(response.read())
            return gzip.GzipFile(fileobj=buffer)

        return response

    @staticmethod
    def create_request(url):
        request = Request(url)
        request.add_header('Accept-Encoding', 'gzip')
        return request

    def read_data_and_replace_content(self, response, encoding):
        html = response.read().decode(encoding)
        content_parser = ContentParser(transformer)
        content_parser.feed(html)
        return content_parser.result_html.encode(encoding)

    def redirect_to_original_site(self):
        url_parts = urlparse.urlparse(setup.SOURCE_URL)
        self.send_headers(302, {
            'Location': urlparse.urlunparse([url_parts.scheme, url_parts.netloc, self.path, '', '', ''])
        })

    def do_GET(self):
        if self.path != '/':
            # forward all other requests to the original site (images, scripts, etc.)
            self.redirect_to_original_site()
            return

        response = urlopen(self.create_request(setup.SOURCE_URL))
        encoding = self.get_encoding(response.headers)
        response = self.unzip_response(response)
        self.send_headers(200, {'Content-Type': 'text/html'})
        self.wfile.write(self.read_data_and_replace_content(response, encoding))


server = HTTPServer((setup.SERVER_ADDRESS, setup.SERVER_PORT), HttpProcessor)

if __name__ == '__main__':
    url = 'http://%s:%d/' % (setup.SERVER_ADDRESS, setup.SERVER_PORT)
    print('Open {} in your browser.'.format(url))
    if setup.OPEN_AT_STARTUP:
        webbrowser.open(url)
    server.serve_forever()
