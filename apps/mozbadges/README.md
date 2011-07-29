# Django Open Badge Integration

## Overview
Step 0: Clone this repo somewhere in your django app's path and enable it in
your setting file's `INSTALLED_APPS`.

While you're mucking around in there, include an additional setting, something
resembling the following:

```python    
MOZBADGES = {
    'hub': 'http://alpha.badgehub.org',
    'badge_getter': 'users.badges.get_awarded_badges',
}
```

Be sure to run the test suite afterwards and make sure everything is kosher.

## Badge Getter

### Input
The badge getter is going to get called a little something like this:

```python
def some_view(request):
    user = request.user
    if user.is_authenticated():
        badges = badge_getter(request.user)
```

Your badge_getter method should take a User object and know how to get awarded
badges from it.

### Output

**This is absolutely going to change. It is currently tailored specifically to
  the p2pu badge pilot data**

The badge processer expects badge_getter to output a dictionary looking something like this:

```python
{
    'proud_js_expert' : {
        'name' : 'JavaScript Expert',
        'url': 'http://example.com/badge-evidence/user-1/js-expert',
        'image_url': 'http://example.com/badge-images/js-expert.png',
        'description': 'Awarded for being totally rad at JavaScript',
        'template': 'http://example.com/badge-requirements/js-expert',
    },
    'ashamed_cobol_master': { ... },
    'reluctant_java_user': { ... },
}
```
You are welcome to include other information in the dictionary; at the moment
it will be ignored. In future versions it will likely be included as extra
metadata passed to the hub.

## How to send badges

**The authenticated user must have an email address associated with their
  account (that is, stored in the auth_user table and accessible by
  django.contrib.auth.models.User). Bad things will happen if the user has no
  email address. Always make sure the user has an email address!**

Hook up a route to the view `send_badges`, and have a logged-in user make an
empty POST request to it.

The return value will be some (potentially) helpful json. You can read the
`status` attribute on the response payload and expect one of three results:
`accepted`, which is good; `failed`, which is bad (validation error) and will
have an additional `errors` attribute which will be fairly annoying to get
data out of because it's keyed by the full URL to each badge you just tried to
send; and `fatal` which is really bad and indicates either sort of server
failure on the hub side (or you specified an valid-looking but bad uri for the
hub in your settings).
