import bleach

def clean_user_content(content):
    config = {
        'tags': ['table', 'tr', 'th', 'td', 'tbody', 'a', 'iframe'],
        'attributes': {'a': ['href'], 'iframe': ['src', 'width', 'height'] },
        'styles': [],
        'strip': True
    }
    content = bleach.clean(content, **config)
    #TODO
    return content

def clean_trusted_user_content(content):
    bleach.clean(content, strip=True)
    #TODO
    return content
