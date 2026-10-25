"""Rollback-only synthetic cardinality benchmark; never publishes test catalogue rows."""
import json,statistics,time,uuid
from django.core.management.base import BaseCommand
from django.db import transaction,connection
from django.test import Client
from catalog import models as m
class Command(BaseCommand):
    help='Benchmark catalogue views against synthetic rows inside a transaction that always rolls back.'
    def add_arguments(self,p): p.add_argument('--rows',type=int,default=10000);p.add_argument('--requests',type=int,default=100)
    def handle(self,*args,**opts):
        if not 1<=opts['rows']<=100000: raise ValueError('Use 1–100000 rows.')
        with transaction.atomic():
            brand=m.Brand.objects.first();source=m.Source.objects.first();ingredient=m.Ingredient.objects.get(slug='juniper')
            products=[m.Product(id=uuid.uuid4(),slug=f'benchmark-{uuid.uuid4()}',brand=brand,name=f'Synthetic benchmark {i:06}',description='Synthetic rollback-only row',status='published') for i in range(opts['rows'])]
            m.Product.objects.bulk_create(products,batch_size=1000)
            m.Variant.objects.bulk_create([m.Variant(product=p,name='Synthetic',market='Test',abv=40,volume_ml=700,source=source) for p in products],batch_size=1000)
            recipes=[m.Recipe(product=p,version='Synthetic',source=source) for p in products];m.Recipe.objects.bulk_create(recipes,batch_size=1000)
            m.RecipeIngredient.objects.bulk_create([m.RecipeIngredient(recipe=r,ingredient=ingredient,source=source) for r in recipes],batch_size=1000)
            if connection.vendor=='postgresql':
                with connection.cursor() as cur:
                    for table in ['catalog_product','catalog_variant','catalog_recipe','catalog_recipeingredient']:cur.execute(f'ANALYZE {table}')
            client=Client(HTTP_HOST="localhost");timings={}
            for label,path in [('catalogue','/api/v1/products?limit=24'),('ingredient_search','/api/v1/products?q=juniper&limit=24')]:
                values=[]
                for _ in range(opts['requests']):
                    start=time.perf_counter();response=client.get(path);values.append((time.perf_counter()-start)*1000)
                    if response.status_code!=200: raise ValueError('Benchmark request failed.')
                values.sort();timings[label]={'median_ms':round(statistics.median(values),2),'p95_ms':round(values[int(len(values)*.95)],2)}
            report={'synthetic_products':opts['rows'],'total_products':m.Product.objects.count(),'variants_per_synthetic_product':1,'ingredients_per_synthetic_recipe':1,'requests_per_path':opts['requests'],'concurrency':1,'database':connection.vendor,'timings':timings,'scope':'In-process Django HTTP test client, production query code, synthetic single-ingredient rows, one rollback-only transaction. No network, TLS or concurrent-write claim.'}
            transaction.set_rollback(True)
        self.stdout.write(json.dumps(report,indent=2))
