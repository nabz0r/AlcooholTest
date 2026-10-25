"""Versioned public catalogue interchange. User records never enter public exports."""
import json, hashlib, os, subprocess
from pathlib import Path
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID
from django.conf import settings
from django.db import transaction, connection
from django.utils import timezone
from django.core.exceptions import ValidationError
from jsonschema import Draft202012Validator
from . import models as m
TABLES={'sources':m.Source,'places':m.Place,'brands':m.Brand,'ingredients':m.Ingredient,'compounds':m.Compound,'ingredient_compounds':m.IngredientCompound,'products':m.Product,'bottle_assets':m.BottleAsset,'variants':m.Variant,'recipes':m.Recipe,'recipe_ingredients':m.RecipeIngredient,'studies':m.Study,'measurements':m.Measurement,'mechanisms':m.Mechanism,'critic_reviews':m.CriticReview,'price_observations':m.PriceObservation}

def encode(value):
    if isinstance(value,(UUID,Decimal)): return str(value)
    if isinstance(value,(date,datetime)): return value.isoformat()
    raise TypeError(type(value).__name__)

def validate_document(doc):
    schema=json.loads(settings.SCHEMA_FILE.read_text())
    errors=sorted(Draft202012Validator(schema).iter_errors(doc),key=lambda e:str(e.path))
    if errors: raise ValueError('; '.join(f'{list(e.path)}: {e.message}' for e in errors[:8]))
    seen={}
    for key,model in TABLES.items():
        seen[key]=set()
        for row in doc['tables'][key]:
            if row['id'] in seen[key]: raise ValueError(f'Duplicate ID in {key}.')
            seen[key].add(row['id'])
            obj=model(**row); obj.full_clean(validate_unique=False,validate_constraints=False,exclude=[f.name for f in model._meta.fields if f.many_to_one])
    # Cross-reference against the document, never silently rely on an existing DB.
    reverse={model:key for key,model in TABLES.items()}
    for key,model in TABLES.items():
        for row in doc['tables'][key]:
            for f in model._meta.fields:
                if f.many_to_one and row.get(f.attname) is not None and row.get(f.attname) not in seen[reverse[f.related_model]]: raise ValueError(f'Missing reference {key}.{f.attname}')
    return {k:len(v) for k,v in doc['tables'].items()}

@transaction.atomic
def import_document(doc):
    counts=validate_document(doc)
    # Serialise concurrent imports; all rows are committed or none are.
    if connection.vendor=='postgresql':
        with connection.cursor() as cur: cur.execute('SELECT pg_advisory_xact_lock(72470521)')
    for key,model in TABLES.items():
        for row in doc['tables'][key]:
            values=dict(row); pk=values.pop('id'); values.pop('updated_at',None)
            if model is m.Product: values.pop('photo',None) # Never accept filesystem paths from imports.
            if model is m.Product: values.pop('edition_of_id',None); values.pop('merged_into_id',None)
            obj,_=model.objects.update_or_create(id=pk,defaults=values)
            obj.full_clean()
    for row in doc['tables']['products']:
        obj=m.Product.objects.get(pk=row['id']); obj.edition_of_id=row.get('edition_of_id'); obj.merged_into_id=row.get('merged_into_id'); obj.full_clean(); obj.save()
    return counts

def rows_for(key,model):
    qs=model.objects.all()
    if key=='products': qs=qs.filter(status='published')
    if key in ['variants','recipes']: qs=qs.filter(product__status='published')
    if key=='recipe_ingredients': qs=qs.filter(recipe__product__status='published')
    if key=='bottle_assets': qs=qs.filter(product__status='published')
    if key=='critic_reviews': qs=qs.filter(product__status='published')
    if key=='price_observations': qs=qs.filter(variant__product__status='published')
    if key=='measurements': qs=qs.filter(variant__product__status='published')
    fields=[f.attname for f in model._meta.fields if f.name not in ['updated_at','photo']]
    return qs.order_by('id').values(*fields).iterator(chunk_size=1000)

@transaction.atomic
def export_file(path,kind):
    if connection.vendor=='postgresql' and len(connection.atomic_blocks)==1:
        with connection.cursor() as cur: cur.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ, READ ONLY')
    with path.open('w') as out:
        if kind=='json':
            out.write('{"schema_version":"1.0","generated_at":'+json.dumps(timezone.now().isoformat())+',"tables":{')
            for n,(key,model) in enumerate(TABLES.items()):
                if n: out.write(',')
                out.write(json.dumps(key)+':[')
                for i,row in enumerate(rows_for(key,model)):
                    if i: out.write(',')
                    out.write(json.dumps(row,default=encode,sort_keys=True))
                out.write(']')
            out.write('}}')
        else:
            out.write(json.dumps({'type':'manifest','schema_version':'1.0','generated_at':timezone.now().isoformat()})+'\n')
            for key,model in TABLES.items():
                for row in rows_for(key,model): out.write(json.dumps({'table':key,'record':row},default=encode,sort_keys=True)+'\n')

def run_job(job):
    root=settings.EXPORT_ROOT; root.mkdir(parents=True,exist_ok=True)
    final=root/f'{job.id}.{ "json" if job.kind=="import" else ("dump" if job.kind=="sql" else "jsonl" if job.kind in ["discover","research","prices"] else job.kind)}'
    temp=root/f'{job.id}.tmp'
    try:
        if job.kind in ['discover','research']:
            from .ingestion import discover_to_file,research_to_file
            (discover_to_file if job.kind=='discover' else research_to_file)(temp)
        elif job.kind=='prices':
            from .price_archive import price_archive_to_file
            price_archive_to_file(temp)
        elif job.kind=='import':
            doc=json.loads((root/f'{job.id}.input').read_text())
            result=import_document(doc)
            temp.write_text(json.dumps({'imported':result,'mode':'transactional upsert; no deletion'}))
        elif job.kind=='sql':
            if connection.vendor!='postgresql': raise ValueError('SQL backup requires PostgreSQL.')
            cfg=settings.DATABASES['default']
            env={**os.environ,'PGPASSWORD':cfg['PASSWORD']}
            # Fixed executable and argument array: no shell interpolation.
            subprocess.run(['pg_dump','--host',cfg['HOST'],'--port',str(cfg['PORT']),'--username',cfg['USER'],'--dbname',cfg['NAME'],'--format=custom','--no-owner','--no-acl','--file',str(temp)],env=env,check=True,capture_output=True,timeout=600)
        else: export_file(temp,job.kind)
        digest=hashlib.sha256()
        with temp.open('rb') as stream:
            for chunk in iter(lambda:stream.read(1024*1024),b''): digest.update(chunk)
        os.replace(temp,final)
        job.filename=final.name; job.checksum=digest.hexdigest(); job.size=final.stat().st_size; job.status='done'
        (root/f'{job.id}.manifest.json').write_text(json.dumps({'id':str(job.id),'kind':job.kind,'sha256':job.checksum,'bytes':job.size,'schema_version':'1.0','contains_private_data':job.kind=='sql'},indent=2))
    except Exception as exc:
        job.status='failed'; job.error=f'{type(exc).__name__}: operation failed. Check worker logs.'
        import logging
        logging.getLogger(__name__).exception('Job %s failed',job.id)
    finally:
        temp.unlink(missing_ok=True); (root/f'{job.id}.input').unlink(missing_ok=True)
        job.finished_at=timezone.now(); job.save()
