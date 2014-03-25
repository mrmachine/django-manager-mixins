"""
Commonly useful queryset mixins.
"""
class SelectRelatedMixin(object):
    """
    Uses ``select_related()`` by default. It is more often that we encounter
    performance problems when we forget to select related models than when we
    selected too many related models.
    """
    def mixin_default(self, *args, **kwargs):
        queryset = super(SelectRelatedMixin, self) \
            .mixin_default().select_related()
        return queryset

class UpdateOrCreateMixin(object):
    """
    Adds ``update_or_create()``, for Django < 1.7.
    """
    def update_or_create(self, **kwargs):
        # HACK: Look at `core_filters` to determine related fields that should
        # be added to lookup kwargs (when called from a reverse/related
        # manager). Strip "__exact" from the lookup.
        for k, v in getattr(self, 'core_filters', {}).items():
            kwargs[k.replace('__exact', '').replace('__', '_')] = v
        obj, created = self.get_or_create(**kwargs)
        if not created:
            for k, v in kwargs.get('defaults', {}).iteritems():
                setattr(obj, k, v)
            obj.save(force_update=True)
        return obj, created
