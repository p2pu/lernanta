import re

def extract_reply(text):
    """ try to get the actual reply and loose the original message """
    patterns = [
        re.compile('\nOn .*?wrote:\n'),
        re.compile('-----Original Message----'),
        re.compile('________________________________'),
        re.compile('reply+.*?@reply.p2pu.org'),
        re.compile('From: '),
        re.compile('On.*?wrote:'),
        re.compile('On .*'),
        re.compile('-- \n'),
        re.compile('--\n'),
        re.compile('Sent from my iPhone'),
        re.compile('Sent from my BlackBerry'),
    ]   
    for pattern in patterns:
        match = pattern.search(text)
        if match:
            text = text[:match.start()]
            break
    return text

def strip_email_addresses(text):
    return text
