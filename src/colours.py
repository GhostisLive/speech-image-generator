def __format(colour, text):
    return f"{colour}{text}\033[00m"

def red(text):
    return __format("\033[91m", text)

def green(text):
    return __format("\033[92m", text)

def blue(text):
    return __format("\033[94m", text)

def yellow(text):
    return __format("\033[93m", text)
