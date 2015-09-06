

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
