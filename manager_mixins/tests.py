from django import VERSION
from django.contrib.sites.models import Site
from django.db import models
from django.test import TestCase
from django.utils.unittest import skipUnless
from manager_mixins.managers import (
    BaseMixinManager, MixinManager, register_mixin_class)
from manager_mixins import mixins

### MODELS ####################################################################

class Discovered(models.Model):
    objects = MixinManager()
    class QuerySet(object):
        def foo(self):
            return 'foo'

class Registered(models.Model):
    objects = MixinManager()

### MIXINS ####################################################################

class GlobalQuerySet(object):
    def baz(self):
        return 'baz'

class RegisteredQuerySet(object):
    def bar(self):
        return 'bar'

### TESTS #####################################################################

class TestMixinManager(TestCase):
    def test_discovered_mixin(self):
        self.assertIsInstance(Discovered.objects.all(), Discovered.QuerySet)
        self.assertEqual(Discovered.objects.foo(), 'foo')

    def test_registered_mixin(self):
        register_mixin_class(RegisteredQuerySet, Registered)
        self.assertIsInstance(Registered.objects.all(), RegisteredQuerySet)
        self.assertEqual(Registered.objects.bar(), 'bar')

    @skipUnless(
        BaseMixinManager in models.Manager.mro(),
        'Base manager not monkey patched.')
    def test_global_mixin(self):
        register_mixin_class(GlobalQuerySet, Site)
        self.assertIsInstance(Site.objects.all(), GlobalQuerySet)
        self.assertEqual(Site.objects.baz(), 'baz')

class TestMixins(TestCase):
    def test_select_related(self):
        register_mixin_class(mixins.SelectRelatedMixin, Site)
        self.assertEqual(Site.objects.all().query.select_related, True)

    @skipUnless(
        VERSION < (1, 7),
        '`update_or_create()` implemented natively in Django 1.7')
    def test_update_or_create(self):
        register_mixin_class(mixins.UpdateOrCreateMixin, Site)
        self.assertEqual(Site.objects.count(), 1)
        obj, created = Site.objects.update_or_create(
            name='test', domain='test.com')
        self.assertTrue(created)
        obj, created = Site.objects.update_or_create(
            name='test', defaults=dict(domain='www.test.com'))
        self.assertFalse(created)
        self.assertEqual(
            Site.objects.filter(domain='www.test.com').count(), 1)
