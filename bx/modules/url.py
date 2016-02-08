
import re

import http.client
import html.parser
import urllib.parse
import urllib.request

from bx import bot_module


class Module(bot_module.BotModule):
    """Paste titles of urls."""

    def on_event(self, event):
        # Don't paste urls in stealth mode
        if self.bot.config.get_stealth():
            return False
        if event.name == "irc_privmsg" and event.window.is_channel():
            self.handle_privmsg(event)
        return False

    def handle_privmsg(self, event):
        """Handle message events."""
        urls = self.find_urls(event.data)
        # Gather titles and send them if found
        titles = []
        for url in urls:
            title = self.get_url_title(url)
            self.logger.debug("title: {}".format(title))
            if title:
                titles.append('"'+title+'"')
        if titles:
            event.window.send(", ".join(titles))

    def find_urls(self, s):
        try:
            re
        except:
            return []
        urls = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', s)
        return urls

    def get_mimetype(self, url):
        """Get the mimetype of an url via response headers."""
        headers = self.get_headers(url)
        content_type = False
        for item in headers:
            if item[0] == 'content-type':
                content_type = item[1].split(";")[0].strip()
                break
        return content_type

    def get_headers(self, url):
        urlobj = urllib.parse.urplarse(url)
        domain = urlobj.netloc
        get = urlobj.path + urlobj.query
        conn = http.client.HTTPConnection(domain, timeout=5)
        # Create a header request to avoid downloading the entire body
        conn.request("HEAD", get)
        res = conn.getresponse()
        headers = res.getheaders()
        return headers

    def find_title(self, data):
        title = False
        if not data:
            return False

        class TitleParser(html.parser.HTMLParser):
            def __init__(self):
                html.parser.HTMLParser.__init__(self)
                self.title = ""
                self.in_title = False

            def handle_starttag(self, tag, attrs):
                if tag == "title":
                    self.in_title = True

            def handle_endtag(self, tag):
                if self.in_title:
                    self.in_title = False
                    self.title = self.title.replace("\n", "")
                    self.title = self.title.replace("\r", "")

            def handle_data(self, data):
                if self.in_title:
                    self.title += data

        # instantiate the parser and fed it some HTML
        parser = TitleParser()
        parser.feed(data)
        title = parser.title or False
        return title

    def get_url_title(self, url):
        """Get <title> tag contents from url."""
        ignore_ext = ["jpg", "png", "gif", "tiff", "psd", "zip", "rar", "sh"]
        if url[-3:] in ignore_ext:
            self.logger.debug("Invalid extension.")
            return False

        # Check that the the resource content type is something relevant
        try:
            content_type = self.get_content_type(url)
            if content_type and content_type not in ["text/html", "text/xhtml", "text/plain"]:
                self.logger.debug("Invalid content-type.")
                return False
        except Exception:
            self.logger.warning("Failed checking content type.")

        # Request the url with a timeout
        response = urllib.request.urlopen(url, timeout=5)
        # Only proceed if request is ok
        if response.getcode() != 200:
            self.logger.debug("Invalid response code.")
            return False
        charset = response.headers.get_param("charset")
        self.logger.debug("Charset detected: {}".format(charset))

        # Read max 50 000 bytes to avoid Out of Memory
        data = response.read(50000)
        if data:
            self.logger.debug("Got url data.")
        if charset:
            data = data.decode(charset)
        else:
            self.logger.warning("No charset, using UTF-8!")
            data = data.decode("utf-8")
        try:
            data = html.parser.HTMLParser().unescape(data)
        except:
            self.logger.exception("Failed to unescape HTML!")

        # Find title, return result if found
        title = self.find_title(data)
        if not title:
            return False
        return title
