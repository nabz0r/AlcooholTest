"""Server-rendered public discovery pages; the interactive app enhances this HTML."""
import json
from xml.sax.saxutils import escape
from django.conf import settings
from django.http import HttpResponse,Http404,HttpResponsePermanentRedirect
from django.shortcuts import render,get_object_or_404
from .models import Product

PAGES={'':'A world within','discover':'Find your next bottle','catalogue':'The spirits collection','stories':'Stories, craft and culture','research':'Research with context','compare':'Compare spirits','shelf':'Your private shelf','contribute':'Contribute a discovery','account':'Your account','setup':'Set up your instance','studio':'Editorial operations'}
def page(request,section='',slug=None):
    origin=settings.PUBLIC_BASE_URL.rstrip('/')
    product=None;products=Product.objects.filter(status='published',edition_of__isnull=True).select_related('brand').order_by('brand__name','name')
    title=PAGES.get(section,'Alcooltest');description='Explore spirits through their places, craft, disclosed botanicals and source-linked research. An independent open spirits atlas.'
    if slug:
        product=get_object_or_404(Product.objects.select_related('brand','history_source'),slug=slug)
        if product.merged_into_id:return HttpResponsePermanentRedirect('/spirits/'+product.merged_into.slug+'/')
        if product.status!='published':raise Http404
        title=f'{product.brand.name} {product.name}';description=product.description[:300]
        schema={'@context':'https://schema.org','@type':'Product','name':title,'description':description,'brand':{'@type':'Brand','name':product.brand.name},'category':product.category,'url':origin+request.path}
        asset=product.assets.filter(view='front').first()
        if asset:schema['image']=origin+asset.local_path
    elif section not in PAGES:raise Http404
    else:schema={'@context':'https://schema.org','@type':'WebSite' if not section else 'CollectionPage','name':title+' — Alcooltest','url':origin+request.path,'description':description}
    private=section in ['account','setup','studio','shelf','contribute','compare']
    response=render(request,'catalog/page.html',{'title':title,'description':description,'canonical':origin+request.path,'origin':origin,'product':product,'products':products if section in ['','catalogue','discover','stories'] else [],'schema':json.dumps(schema).replace('<','\\u003c').replace('>','\\u003e').replace('&','\\u0026'),'robots':'noindex, nofollow' if private else 'index, follow'})
    if private:response['X-Robots-Tag']='noindex, nofollow'
    return response

def sitemap(request):
    origin=settings.PUBLIC_BASE_URL.rstrip('/');entries=[(origin+p,None) for p in ['/','/discover/','/catalogue/','/stories/','/research/']]
    entries += [(origin+'/spirits/'+p.slug+'/',p.updated_at.date().isoformat()) for p in Product.objects.filter(status='published')]
    xml='<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'+''.join('<url><loc>'+escape(url)+'</loc>'+('<lastmod>'+date+'</lastmod>' if date else '')+'</url>' for url,date in entries)+'</urlset>'
    return HttpResponse(xml,content_type='application/xml')
def robots(request):return HttpResponse('User-agent: *\nDisallow: /admin/\nDisallow: /api/\nDisallow: /account/\nDisallow: /setup/\nDisallow: /studio/\nDisallow: /shelf/\nSitemap: '+settings.PUBLIC_BASE_URL.rstrip('/')+'/sitemap.xml\n',content_type='text/plain')
