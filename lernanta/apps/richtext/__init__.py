import bleach


DEFAULT_CONFIG = {
    'skin': 'v2',
    'toolbar': 'Full',
    'height': 291,
    'width': 618,
    'filebrowserWindowWidth': 940,
    'filebrowserWindowHeight': 747,
}


CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': [
            ['Source', '-', 'Bold', 'Italic', '-', 'Link', 'Unlink'],
        ],
        'skin': 'kama',
        'width': '420',
        'height': '110',
        'removePlugins': 'resize, elementspath',
        'toolbarCanCollapse': False,
        'extraPlugins': 'embed,prettify',
        'format_tags': 'p;h1;h2;h3;h4;h5;h6',
        'prettify': {
            'element': 'pre',
            'attributes': {'class': 'prettyprint'}},
    },
    'rich': {
        'toolbar': [
            ['Source'],
            ['Bold', 'Italic', 'Underline', 'Strike', 'Subscript',
                'Superscript'],
            ['JustifyLeft', 'JustifyCenter', 'JustifyRight', 'JustifyBlock'],
            ['NumberedList', 'BulletedList', 'HorizontalRule', 'Outdent',
                'Indent', 'SyntaxHighlighting', 'Blockquote'],
            ['Maximize'],
            ['Link', 'Unlink', 'Image', 'Embed',
                'Smiley', 'SpecialChar', 'Table'],
            ['Format', 'Font', 'FontSize', 'TextColor', 'BGColor'],
        ],
        'skin': 'kama',
        'width': '568',
        'height': '255',
        'removePlugins': 'resize, elementspath',
        'toolbarCanCollapse': False,
        'extraPlugins': 'embed,prettify',
        'format_tags': 'p;h1;h2;h3;h4;h5;h6',
        'prettify': {'element': 'pre', 'attributes': {'class': 'prettyprint'}},
    },
}
CKEDITOR_CONFIGS['trusted'] = CKEDITOR_CONFIGS['rich']
# Constants for cleaning ckeditor html.

REDUCED_ALLOWED_TAGS = ('a', 'b', 'em', 'i', 'strong', 'p', 'u', 'strike',
    'sub', 'sup', 'br')

RICH_ALLOWED_TAGS = REDUCED_ALLOWED_TAGS + ('h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'ol', 'ul', 'li', 'hr', 'blockquote',
        'span', 'pre', 'code', 'div', 'img',
        'table', 'thead', 'tr', 'th', 'caption', 'tbody', 'td', 'br')


REDUCED_ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'name', 'class', 'target'],
}

RICH_ALLOWED_ATTRIBUTES = REDUCED_ALLOWED_ATTRIBUTES.copy()

RICH_ALLOWED_ATTRIBUTES.update({
    'img': ['src', 'alt', 'style', 'title'],
    'p': ['style'],
    'table': ['align', 'border', 'cellpadding', 'cellspacing',
        'style', 'summary'],
    'th': ['scope'],
    'span': ['style'],
    'pre': ['class'],
    'code': ['class'],
    'h1': ['class'],
})


RICH_ALLOWED_STYLES = ('text-align', 'margin-left', 'border-width',
    'border-style', 'margin', 'float', 'width', 'height',
    'font-family', 'font-size', 'color', 'background-color')


BLEACH_CLEAN = {
    'default': {
        'tags': REDUCED_ALLOWED_TAGS,
        'attributes': REDUCED_ALLOWED_ATTRIBUTES,
        'styles': [],
        'strip': True,
    },
    'rich': {
        'tags': RICH_ALLOWED_TAGS,
        'attributes': RICH_ALLOWED_ATTRIBUTES,
        'styles': RICH_ALLOWED_STYLES,
        'strip': True,
    },
}


def clean_html(config_name, value):
    if config_name == 'trusted':
        return value
    if value:
        return bleach.clean(value, **BLEACH_CLEAN[config_name])
    else:
        return value
