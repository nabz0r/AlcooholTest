import json
from django.core.management.base import BaseCommand
from django.db import models
from django.conf import settings
from catalog.interchange import TABLES
class Command(BaseCommand):
    help='Generate the strict public JSON schema from the normalized model fields.'
    def handle(self,*args,**opts):
        tables={}
        for key,model in TABLES.items():
            props={}
            for f in model._meta.fields:
                if f.name in ['updated_at','photo']: continue
                if isinstance(f,(models.UUIDField,models.ForeignKey)): rule={'type':'string','pattern':'^[0-9a-fA-F-]{36}$'}
                elif isinstance(f,models.BooleanField): rule={'type':'boolean'}
                elif isinstance(f,models.IntegerField): rule={'type':'integer','minimum':0}
                elif isinstance(f,models.DecimalField): rule={'type':['string','number'],'pattern':r'^\d+(\.\d+)?$'}
                else:
                    rule={'type':'string','maxLength':f.max_length or 20000}
                    if isinstance(f,models.SlugField): rule['pattern']='^[-a-zA-Z0-9_]+$'
                    if isinstance(f,models.URLField): rule['pattern']='^https?://'
                if f.choices: rule['enum']=[v for v,_ in f.choices]
                if f.null: rule={'anyOf':[rule,{'type':'null'}]}
                props[f.attname]=rule
            tables[key]={'type':'array','maxItems':100000,'items':{'type':'object','additionalProperties':False,'required':[name for name in props if (key,name) not in [*[('ingredients',f) for f in ['navigation_group','plant_part','sensory_role','preparation','technical_notes','profile_source_id']],*[('bottle_assets',f) for f in ['view','pair_key','barcode']],*[('price_observations',f) for f in ['basis','observed_period','date_precision']]]],'properties':props}}
        for table,field,pattern in [('market_price_index_points','period',r'^[12]\d{3}-(0[1-9]|1[0-2])$'),('market_price_indexes','currency',r'^[A-Z]{3}$')]:
            tables[table]['items']['properties'][field]['pattern']=pattern
        tables['price_observations']['items']['properties']['observed_period']['pattern']=r'^$|^[12]\d{3}-(0[1-9]|1[0-2])$'
        schema={'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'https://github.com/nabz0r/AlcooholTest/blob/main/data/catalog/schema.json','title':'Alcooltest catalogue 1.0','type':'object','additionalProperties':False,'required':['schema_version','generated_at','tables'],'properties':{'schema_version':{'const':'1.0'},'generated_at':{'type':'string'},'tables':{'type':'object','additionalProperties':False,'required':[k for k in tables if k not in ['external_photo_references','market_price_indexes','market_price_index_points']],'properties':tables}}}
        settings.SCHEMA_FILE.write_text(json.dumps(schema,indent=2)+'\n')
