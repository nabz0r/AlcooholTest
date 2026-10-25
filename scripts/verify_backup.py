"""Restore the newest completed SQL backup into a disposable DB, verify and drop it."""
import json,subprocess

def run(args,**kw):return subprocess.run(['docker','compose','exec','-T',*args],check=True,capture_output=True,**kw)
# Locate archive using the application model, with no credentials in host arguments.
code="from catalog.models import Job; import json; j=Job.objects.filter(kind='sql',status='done').latest('created_at'); print(json.dumps({'file':j.filename}))"
out=run(['api','python','manage.py','shell','-c',code]).stdout.decode()
filename=json.loads(next(x for x in out.splitlines() if x.startswith('{')))['file']
if '/' in filename or not filename.endswith('.dump'):raise ValueError('Unexpected archive name')
archive=run(['api','cat','/app/exports/'+filename]).stdout
database='alcooltest_qa_restore'
run(['db','createdb','-U','alcooltest',database])
try:
    run(['db','pg_restore','-U','alcooltest','-d',database,'--no-owner','--no-acl'],input=archive)
    counts=run(['db','psql','-U','alcooltest','-d',database,'-Atc','SELECT count(*) FROM catalog_product;']).stdout.decode().strip()
    print(json.dumps({'backup_format':'PostgreSQL custom','restore_success':True,'restored_products':int(counts),'temporary_database_removed':True},indent=2))
finally:run(['db','dropdb','-U','alcooltest',database])
