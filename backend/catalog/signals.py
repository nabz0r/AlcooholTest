"""Invalidate public Redis response caches only after editorial commits."""
import uuid
from django.db import transaction
from django.db.models.signals import post_save,post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .interchange import TABLES
from .models import Review,BottlePhoto
from redis.exceptions import RedisError
def invalidate():
    try: cache.set('catalogue:revision',uuid.uuid4().hex,timeout=None)
    except (RedisError,OSError): pass
@receiver(post_save)
@receiver(post_delete)
def invalidate_public(sender,**kwargs):
    if sender in set(TABLES.values())|{Review,BottlePhoto}:
        transaction.on_commit(invalidate)
