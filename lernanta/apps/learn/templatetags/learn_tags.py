from django import template
from l10n.urlresolvers import reverse

register = template.Library()


@register.simple_tag
def learn_default(tag=None, school=None):
    """ return the default URL for the learn page """
    #learn_url = reverse('learn_list', kwargs={'list_name':'community'})
    learn_url = reverse('learn_list', kwargs={'list_name':'community'})
    params = []
    if school:
        learn_url = reverse('learn_schools',
            kwargs={'school_slug':school.slug})
    if tag:
        learn_url = reverse('learn_all')
        params += ['filter_tags=%s' % tag.name]
    if len(params):
        learn_url += "?"
        learn_url += "&".join(params)
    return learn_url


@register.simple_tag
def filter_add_tag(filter_tags, tag):
    """ add a tag to the current filter string """
    filter_list = []
    filter_list += filter_tags
    filter_list += [tag]
    return '|'.join(filter_list)


@register.simple_tag
def filter_remove_tag(filter_tags, tag):
    """ remove a tag from the current filter string """
    filter_list = []
    filter_list += filter_tags
    try:
        filter_list.remove(tag)
    except:
        pass
    return '|'.join(filter_list)
