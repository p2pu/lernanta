import re

def extract_reply(text):
    patterns = [
        re.compile('\nOn .*?wrote:\n'),
        re.compile('-- \n'),
        re.compile('--\n'),
        re.compile('-----Original Message----'),
        re.compile('________________________________'),
        re.compile('From: '),
        re.compile('Sent from my iPhone'),
        re.compile('Sent from my BlackBerry')
    ]   
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            print('match!')
            text = text[:match.start()]
    return text
