from db import MetaTag

def save_tag(item_uri, key, value):
    if MetaTag.objects.filter(item_uri=item_uri, key=key).exists():
        meta = MetaTag.objects.get(item_uri=item_uri, key=key)
        if len(value) == 0:
            meta.delete()
        else:
            meta.value = value
            meta.save()
    elif len(value) > 0:
        meta = MetaTag(
            item_uri=item_uri,
            key=key,
            value=value
        )
        meta.save()


def get_tags(item_uri):
    meta_tags = MetaTag.objects.filter(item_uri=item_uri)
    meta = {}
    for tag in meta_tags:
        meta[tag.key] = tag.value
    return meta
