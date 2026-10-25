from django.urls import path
from . import views as v
from . import memento
urlpatterns=[path('memento',memento.memento_index),path('memento/capsules/<str:digest>',memento.memento_capsule)]
urlpatterns+=[path('discover',v.discover),path('products/<slug:slug>/photos',v.propose_photo),path('ingredients/<slug:slug>',v.ingredient_detail),path('products/<slug:slug>/observations',v.observations),path('health',v.health),path('session',v.session),path('setup',v.setup),path('register',v.register),path('login',v.sign_in),path('logout',v.sign_out),path('products',v.products),path('products/<slug:slug>',v.product),path('products/<slug:slug>/reviews',v.review),path('stats',v.stats),path('evidence',v.evidence),path('submissions',v.submit),path('collection',v.collection),path('operations',v.operations),path('jobs',v.create_job),path('imports',v.import_data),path('jobs/<uuid:job_id>/download',v.download),path('jobs/<uuid:job_id>/manifest',v.download,{'manifest':True}),path('schema',v.schema)]
