import uuid
from decimal import Decimal
from io import BytesIO
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError
from PIL import Image

class Entity(models.Model):
    id=models.UUIDField(primary_key=True,default=uuid.uuid4,editable=False)
    updated_at=models.DateTimeField(auto_now=True)
    class Meta: abstract=True

class Source(Entity):
    title=models.CharField(max_length=240)
    url=models.URLField(max_length=1000)
    publisher=models.CharField(max_length=160)
    kind=models.CharField(max_length=20,choices=[(x,x.title()) for x in ['manufacturer','research','regulator','secondary']])
    accessed_on=models.DateField()
    license_note=models.TextField(default='Linked reference only; original content retains its rights.')
    def __str__(self): return self.title

class Place(Entity):
    slug=models.SlugField(unique=True)
    name=models.CharField(max_length=120)
    region=models.CharField(max_length=120,blank=True)
    country=models.CharField(max_length=80)
    source=models.ForeignKey(Source,on_delete=models.PROTECT)
    notes=models.TextField(blank=True)
    def __str__(self): return f'{self.name}, {self.country}'

class Brand(Entity):
    slug=models.SlugField(unique=True)
    name=models.CharField(max_length=120)
    country=models.CharField(max_length=80)
    website=models.URLField()
    def __str__(self): return self.name

NAVIGATION_GROUPS=[('floral','Flowers'),('citrus','Citrus'),('herbal','Leaves & herbs'),('spice','Spices & seeds'),('fruit','Fruit & kernels'),('roots','Roots'),('grain','Grains')]

class Ingredient(Entity):
    plant_part=models.CharField(max_length=120,blank=True,default='')
    sensory_role=models.TextField(blank=True,default='')
    preparation=models.TextField(blank=True,default='')
    technical_notes=models.TextField(blank=True,default='')
    profile_source=models.ForeignKey(Source,on_delete=models.PROTECT,null=True,blank=True,related_name='ingredient_profiles')

    navigation_group=models.CharField(max_length=16,choices=[('','Unclassified')]+NAVIGATION_GROUPS,blank=True,default='',db_index=True)
    slug=models.SlugField(unique=True)
    name=models.CharField(max_length=120)
    scientific_name=models.CharField(max_length=160,blank=True)
    family=models.CharField(max_length=60,default='botanical')
    notes=models.TextField(blank=True)
    def __str__(self): return self.name

class Compound(Entity):
    slug=models.SlugField(unique=True)
    name=models.CharField(max_length=120)
    cas=models.CharField(max_length=30,blank=True)
    notes=models.TextField(blank=True)
    def __str__(self): return self.name

class IngredientCompound(Entity):
    ingredient=models.ForeignKey(Ingredient,on_delete=models.CASCADE)
    compound=models.ForeignKey(Compound,on_delete=models.CASCADE)
    source=models.ForeignKey(Source,on_delete=models.PROTECT)
    notes=models.TextField(default='Possible constituent of the plant; not a measurement in a beverage.')
    class Meta: constraints=[models.UniqueConstraint(fields=['ingredient','compound'],name='unique_ingredient_compound')]

class Product(Entity):
    slug=models.SlugField(unique=True)
    merged_into=models.ForeignKey('self',on_delete=models.PROTECT,null=True,blank=True,related_name='merged_occurrences',help_text='Archived duplicate retained for traceability. Use the merge tool.')
    history=models.TextField(blank=True,help_text='Original, source-linked cultural and historical summary.')
    history_source=models.ForeignKey(Source,on_delete=models.PROTECT,null=True,blank=True,related_name='product_histories')
    edition_of=models.ForeignKey('self',on_delete=models.PROTECT,null=True,blank=True,related_name='editions',help_text='Canonical product family. Use variants for market, size or seller occurrences; editions only for genuinely distinct releases.')
    brand=models.ForeignKey(Brand,on_delete=models.PROTECT,related_name='products')
    place=models.ForeignKey(Place,on_delete=models.PROTECT,null=True,blank=True,related_name='products')
    name=models.CharField(max_length=160)
    category=models.CharField(max_length=40,default='Gin',db_index=True)
    description=models.TextField()
    disclosure=models.CharField(max_length=20,choices=[('partial','Partial disclosure'),('complete','Named ingredients disclosed'),('unknown','Unknown')],default='partial')
    status=models.CharField(max_length=20,choices=[('draft','Draft'),('published','Published'),('archived','Archived')],default='draft',db_index=True)
    color=models.CharField(max_length=7,default='#654026',validators=[RegexValidator(r'^#[0-9a-fA-F]{6}$')])
    shape=models.CharField(max_length=12,choices=[('round','Round'),('square','Square'),('hex','Hexagonal')],default='round')
    photo=models.ImageField(upload_to='bottles/%Y/%m/',blank=True)
    photo_credit=models.CharField(max_length=240,blank=True)
    photo_license=models.CharField(max_length=160,blank=True)
    class Meta: indexes=[models.Index(fields=['status','name','id']),models.Index(fields=['brand','status'])]
    def clean(self):
        if self.edition_of_id:
            if str(self.edition_of_id)==str(self.id): raise ValidationError('A product cannot be its own edition.')
            parent=Product.objects.filter(pk=self.edition_of_id).first()
            if parent and (parent.edition_of_id or str(parent.brand_id)!=str(self.brand_id)): raise ValidationError('Choose a root product of the same brand.')
        if self.photo and (not self.photo_credit or not self.photo_license): raise ValidationError('Photographs require credit and a license or permission statement.')
        if self.photo and not self.photo._committed:
            if self.photo.size>5*1024*1024: raise ValidationError('Image exceeds 5 MiB.')
            try:
                im=Image.open(self.photo)
                if im.format not in ['JPEG','PNG','WEBP'] or im.width*im.height>16000000: raise ValueError()
                im.load(); im.thumbnail((1600,1600)); out=BytesIO(); im.convert('RGB').save(out,format='JPEG',quality=88)
                self.photo=ContentFile(out.getvalue(),name=f'{uuid.uuid4()}.jpg')
            except Exception: raise ValidationError('Use a valid JPEG, PNG or WebP image under 16 megapixels.')
    def __str__(self): return f'{self.brand.name} · {self.name}'

class BottleAsset(Entity):
    pair_key=models.CharField(max_length=100,blank=True,default='',help_text='Shared only by verified views of the same packaging reference.')
    barcode=models.CharField(max_length=14,blank=True,default='',validators=[RegexValidator(r'^\d{8,14}$')])
    view=models.CharField(max_length=12,choices=[('front','Front'),('back','Rear label'),('detail','Detail')],default='front')
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='assets')
    local_path=models.CharField(max_length=180,validators=[RegexValidator(r'^/bottles/[-a-z0-9]+\.(jpg|png|webp)$')])
    source_page=models.URLField(max_length=1000)
    author=models.CharField(max_length=500)
    license=models.CharField(max_length=120)
    license_url=models.URLField(max_length=1000)
    sha256=models.CharField(max_length=64,validators=[RegexValidator(r'^[0-9a-f]{64}$')])
    edition_note=models.TextField()
    class Meta: constraints=[models.UniqueConstraint(fields=['product','local_path'],name='unique_product_asset')]
    def __str__(self): return f'{self.product} — {self.license}'

class Variant(Entity):
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='variants')
    name=models.CharField(max_length=120)
    market=models.CharField(max_length=80)
    abv=models.DecimalField(max_digits=4,decimal_places=1,validators=[MinValueValidator(0),MaxValueValidator(100)])
    volume_ml=models.PositiveIntegerField(validators=[MinValueValidator(1),MaxValueValidator(30000)])
    source=models.ForeignKey(Source,on_delete=models.PROTECT)
    barcode=models.CharField(max_length=14,blank=True,validators=[RegexValidator(r'^\d{8,14}$')])
    class Meta: constraints=[models.UniqueConstraint(fields=['product','name','market','volume_ml'],name='unique_variant')]
    def __str__(self): return f'{self.product} / {self.market} / {self.volume_ml}ml'

class Recipe(Entity):
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='recipes')
    version=models.CharField(max_length=40)
    declared_count=models.PositiveSmallIntegerField(null=True,blank=True)
    process=models.TextField(blank=True)
    source=models.ForeignKey(Source,on_delete=models.PROTECT)
    notes=models.TextField(blank=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['product','version'],name='unique_recipe_version')]
    def __str__(self): return f'{self.product} — {self.version}'

class RecipeIngredient(Entity):
    recipe=models.ForeignKey(Recipe,on_delete=models.CASCADE,related_name='ingredients')
    ingredient=models.ForeignKey(Ingredient,on_delete=models.PROTECT)
    source=models.ForeignKey(Source,on_delete=models.PROTECT)
    certainty=models.CharField(max_length=20,choices=[('confirmed','Manufacturer confirmed'),('reported','Reported'),('hypothesis','Hypothesis')],default='confirmed')
    stage=models.CharField(max_length=60,default='distillation')
    amount=models.DecimalField(max_digits=12,decimal_places=4,null=True,blank=True,validators=[MinValueValidator(0)])
    unit=models.CharField(max_length=20,blank=True)
    notes=models.TextField(blank=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['recipe','ingredient'],name='unique_recipe_ingredient')]

class Study(Entity):
    title=models.CharField(max_length=240)
    compound=models.ForeignKey(Compound,on_delete=models.PROTECT,related_name='studies')
    source=models.ForeignKey(Source,on_delete=models.PROTECT)
    design=models.CharField(max_length=80)
    population=models.CharField(max_length=120)
    finding=models.TextField()
    limitation=models.TextField()
    beverage_evidence=models.BooleanField(default=False,help_text='Only true for research on this beverage, not isolated compounds.')
    class Meta: verbose_name_plural='Studies'
    def __str__(self): return self.title

class Measurement(Entity):
    variant=models.ForeignKey(Variant,on_delete=models.CASCADE,related_name='measurements')
    compound=models.ForeignKey(Compound,on_delete=models.PROTECT)
    value=models.DecimalField(max_digits=16,decimal_places=6,validators=[MinValueValidator(0)])
    unit=models.CharField(max_length=30)
    method=models.CharField(max_length=160)
    batch=models.CharField(max_length=80)
    source=models.ForeignKey(Source,on_delete=models.PROTECT)
    sampled_on=models.DateField(null=True,blank=True)

class Submission(Entity):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    payload=models.JSONField()
    status=models.CharField(max_length=12,choices=[('pending','Pending'),('approved','Approved'),('rejected','Rejected')],default='pending',db_index=True)
    decision_note=models.TextField(blank=True)
    created_at=models.DateTimeField(auto_now_add=True)
    reviewed_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True,related_name='+')

class Review(Entity):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='reviews')
    rating=models.PositiveSmallIntegerField(validators=[MinValueValidator(0),MaxValueValidator(5)])
    text=models.TextField(max_length=2000)
    approved=models.BooleanField(default=False,db_index=True)
    aroma=models.PositiveSmallIntegerField(null=True,blank=True,validators=[MinValueValidator(0),MaxValueValidator(5)])
    taste=models.PositiveSmallIntegerField(null=True,blank=True,validators=[MinValueValidator(0),MaxValueValidator(5)])
    finish=models.PositiveSmallIntegerField(null=True,blank=True,validators=[MinValueValidator(0),MaxValueValidator(5)])
    value=models.PositiveSmallIntegerField(null=True,blank=True,validators=[MinValueValidator(0),MaxValueValidator(5)])
    design=models.PositiveSmallIntegerField(null=True,blank=True,validators=[MinValueValidator(0),MaxValueValidator(5)])
    context=models.CharField(max_length=16,choices=[('neat','Neat'),('ice','On ice'),('tonic','With tonic'),('cocktail','In a cocktail')],blank=True)
    tags=models.JSONField(default=list,blank=True)
    buy_again=models.BooleanField(null=True,blank=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['user','product'],name='unique_user_review')]

class Collection(Entity):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    state=models.CharField(max_length=12,choices=[('wishlist','Wishlist'),('owned','Owned'),('tasted','Tasted')])
    class Meta: constraints=[models.UniqueConstraint(fields=['user','product'],name='unique_collection_item')]

class Job(Entity):
    parameters=models.JSONField(default=dict,blank=True)
    kind=models.CharField(max_length=20,choices=[(x,x.title()) for x in ['json','jsonl','sql','import','discover','research','prices','memento']])
    status=models.CharField(max_length=12,default='queued',db_index=True,choices=[(x,x.title()) for x in ['queued','running','done','failed']])
    created_by=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True)
    created_at=models.DateTimeField(auto_now_add=True)
    started_at=models.DateTimeField(null=True,blank=True)
    finished_at=models.DateTimeField(null=True,blank=True)
    filename=models.CharField(max_length=100,blank=True)
    checksum=models.CharField(max_length=64,blank=True)
    size=models.PositiveBigIntegerField(default=0)
    error=models.TextField(blank=True)
    class Meta: indexes=[models.Index(fields=['status','created_at'])]

class Audit(Entity):
    actor=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True)
    action=models.CharField(max_length=80)
    target=models.CharField(max_length=160)
    detail=models.JSONField(default=dict)
    created_at=models.DateTimeField(auto_now_add=True)

class RateBucket(models.Model):
    key=models.CharField(max_length=100,primary_key=True)
    window=models.BigIntegerField()
    count=models.PositiveIntegerField(default=0)

class Installation(models.Model):
    id=models.PositiveSmallIntegerField(primary_key=True,default=1)
    completed=models.BooleanField(default=False)

class Mechanism(Entity):
    compound=models.ForeignKey(Compound,on_delete=models.CASCADE,related_name='mechanisms')
    target=models.CharField(max_length=120)
    action=models.CharField(max_length=160)
    evidence_context=models.CharField(max_length=160)
    source=models.ForeignKey(Source,on_delete=models.PROTECT)
    limitation=models.TextField()
    def __str__(self): return f'{self.compound}: {self.target}'

class CriticReview(Entity):
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='critic_reviews')
    critic=models.CharField(max_length=160)
    source=models.ForeignKey(Source,on_delete=models.PROTECT)
    summary=models.TextField(help_text='Original factual summary. Do not copy full copyrighted reviews.')
    score=models.DecimalField(max_digits=6,decimal_places=2,null=True,blank=True)
    score_max=models.PositiveSmallIntegerField(null=True,blank=True)
    published_on=models.DateField(null=True,blank=True)
    def __str__(self): return f'{self.critic} — {self.product}'

class Observation(Entity):
    STATES=[(x,x.title()) for x in ['baseline','relaxed','sociable','sleepy','uncomfortable']]
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    from_state=models.CharField(max_length=20,choices=STATES)
    to_state=models.CharField(max_length=20,choices=STATES)
    created_at=models.DateTimeField(auto_now_add=True)
    notes=models.CharField(max_length=500,blank=True)

class DiscoveryCursor(models.Model):
    key=models.CharField(max_length=80,primary_key=True)
    cursor=models.CharField(max_length=100,blank=True)
    exhausted=models.BooleanField(default=False)
    updated_at=models.DateTimeField(auto_now=True)

class DiscoveryCandidate(Entity):
    resolved_product=models.ForeignKey(Product,on_delete=models.PROTECT,null=True,blank=True,related_name="discovery_occurrences",help_text="Link this occurrence to the real existing product before acceptance. A seller, bottle size or market is not a new product.")
    provider=models.CharField(max_length=30)
    external_id=models.CharField(max_length=80)
    label=models.CharField(max_length=240)
    category=models.CharField(max_length=40)
    source_url=models.URLField(max_length=1000)
    payload=models.JSONField()
    status=models.CharField(max_length=20,choices=[('pending','Pending review'),('accepted','Accepted'),('rejected','Rejected')],default='pending',db_index=True)
    image_path=models.CharField(max_length=250,blank=True)
    image_metadata=models.JSONField(default=dict)
    class Meta: constraints=[models.UniqueConstraint(fields=['provider','external_id'],name='unique_external_candidate')]
    def __str__(self): return f'{self.label} ({self.external_id})'

class PriceObservation(Entity):
    basis=models.CharField(max_length=20,default='unspecified',choices=[('unspecified','Unspecified price basis'),('retail_offer','Retail offer'),('archive_capture','Archived retail offer'),('launch_msrp','Manufacturer launch recommendation'),('historical_ad','Published historical price'),('wholesale_list','Published wholesale list')])
    variant=models.ForeignKey(Variant,on_delete=models.CASCADE,related_name='prices')
    observed_on=models.DateField(null=True,blank=True,help_text='Use only an actual source day. Leave empty when the source gives a month.')
    observed_period=models.CharField(max_length=7,blank=True,default='',validators=[RegexValidator(r'^[12]\d{3}-(0[1-9]|1[0-2])$')],help_text='Source month YYYY-MM, without a manufactured day.')
    date_precision=models.CharField(max_length=5,default='day',choices=[('day','Exact source day'),('month','Source month only')])
    amount=models.DecimalField(max_digits=10,decimal_places=2,validators=[MinValueValidator(0)])
    currency=models.CharField(max_length=3,validators=[RegexValidator(r'^[A-Z]{3}$')])
    country=models.CharField(max_length=80)
    retailer=models.CharField(max_length=160)
    source=models.ForeignKey(Source,on_delete=models.PROTECT)
    tax_included=models.BooleanField(default=None,null=True,blank=True)
    promotion=models.BooleanField(default=None,null=True,blank=True)
    notes=models.TextField(blank=True)
    class Meta:
        indexes=[models.Index(fields=['variant','currency','country','observed_on']),models.Index(fields=['variant','currency','country','observed_period'])]
        constraints=[
            models.UniqueConstraint(fields=['variant','observed_on','retailer','currency','country'],name='unique_price_observation'),
            models.UniqueConstraint(fields=['variant','observed_period','retailer','currency','country'],condition=models.Q(date_precision='month'),name='unique_monthly_price_observation'),
            models.CheckConstraint(condition=(models.Q(date_precision='day',observed_on__isnull=False,observed_period='')|models.Q(date_precision='month',observed_on__isnull=True,observed_period__regex=r'^[12]\d{3}-(0[1-9]|1[0-2])$')),name='valid_price_date_precision'),
        ]
    def clean(self):
        from .price_dates import price_bounds
        try:price_bounds(self)
        except (TypeError,ValueError) as exc:raise ValidationError({'date_precision':str(exc)})

class BottlePhoto(Entity):
    pair_key=models.CharField(max_length=100,blank=True,default='',help_text='Assign in editorial review only after matching the same source packaging reference.')
    barcode=models.CharField(max_length=14,blank=True,default='',validators=[RegexValidator(r'^\d{8,14}$')])
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='community_photos')
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.SET_NULL,null=True,blank=True)
    view=models.CharField(max_length=12,choices=[('front','Front'),('back','Rear label'),('detail','Detail')])
    photo=models.ImageField(upload_to='label-photos/%Y/%m/')
    credit=models.CharField(max_length=240)
    license=models.CharField(max_length=160)
    source_url=models.URLField(max_length=1000)
    caption=models.CharField(max_length=300,blank=True)
    approved=models.BooleanField(default=False,db_index=True)
    def clean(self):
        if self.photo and not self.photo._committed:
            if self.photo.size>5*1024*1024:raise ValidationError('Photograph exceeds 5 MiB.')
            try:
                image=Image.open(self.photo)
                if image.format not in ['JPEG','PNG','WEBP'] or image.width*image.height>16000000:raise ValueError()
                image.load();image.thumbnail((2400,2400));out=BytesIO();image.convert('RGB').save(out,format='JPEG',quality=92)
                self.photo=ContentFile(out.getvalue(),name=f'{uuid.uuid4()}.jpg')
            except Exception:raise ValidationError('Use a valid JPEG, PNG or WebP under 16 megapixels.')

class PriceArchiveTarget(Entity):
    review_rules=models.JSONField(default=dict,blank=True,help_text='Provider-specific review holds, e.g. {"drinkshop":{"blocked_abv":["15"]}}. Clear only after resolving the source conflict.')
    drinkshop_id=models.PositiveIntegerField(null=True,blank=True,validators=[MinValueValidator(1),MaxValueValidator(999999)],help_text='Optional exact historical TheDrinkShop product ID. This provider uses a separate parser and source identity.')
    drinkshop_titles=models.JSONField(default=list,blank=True,help_text='Exact historical primary titles verified for this expression.')
    drinkshop_volume_ml=models.PositiveIntegerField(null=True,blank=True,validators=[MinValueValidator(1),MaxValueValidator(30000)],help_text='Exact reviewed single-bottle row; case and miniature prices are rejected.')
    legacy_url=models.URLField(max_length=1000,blank=True,help_text='Reviewed pre-2007 Actinic category URL; never an arbitrary provider.')
    legacy_ref=models.CharField(max_length=80,blank=True,help_text='Exact reviewed Actinic PROD_REF for this expression.')
    legacy_titles=models.JSONField(default=list,blank=True,help_text='Exact names permitted in this one reviewed catalogue row.')
    legacy_age=models.CharField(max_length=30,blank=True,help_text='Exact age cell, e.g. 12yo; empty for an explicitly unaged row.')
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='price_archive_targets')
    retailer_id=models.PositiveIntegerField(validators=[MinValueValidator(1),MaxValueValidator(999999)],help_text='Verified The Whisky Exchange product ID. Never infer one from a brand.')
    tokens=models.JSONField(help_text='Required words or phrases in the primary product heading, e.g. ["yamazaki", "12"].')
    exclude_tokens=models.JSONField(default=list,blank=True,help_text='Reject headings containing another expression or edition.')
    original_urls=models.JSONField(default=list,blank=True,help_text='Optional verified aliases on the same retailer product ID. Legacy and canonical patterns are always searched.')
    source_url=models.URLField(max_length=1000,help_text='Page used to verify the exact retailer/product identity.')
    enabled=models.BooleanField(default=True,db_index=True)
    notes=models.TextField(blank=True)
    last_checked=models.DateTimeField(null=True,blank=True)
    last_result=models.JSONField(default=dict,blank=True)
    class Meta: constraints=[models.UniqueConstraint(fields=['product','retailer_id'],name='unique_product_archive_target')]
    def clean(self):
        from urllib.parse import urlparse
        from .price_archive import archive_urls
        errors={}
        try:
            if not isinstance(self.review_rules,dict) or set(self.review_rules)-{'drinkshop'}:raise ValueError()
            if 'drinkshop' in self.review_rules:
                rules=self.review_rules['drinkshop']
                if not isinstance(rules,dict) or set(rules)-{'blocked_abv','reason'}:raise ValueError()
                blocked=rules.get('blocked_abv',[])
                if not isinstance(blocked,list) or len(blocked)>20:raise ValueError()
                for value in blocked:
                    number=Decimal(str(value))
                    if isinstance(value,bool) or not number.is_finite() or not 0<=number<=100:raise ValueError()
                reason=rules.get('reason','')
                if not isinstance(reason,str) or len(reason)>1000:raise ValueError()
        except (ValueError,TypeError,ArithmeticError):errors['review_rules']='Use only a drinkshop object with up to 20 finite blocked_abv values from 0 to 100 and an optional reason of at most 1000 characters.'
        for field in ['tokens','exclude_tokens']:
            value=getattr(self,field)
            if not isinstance(value,list) or len(value)>20 or (field=='tokens' and not value) or any(not isinstance(t,str) or not t.strip() or len(t)>80 for t in value):errors[field]='Use a list of up to 20 nonempty words or phrases.'
        if not isinstance(self.original_urls,list) or len(self.original_urls)>2 or any(not isinstance(u,str) or len(u)>1000 for u in self.original_urls):errors['original_urls']='Use up to two reviewed retailer aliases.'
        if not errors:
            try:archive_urls({'retailer_id':self.retailer_id,'original_urls':self.original_urls,**({f:getattr(self,f) for f in ['drinkshop_id','drinkshop_titles','drinkshop_volume_ml']} if self.drinkshop_id else {}),**({f:getattr(self,f) for f in ['legacy_url','legacy_ref','legacy_titles','legacy_age']} if self.legacy_url else {})})
            except (ValueError,TypeError):errors['original_urls']='Aliases must belong to this exact retailer product ID.'
        parsed=urlparse(self.source_url)
        if parsed.scheme!='https' or parsed.hostname not in ['thewhiskyexchange.com','www.thewhiskyexchange.com']:errors['source_url']='Use the verified HTTPS retailer product page.'
        import re
        if not re.match(rf'^/(?:[Pp]/{self.retailer_id}/|[Pp]-{self.retailer_id}\.aspx$)',parsed.path):errors['source_url']='The reviewed page must match this retailer product ID.'
        if self.legacy_url or self.legacy_ref or self.legacy_titles:
            legacy=urlparse(self.legacy_url)
            if legacy.scheme not in ['http','https'] or legacy.hostname not in ['www.thewhiskyexchange.com','thewhiskyexchange.com'] or legacy.query or not re.fullmatch(r'/acatalog/The_Whisky_Exchange__[A-Za-z0-9_]+\.html',legacy.path):errors['legacy_url']='Use a reviewed Actinic category on the fixed retailer host.'
            if not re.fullmatch(r'[A-Za-z]+/[A-Za-z0-9]+',self.legacy_ref):errors['legacy_ref']='Use the exact reviewed product reference.'
            if not isinstance(self.legacy_titles,list) or not self.legacy_titles or len(self.legacy_titles)>5 or any(not isinstance(t,str) or not t.strip() or len(t)>160 for t in self.legacy_titles):errors['legacy_titles']='Use up to five reviewed exact row titles.'
        if self.drinkshop_id or self.drinkshop_titles or self.drinkshop_volume_ml:
            if not self.drinkshop_id:errors['drinkshop_id']='A reviewed provider identifier is required.'
            if not self.drinkshop_volume_ml:errors['drinkshop_volume_ml']='A reviewed single-bottle format is required.'
            if not isinstance(self.drinkshop_titles,list) or not self.drinkshop_titles or len(self.drinkshop_titles)>5 or any(not isinstance(t,str) or not t.strip() or len(t)>160 for t in self.drinkshop_titles):errors['drinkshop_titles']='Use up to five reviewed exact primary titles.'
        if errors:raise ValidationError(errors)
    def as_target(self):
        return {'product':self.product.slug,'retailer_id':self.retailer_id,'tokens':self.tokens,'exclude_tokens':self.exclude_tokens,'original_urls':self.original_urls,'review_rules':self.review_rules,**({f:getattr(self,f) for f in ['drinkshop_id','drinkshop_titles','drinkshop_volume_ml']} if self.drinkshop_id else {}),**({f:getattr(self,f) for f in ['legacy_url','legacy_ref','legacy_titles','legacy_age']} if self.legacy_url else {})}
    def __str__(self):return f'{self.product} / retailer #{self.retailer_id}'

class ProductResearch(Entity):
    product=models.OneToOneField(Product,on_delete=models.CASCADE,related_name='research_plan')
    first_release_year=models.PositiveSmallIntegerField(null=True,blank=True,validators=[MinValueValidator(1700),MaxValueValidator(2100)],help_text='Expression launch year, not the distillery founding date. Leave unknown without evidence.')
    release_not_before_year=models.PositiveSmallIntegerField(null=True,blank=True,validators=[MinValueValidator(1700),MaxValueValidator(2100)],help_text='Sourced earliest possible year, for example a brand launch. This bound is not an exact expression launch year.')
    release_source_url=models.URLField(max_length=1000,blank=True)
    notes=models.TextField(blank=True,help_text='Research scope, checked sources and unresolved identity/rights/coverage questions.')
    def clean(self):
        if (self.first_release_year or self.release_not_before_year) and not self.release_source_url:raise ValidationError({'release_source_url':'A launch year or earliest possible year requires a source.'})
        if self.first_release_year and self.release_not_before_year and self.first_release_year<self.release_not_before_year:raise ValidationError({'first_release_year':'An expression cannot precede its sourced earliest possible year.'})
    def __str__(self):return str(self.product)

class ExternalPhotoReference(Entity):
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='external_photo_references')
    view=models.CharField(max_length=12,choices=[('front','Front'),('back','Rear label'),('detail','Detail')])
    source_page=models.URLField(max_length=1000)
    image_url=models.URLField(max_length=2000,help_text='Verified source image URL for inspection. Never fetched or mirrored by the public application.')
    publisher=models.CharField(max_length=160)
    credit=models.CharField(max_length=500,blank=True)
    rights_note=models.TextField(help_text='Exact reuse status. A publicly visible image is not automatically licensed for redistribution.')
    edition_note=models.TextField(help_text='What the verified image actually shows: product, side, packaging, format and limitations.')
    verified_on=models.DateField()
    verified=models.BooleanField(default=False,db_index=True,help_text='Only check after visually confirming this expression and side. Public display is an external link, never a locally hosted image.')
    class Meta:constraints=[models.UniqueConstraint(fields=['product','view','image_url'],name='unique_external_photo_reference')]
    def clean(self):
        from urllib.parse import urlparse
        for field in ['source_page','image_url']:
            if urlparse(getattr(self,field)).scheme!='https':raise ValidationError({field:'Use a public HTTPS source reference.'})
        if self.verified and (not self.rights_note.strip() or not self.edition_note.strip()):raise ValidationError('Verified references require rights and packaging notes.')
    def __str__(self):return f'{self.product} — {self.view} at {self.publisher}'


class MarketPriceIndex(Entity):
    """A survey statistic, separate from offers for a particular bottling."""
    slug=models.SlugField(max_length=160,unique=True)
    product=models.ForeignKey(Product,on_delete=models.CASCADE,related_name='market_indexes')
    source=models.ForeignKey(Source,on_delete=models.PROTECT,related_name='market_indexes')
    title=models.CharField(max_length=240)
    currency=models.CharField(max_length=3,validators=[RegexValidator(r'^[A-Z]{3}$')])
    territory=models.CharField(max_length=100)
    statistic=models.CharField(max_length=160,help_text='What is measured, e.g. median of city survey prices; never a particular retailer offer.')
    unit_scope=models.CharField(max_length=300,help_text='Survey unit and specification scope. Do not assert one unchanged ABV across changing definitions.')
    method=models.TextField(help_text='Collection, processing, specification changes and limits, including the secondary/primary-source distinction.')
    notes=models.TextField(blank=True)
    method_source_url=models.URLField(max_length=1000,blank=True,help_text='Optional original survey metadata or dataset reference. This does not claim the raw dataset was downloaded.')
    fact_sha256=models.CharField(max_length=64,blank=True,validators=[RegexValidator(r'^[0-9a-f]{64}$')],help_text='Optional hash of the documented source fact extraction, not of an unavailable original CSV.')
    verified=models.BooleanField(default=False,db_index=True,help_text='Only reviewed series are exposed in the public API and public exports.')
    def __str__(self):return self.title


class MarketPriceIndexPoint(Entity):
    index=models.ForeignKey(MarketPriceIndex,on_delete=models.CASCADE,related_name='points')
    period=models.CharField(max_length=7,validators=[RegexValidator(r'^[12]\d{3}-(0[1-9]|1[0-2])$')],help_text='Actual monthly period YYYY-MM. No day is fabricated.')
    value=models.DecimalField(max_digits=12,decimal_places=2,validators=[MinValueValidator(Decimal('0.01'))])
    class Meta:
        ordering=['period']
        constraints=[
            models.UniqueConstraint(fields=['index','period'],name='unique_market_index_period'),
            models.CheckConstraint(condition=models.Q(value__gt=0),name='positive_market_index_value'),
            models.CheckConstraint(condition=models.Q(period__regex=r'^[12]\d{3}-(0[1-9]|1[0-2])$'),name='valid_market_index_month'),
        ]
    def __str__(self):return f'{self.index}: {self.period} / {self.value}'
