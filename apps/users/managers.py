from taggit.utils import require_instance_manager
from taggit.managers import TaggableManager, _TaggableManager


class CategoryTaggableManager(TaggableManager):
    def formfield(self, *args, **kwargs):
        return None
    def __get__(self, instance, model):
        """Override ___get___ to return a slightly tweaked manager class"""
        if instance is not None and instance.pk is None:
            raise ValueError("%s objects need to have a primary key value "
                "before you can access their tags." % model.__name__)
        manager = _CategoryTaggableManager(
            through=self.through, model=model, instance=instance
        )
        return manager


class _CategoryTaggableManager(_TaggableManager):
    @require_instance_manager
    def add(self, category, *tags):
        """This is the same as the _TaggableManager add, except it accepts a
           category parameter."""
        str_tags = set([
            t
            for t in tags
            if not isinstance(t, self.through.tag_model())
        ])
        tag_objs = set(tags) - str_tags
        # If str_tags has 0 elements Django actually optimizes that to not do a
        # query.  Malcolm is very smart.
        existing = self.through.tag_model().objects.filter(
            name__in=str_tags, category=category
        )
        tag_objs.update(existing)

        for new_tag in str_tags - set(t.name for t in existing):
            tag_objs.add(self.through.tag_model().objects.
                create(name=new_tag, category=category))

        for tag in tag_objs:
            self.through.objects.get_or_create(tag=tag, **self._lookup_kwargs())

    @require_instance_manager
    def set(self, category, *tags):
        self.clear(category)
        self.add(category, *tags)

    @require_instance_manager
    def remove(self, category, *tags):
        self.through.objects.filter(**self._lookup_kwargs()).filter(
            tag__name__in=tags, tag__category=category).delete()

    @require_instance_manager
    def clear(self, category):
        self.through.objects.filter(**self._lookup_kwargs()).filter(tag__category=category).delete()

