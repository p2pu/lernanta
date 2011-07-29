import base64

def process_getter(q_getter=''):
    # too clever? not clever enough?
    _module, _method = q_getter.rsplit('.', 1)
    module = __import__(_module, globals(), locals(), [_method], -1)
    return getattr(module, _method)

def base64url_decode(input):
    input += '=' * (4 - (len(input) % 4))
    return base64.urlsafe_b64decode(input)
def base64url_encode(input):
    return base64.urlsafe_b64encode(input).replace('=', '')
