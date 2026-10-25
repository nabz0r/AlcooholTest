"""Per-record editorial checks; missing evidence is never a completed dossier."""
from . import models as m

CHECKS = [('history','Attributed history'),('bottling','Sourced bottling'),('production','Production account'),('ingredients','Named inputs'),('criticism','Attributed criticism'),('front','Real front photograph'),('back','Real rear photograph'),('prices','Dated price evidence')]

def dossier_rows(queryset=None):
    qs=queryset if queryset is not None else m.Product.objects.filter(status='published',edition_of__isnull=True,merged_into__isnull=True)
    qs=qs.select_related('brand','history_source').prefetch_related('variants__prices','recipes__ingredients','critic_reviews','assets','community_photos')
    rows=[]
    for p in qs.order_by('brand__name','name'):
        recipes=list(p.recipes.all()); assets=list(p.assets.all());photos=[x for x in p.community_photos.all() if x.approved]
        checks={'history':bool(p.history.strip() and p.history_source_id),'bottling':bool(p.variants.all()),'production':any(r.process.strip() and r.source_id for r in recipes),'ingredients':any(r.ingredients.all() for r in recipes),'criticism':any(c.summary.strip() and c.source_id for c in p.critic_reviews.all()),'front':bool(p.photo) or any(a.view=='front' for a in assets+photos),'back':any(a.view=='back' for a in assets+photos),'prices':any(v.prices.all() for v in p.variants.all())}
        rows.append({'product':p,'checks':[{'key':key,'label':label,'present':checks[key]} for key,label in CHECKS],'missing':[key for key,_ in CHECKS if not checks[key]],'documented':sum(checks.values()),'complete':all(checks.values()),'disclosure':p.get_disclosure_display()})
    return rows
