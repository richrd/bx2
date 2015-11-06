
import re
import datetime


def starts(s, what):
    """Check if a string begins with given string or any one in given list."""
    if isinstance(what, str):
        what = [what]
    for item in what:
        if s.find(item) == 0:
            return True
    return False


def ends(s, what):
    """Check if a string ends with given string or any one in given list."""
    s = s[::-1]
    if isinstance(what, str):
        what = [what]
    for item in what:
        if s.find(item[::-1]) == 0:
            return True
    return False


def str_to_seconds(s):
    """Convert string durations to seconds.

    Format is "3d12h30m5s" and only seconds are required eg. "30s"
    """
    units = {
        "d": 24*60*60,
        "h": 60*60,
        "m": 60,
        "s": 1,
        }
    s = s.strip().lower()
    if len(s) < 2:
        return False
    if s[-1] in units.keys():
        unit = units[s[-1]]
    else:
        return False
    try:
        part = s[:-1].replace(",", ".")
        n = float(part)
    except:
        return False

    return n*unit


def escape_html(self, html):
    import html.parser
    html_parser = html.parser.HTMLParser()
    unescaped = html_parser.unescape(html)
    return unescaped


def replace_url_to_link(value):
    # Replace url to link
    urls = re.compile(r"((https?):((//)|(\\\\))+[\w\d:#@%/;$()~_?\+-=\\\.&]*)", re.MULTILINE | re.UNICODE)
    value = urls.sub(r'<a href="\1" target="_blank">\1</a>', value)
    return value


def format_timestamp(stamp, format="%Y-%m-%d %H:%M:%S"):
    return datetime.datetime.fromtimestamp(stamp).strftime(format)
