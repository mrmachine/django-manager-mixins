from django.db import models
from django.db.models.query import QuerySet
from django.utils.module_loading import import_by_path

_CACHE = {}
_MODELS = {}

class BaseMixin(QuerySet):
    """
    Provides a NOOP ``mixin_default()`` method, so that mixin classes can safely
    call it on their super class in order for multiple inheritance to play nice.
    """
    def mixin_default(self):
        return self

def _cache_queryset_class(model):
    """
    Derives and caches a queryset class from the registered mixins for each
    class in the model's MRO.
    """
    # Use `django.db.models.query.QuerySet` as the base concrete class.
    qs_class = BaseMixin
    # Global mixin.
    mixin = _MODELS.get(models.Model)
    if mixin:
        # Cache the global mixin, so we don't create a separate but identical
        # subclass for every model.
        if not models.Model in _CACHE:
            class qs_class(mixin, qs_class):
                pass
            _CACHE[models.Model] = qs_class
        qs_class = _CACHE[models.Model]
    # Mixin for each class in the model's MRO.
    if hasattr(model, 'mro'):
        for cls in reversed(model.mro()):
            # Get registered or discovered mixin.
            mixin = _MODELS.get(cls, getattr(cls, 'QuerySet', None))
            if mixin and mixin not in qs_class.mro():
                class qs_class(mixin, qs_class):
                    pass
    _CACHE[model] = qs_class

def _get_queryset_class(model=models.Model):
    """
    Returns the queryset class for a model from the cache.
    """
    if not model in _CACHE:
        _cache_queryset_class(model)
    return _CACHE[model]

def register_mixin_class(mixin, model=models.Model):
    """
    Registers a mixin class for a model. If no model is given, the mixin will
    apply globally.
    """
    global _CACHE
    # Invalidate the entire cache, because mixins for a model can inherit from
    # mixins for another model.
    _CACHE = {}
    # Register mixin.
    _MODELS[model] = mixin

class BaseMixinManager(object):
    """
    Uses a queryset class that is dynamically created from mixins.

    Mixins can be explicitly registered, or discovered when declared as an inner
    ``QuerySet`` class on a model. Mixins that are registered or discovered for
    base models will be combined.

    Exposes queryset methods on the manager for convenience.
    """
    use_for_related_fields = True

    def __getattr__(self, name):
        """
        Wrapper for public methods on mixed in classes.
        """
        # Don't expose ``django.db.models.query.QuerySet`` methods or private
        # methods on a mixin class.
        if not hasattr(QuerySet, name) and not name.startswith('_'):
            return getattr(self.get_query_set(), name)
        raise AttributeError(
            '%r object has no attribute %r' % (self.__class__.__name__, name))

    def get_query_set(self):
        """
        Returns a queryset object, taking into account any registered mixins.
        """
        qs_class = _get_queryset_class(self.model)
        queryset = qs_class(self.model, using=self._db)
        # Call ``mixin_default()`` on the queryset (if it exists), so that mixin
        # classes have a hook to customise the default queryset that is
        # returned. E.g. by calling ``select_related()``, ``distinct()``, etc.
        if hasattr(queryset, 'mixin_default'):
            queryset = queryset.mixin_default()
        return queryset

class MixinManager(BaseMixinManager, models.Manager):
    """
    Actual ``django.db.models.Manager`` subclass (not just a mixin) for direct
    use when declaring models.
    """
    pass
