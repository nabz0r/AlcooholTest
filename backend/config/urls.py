from django.contrib import admin
from django.urls import path, include
from catalog import seo
urlpatterns=[path('',seo.page),path('sitemap.xml',seo.sitemap),path('robots.txt',seo.robots),path('spirits/<slug:slug>/',seo.page),path('admin/',admin.site.urls),path('api/v1/',include('catalog.urls')),path('<slug:section>/',seo.page)]
admin.site.site_header='Alcooltest · Editorial studio'
admin.site.site_title='Alcooltest Admin'
admin.site.index_title='Catalogue, provenance & operations'
