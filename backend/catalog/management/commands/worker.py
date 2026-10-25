import time
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from catalog.models import Job,RateBucket
from catalog.interchange import run_job
class Command(BaseCommand):
    help='Process durable export/import jobs; run one or more workers with PostgreSQL.'
    def add_arguments(self,p): p.add_argument('--once',action='store_true')
    def handle(self,*args,**opts):
        while True:
            # A job exceeding the hard execution budget is failed, never silently duplicated.
            Job.objects.filter(status='running',started_at__lt=timezone.now()-timedelta(minutes=15)).update(status='failed',error='Worker interrupted or execution deadline exceeded; create a new job.',finished_at=timezone.now())
            RateBucket.objects.filter(window__lt=int(time.time())//300-2).delete()
            with transaction.atomic():
                job=Job.objects.select_for_update(skip_locked=True).filter(status='queued').order_by('created_at').first()
                if job and job.kind=='import':
                    from django.conf import settings
                    if not (settings.EXPORT_ROOT/f'{job.id}.input').exists(): job=None
                if job: job.status='running'; job.started_at=timezone.now(); job.save()
            if job: run_job(job)
            if opts['once']: return
            if not job: time.sleep(2)
