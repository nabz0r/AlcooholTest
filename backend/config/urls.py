from django.contrib import admin
from django.urls import path, include
urlpatterns=[path('admin/',admin.site.urls),path('api/v1/',include('catalog.urls'))]
admin.site.site_header='Alcooltest · Editorial studio'
admin.site.site_title='Alcooltest Admin'
admin.site.index_title='Catalogue, provenance & operations'
