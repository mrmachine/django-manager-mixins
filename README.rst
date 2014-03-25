Overview
========

Provides a custom manager, ``MixinManager``, that allows queryset mixins to be
dynamically registered based on the model to which the manager is attached. This
manager is used for related fields by default.

Mixins can be explicitly registered, or automatically discovered when declared
as an inner ``QuerySet`` class on a model. Any mixins that are registered for a
model's base classes will also be combined.

Also exposes queryset methods on the manager for convenience.


Installation
============

For basic usage, where you only need to register mixins for your own models,
just place the ``manager_mixins`` package somewhere on your ``$PYTHONPATH``.

If you want to register mixins for 3rd party models, you will need to monkey
patch Django's ``Manager`` class to add ``BaseMixinManager`` to its MRO::

    # settings.py
    # Enable registration and discovery of mixins for any model that uses
    # ``django.db.models.Manager``.
    from manager_mixins.monkeypatch import manager

This monkey patch needs to be imported in ``settings.py``, before the original
manager class is imported by apps being loaded.


Usage
=====

Use ``MixinManager`` as the default manager for any models you want to provide
mixins to, then either declare an inner ``QuerySet`` class on those models or
use ``register_mixin_class()`` to register mixins::

    # models.py
    from django.db import models
    from manager_mixins.managers import MixinManager, register_mixin_class

    # Declare a mixin as an inner ``QuerySet`` class on a model.
    class MyModel(models.Model):
        objects = MixinManager()
        class QuerySet(object):
            def foo(self):
                return self.filter(...)

    # Explicitly register a mixin for a model.
    class OtherModel(models.Model):
        objects = MixinManager()
    class OtherQuerySet(object):
        def bar(self):
            return self.filter(...)
    register_mixin_class(OtherQuerySet, OtherModel)

If you have installed the ``manager`` monkey patch, you can register mixins for
3rd party models that don't normally use ``MixinManager``.

You can even add methods to ALL querysets by registering a mixin for the base
model, ``django.db.models.Model``.


Mixin Classes
=============

A queryset mixin should be an ``object`` subclass. Any methods it provides will
be exposed on managers and querysets for registered models.

Some commonly useful mixins are provided in ``manager_mixins.mixins``:

* ``SelectRelatedMixin`` - uses ``select_related()`` by default. It occurs more
  often that we encounter performance problems when we forget to select related
  models than when we select too many. Use ``select_related(None)`` in those
  few cases.

* ``UpdateOrCreateMixin`` - adds ``update_or_create()``, for Django < 1.7.

Here's how to use them::

    # models.py
    from django.db import models
    from manager_mixins.managers import register_mixin_class
    from manager_mixins.mixins import SelectRelatedMixin, UpdateOrCreateMixin

    class GlobalMixin(SelectRelatedMixin, UpdateOrCreateMixin):
        pass

    register_mixin_class(GlobalMixin, models.Model)

A mixin can provide a ``mixin_default()`` method, which will be called when a
queryset is created by the manager. You can use this method to customise the
default queryset that is returned. For example, by calling ``select_related()``
or ``distinct()``.

If you do provide a ``mixin_default()`` method, you should always call it on the
super class to ensure that it is executed for all registered mixins::

    class DistinctMixin(object):
        def mixin_default(self, *args, **kwargs):
            return super(DistinctMixin, self).mixin_default().distinct()
