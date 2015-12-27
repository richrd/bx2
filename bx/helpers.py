
import re
import json
import random
import datetime


def merge(x, y):
    # store a copy of x, but overwrite with y's values where applicable
    merged = dict(x, **y)
    xkeys = x.keys()

    # if the value of merged[key] was overwritten with y[key]'s value
    # then we need to put back any missing x[key] values
    for key in xkeys:
        # if this key is a dictionary, recurse
        if isinstance(x[key], dict) and key in y.keys():
            merged[key] = merge(x[key], y[key])
    return merged


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


def seconds_to_duration(sec):
    m, s = divmod(sec, 60)
    h, m = divmod(m, 60)
    d, h = divmod(h, 24)
    return "%d days %d:%02d:%02d" % (d, h, m, s)


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


# HSV values in [0..1]
# returns [r, g, b] values from 0 to 255
def hsv_to_rgb(h, s, v):
    h_i = int(h*6)
    f = h*6 - h_i
    p = v * (1 - s)
    q = v * (1 - f*s)
    t = v * (1 - (1 - f) * s)
    if h_i == 0:
        r, g, b = v, t, p
    if h_i == 1:
        r, g, b = q, v, p
    if h_i == 2:
        r, g, b = p, v, t
    if h_i == 3:
        r, g, b = p, q, v
    if h_i == 4:
        r, g, b = t, p, v
    if h_i == 5:
        r, g, b = v, p, q
    return (int(r*256), int(g*256), int(b*256))


def generate_colors(n):
    # use golden ratio
    golden_ratio_conjugate = 0.618033988749895
    # h = rand # use random start value
    h = random.random()  # random start value
    i = 0
    colors = []
    while i < n:
        h += golden_ratio_conjugate
        h = h % 1
        colors.append(hsv_to_rgb(h, 0.5, 0.95))
        i += 1
    return colors


def store_json(file, data):
    f = open(file, "w")
    f.write(json.dumps(data))
    f.close()


def load_json(file):
    f = open(file)
    data = f.read()
    f.close()
    return json.loads(data)


def send_all_to_socket(self, data, sock):
    # FIXME: deprecate
    # TODO: Might want to check irc_connected and irc_running before trying to send
    left = data
    while left != "":
        data = bytes(data, self.outgoing_encoding)
        sent = sock.send(data)
        if len(left) == sent:
            return True
        left = left[sent:]
    return False
