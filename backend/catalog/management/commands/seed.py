import json
from django.core.management.base import BaseCommand
from django.conf import settings
from catalog.interchange import import_document
class Command(BaseCommand):
    help='Load the curated seed. Explicit command; never overwrites edits on application restart.'
    def handle(self,*args,**opts): self.stdout.write(str(import_document(json.loads(settings.SEED_FILE.read_text()))))
