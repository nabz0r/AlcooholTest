from pathlib import Path
from django.core.management.base import BaseCommand
from catalog.interchange import export_file
class Command(BaseCommand):
    def add_arguments(self,p): p.add_argument('path'); p.add_argument('--format',choices=['json','jsonl'],default='json')
    def handle(self,*args,**opts): export_file(Path(opts['path']),opts['format'])
