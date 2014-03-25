"""
Monkey patch ``django.db.models.Manager`` by adding ``BaseMixinManager`` to its
MRO, so we can register mixins for 3rd party models.
"""
from django.db import models
from manager_mixins.managers import BaseMixinManager

class Manager(BaseMixinManager, models.Manager):
	pass

models.Manager = Manager
