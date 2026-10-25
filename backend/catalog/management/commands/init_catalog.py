from django.core.management.base import BaseCommand
from django.core.management import call_command
from catalog.models import Product
class Command(BaseCommand):
    help='Seed only on an empty catalogue; never overwrite editorial changes on restart.'
    def handle(self,*args,**opts):
        if not Product.objects.exists(): call_command('seed')
        from catalog.models import PriceArchiveTarget
        if not PriceArchiveTarget.objects.exists():call_command('sync_research')
