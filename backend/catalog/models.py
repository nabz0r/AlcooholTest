import uuid
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

class Ingredient(Entity):
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
    class Meta: constraints=[models.UniqueConstraint(fields=['user','product'],name='unique_user_review')]

class Collection(Entity):
    user=models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
    product=models.ForeignKey(Product,on_delete=models.CASCADE)
    state=models.CharField(max_length=12,choices=[('wishlist','Wishlist'),('owned','Owned'),('tasted','Tasted')])
    class Meta: constraints=[models.UniqueConstraint(fields=['user','product'],name='unique_collection_item')]

class Job(Entity):
    kind=models.CharField(max_length=20,choices=[(x,x.title()) for x in ['json','jsonl','sql','import','discover','research']])
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
    status=models.CharField(max_length=20,choices=[('pending','Pending review'),('accepted','Accepted as draft'),('rejected','Rejected')],default='pending',db_index=True)
    image_path=models.CharField(max_length=250,blank=True)
    image_metadata=models.JSONField(default=dict)
    class Meta: constraints=[models.UniqueConstraint(fields=['provider','external_id'],name='unique_external_candidate')]
    def __str__(self): return f'{self.label} ({self.external_id})'

class PriceObservation(Entity):
    variant=models.ForeignKey(Variant,on_delete=models.CASCADE,related_name='prices')
    observed_on=models.DateField()
    amount=models.DecimalField(max_digits=10,decimal_places=2,validators=[MinValueValidator(0)])
    currency=models.CharField(max_length=3,validators=[RegexValidator(r'^[A-Z]{3}$')])
    country=models.CharField(max_length=80)
    retailer=models.CharField(max_length=160)
    source=models.ForeignKey(Source,on_delete=models.PROTECT)
    tax_included=models.BooleanField(default=True)
    promotion=models.BooleanField(default=False)
    notes=models.TextField(blank=True)
    class Meta:
        indexes=[models.Index(fields=['variant','currency','country','observed_on'])]
        constraints=[models.UniqueConstraint(fields=['variant','observed_on','retailer','currency','country'],name='unique_price_observation')]
