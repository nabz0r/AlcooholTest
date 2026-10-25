"""Reproduce the original curated starter data. No remote scraping or inferred formulas."""
import json, uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
T={k:[] for k in ['sources','places','brands','ingredients','compounds','ingredient_compounds','products','bottle_assets','variants','recipes','recipe_ingredients','studies','measurements','mechanisms','critic_reviews','price_observations']}
def uid(s): return str(uuid.uuid5(uuid.NAMESPACE_URL,'https://alcooltest.local/'+s))
def add(table,key,**kw):
    obj={'id':uid(table+'/'+key),**kw}; T[table].append(obj); return obj['id']
def source(key,title,url,publisher,kind='manufacturer'):
    return add('sources',key,title=title,url=url,publisher=publisher,kind=kind,accessed_on='2026-10-25',license_note='Reference metadata and original summaries only. Linked documents retain their original rights.')
s={}
s['monkey']=source('monkey','Monkey 47 — production and disclosed botanicals','https://monkey47.com/blog/water','Black Forest Distillers')
s['spice']=source('spice','Monkey 47 — spicy botanicals','https://monkey47.com/blog/the-botanicals-part-iv-spicy','Black Forest Distillers')
s['monkey-strength']=source('monkey-strength','Monkey 47 — Schwarzwald Dry Gin specifications','https://www.pernod-ricard.com/en/brands/monkey-47','Pernod Ricard')
s['cut24']=source('cut24','Distiller’s Cut 2024 — Capparis','https://theabsolutcompany.com/media-room/press-release/black-forests-monkey-47-launches-limited-edition-distillers-cut-with-48th-botanical-from-the-black-pearl-of-the-mediterranean/','The Absolut Company')
s['cut25']=source('cut25','Distiller’s Cut 2025 — Fleur de Sel','https://us.monkey47.com/newsletter','Black Forest Distillers')
s['bombay']=source('bombay','Bombay Sapphire — ten botanicals','https://shop.bombaysapphire.com/collections/all-gin/products/bombay-sapphire','Bacardi')
s['hendricks']=source('hendricks','Hendrick’s Original — botanicals and infusions','https://us.hendricksgin.com/hendricks-original/','William Grant & Sons')
s['roku']=source('roku','Roku — Japanese botanicals and market-specific ABV','https://www.suntory.co.jp/wnb/rokugin/lineup.html','Suntory')
s['roku14']=source('roku14','Roku — six Japanese and eight traditional botanicals','https://house.suntory.com/roku-gin/roku-craft-gin','Suntory')
s['tanq']=source('tanq','Tanqueray London Dry — four botanicals','https://www.diageobaracademy.com/en-zz/home/our-brands/tanqueray-london-dry-gin','Diageo')
s['tanq-spec']=source('tanq-spec','Tanqueray 70cl product specification','https://media.thomasridley.co.uk/Products/SPECS/14099.pdf','Thomas Ridley','secondary')
s['botanist']=source('botanist','The Botanist — 22 hand-foraged Islay botanicals','https://www.thebotanist.com/en-us/pages/about','Bruichladdich')
s['botanist-spec']=source('botanist-spec','The Botanist Islay Dry Gin','https://www.thebotanist.com/products/the-botanist-islay-dry-gin','Bruichladdich')
s['nutmeg']=source('nutmeg','NTP — myristicin chemistry and toxicology','https://www.ncbi.nlm.nih.gov/books/NBK556998/','US National Toxicology Program','regulator')
s['metabolites']=source('metabolites','Beyer et al. 2006 — nutmeg metabolites','https://pubmed.ncbi.nlm.nih.gov/16885726/','Therapeutic Drug Monitoring','research')
s['lavender']=source('lavender','Silexan abuse potential randomized trial','https://pmc.ncbi.nlm.nih.gov/articles/PMC7968617/','International Journal of Neuropsychopharmacology','research')
s['melissa']=source('melissa','Kennedy et al. 2004 — acute lemon balm study','https://pubmed.ncbi.nlm.nih.gov/15272110/','Psychosomatic Medicine','research')
s['thujone']=source('thujone','Dettling et al. 2004 — thujone and alcohol','https://pubmed.ncbi.nlm.nih.gov/15536765/','Journal of Studies on Alcohol','research')
s['bcp']=source('bcp','Gertsch et al. 2008 — beta-caryophyllene','https://pubmed.ncbi.nlm.nih.gov/18574142/','PNAS','research')
s['ginchem']=source('ginchem','Einfalt 2020 — volatile compounds in gins','https://www.weinobst.at/dam/jcr%3A4775a082-1c53-4a8f-ab8d-89d1b11c075f/278-2020.pdf','University of Hohenheim','research')
I={}
def ing(name,scientific='',family='botanical'):
    slug=name.lower().replace(' ','-').replace('’','').replace("'",'')
    if name not in I: I[name]=add('ingredients',slug,slug=slug,name=name,scientific_name=scientific,family=family,notes='Species or plant part left unspecified where the cited producer does not identify it.')
    return I[name]
for name,sci,fam in [('Juniper','Juniperus communis','berry'),('Coriander','Coriandrum sativum','seed'),('Nutmeg','Myristica fragrans','spice'),('Lavender','Lavandula angustifolia','flower'),('Lemon balm','Melissa officinalis','herb'),('Sage','','herb'),('Chamomile','','flower'),('Lingonberry','Vaccinium vitis-idaea','berry'),('Capers','Capparis spinosa','bud'),('Sea salt','','mineral')]: ing(name,sci,fam)
brands={}
for key,name,country,url in [('monkey-47','Monkey 47','Germany','https://monkey47.com'),('bombay','Bombay Sapphire','United Kingdom','https://www.bombaysapphire.com'),('hendricks','Hendrick’s','United Kingdom','https://www.hendricksgin.com'),('roku','Roku','Japan','https://house.suntory.com/roku-gin'),('tanqueray','Tanqueray','United Kingdom','https://www.tanqueray.com'),('the-botanist','The Botanist','United Kingdom','https://www.thebotanist.com')]:
    brands[key]=add('brands',key,slug=key,name=name,country=country,website=url)
def product(slug,brand,name,color,shape,desc,disclosure='partial',category='Gin'):
    return add('products',slug,slug=slug,brand_id=brands[brand],name=name,category=category,place_id=None,description=desc,disclosure=disclosure,status='published',color=color,shape=shape,photo_credit='',photo_license='')
def variant(key,p,name,market,abv,ml,src): add('variants',key,product_id=p,name=name,market=market,abv=str(abv),volume_ml=ml,source_id=s[src],barcode='')
def recipe(key,p,count,src,ingredients,process,notes='Proportions and finished-drink compound concentrations are not disclosed.'):
    r=add('recipes',key,product_id=p,version='Public disclosure · 2026-10-25',declared_count=count,process=process,source_id=s[src],notes=notes)
    for name in ingredients:
        specific='spice' if src=='monkey' and name in spices else src
        add('recipe_ingredients',key+'/'+name,recipe_id=r,ingredient_id=ing(name),source_id=s[specific],certainty='confirmed',stage='post-distillation infusion' if name in ['Rose','Cucumber'] else 'distillation',amount=None,unit='',notes='Presence disclosed; quantity unknown.')
    return r
spices=['Cubeb','Cassia bark','Coriander','Grains of paradise','Ambrette seed','Allspice','Cardamom','Clove','Nutmeg','Liquorice']
monkey=['Juniper','Lingonberry','Sloe','Bramble leaf','Angelica','Acacia flower','Chamomile','Sage','Lavender','Honeysuckle','Orris root','Jasmine','Scarlet monarda','Bitter orange','Lemon balm']+spices
p=product('monkey-47-schwarzwald','monkey-47','Schwarzwald Dry Gin','#694024','round','A Black Forest dry gin with 47 declared botanicals. A partial, source-linked ingredient inventory; no reconstructed secret formula.')
variant('monkey-eu',p,'Standard','Europe',47,500,'monkey-strength'); recipe('monkey-original',p,47,'monkey',monkey,'36-hour maceration, distillation and vapour extraction, followed by resting in earthenware vessels.')
for year,extra,src in [(2024,'Capers','cut24'),(2025,'Sea salt','cut25')]:
    p=product(f'monkey-47-cut-{year}','monkey-47',f'Distiller’s Cut {year}', '#543327','round',f'Annual limited edition featuring {extra.lower()}. The additional ingredient is documented separately from the undisclosed base proportions.')
    variant(f'cut-{year}',p,'Annual edition','International',47,500,src)
    recipe(f'cut-{year}',p,48,src,[extra],'Special edition built on the producer’s 47-botanical gin.','Only the additional ingredient is indexed here. Base recipe membership is not silently inherited across editions.')
p=product('bombay-sapphire','bombay','London Dry Gin','#238b9d','square','Vapour-infused gin with ten disclosed botanicals. Strength varies by market.','complete')
variant('bombay-eu',p,'Standard 40%','Europe',40,700,'bombay')
recipe('bombay',p,10,'bombay',['Juniper','Lemon peel','Grains of paradise','Liquorice','Bitter almond','Orris root','Cubeb','Coriander','Cassia bark','Angelica'],'Botanicals held in baskets for vapour infusion.','Named botanical set disclosed; proportions and compound concentrations remain unknown.')
p=product('hendricks-original','hendricks','Original','#34322d','round','Eleven distilled botanicals, followed by rose and cucumber infusions. Infusions are distinguished from the base botanical count.','complete')
variant('hendricks',p,'41.4% edition','Selected international markets',41.4,700,'hendricks')
recipe('hendricks',p,11,'hendricks',['Chamomile','Elderflower','Juniper','Lemon peel','Orange peel','Caraway','Coriander','Cubeb','Angelica','Yarrow root','Orris root','Rose','Cucumber'],'Separate pot-still and Carter-Head distillates are combined, then rose and cucumber are infused.','11 base botanicals plus 2 separately identified infusions. Amounts are unknown.')
p=product('roku-japanese-craft','roku','Japanese Craft Gin','#99b3a4','hex','Six named Japanese botanicals plus eight traditional botanicals. Japanese and export bottlings have different strengths.')
variant('roku-export',p,'Export','Outside Japan',43,700,'roku'); variant('roku-japan',p,'Domestic','Japan',47,700,'roku')
recipe('roku',p,14,'roku14',['Sakura flower','Sakura leaf','Sencha tea','Gyokuro tea','Sansho pepper','Yuzu peel'],'Botanicals harvested in season and distilled according to their characteristics.','Six Japanese botanicals indexed; the eight traditional botanicals are not enumerated by the cited source.')
p=product('tanqueray-london-dry','tanqueray','London Dry','#30735a','round','A disclosed four-botanical recipe. Botanical identity does not reveal proportions or the chemical composition of a finished batch.','complete')
variant('tanqueray',p,'43.1% edition','Selected European markets',43.1,700,'tanq-spec')
recipe('tanqueray',p,4,'tanq',['Juniper','Coriander','Angelica','Liquorice'],'Neutral grain spirit redistilled with four botanicals.')
p=product('the-botanist-islay','the-botanist','Islay Dry Gin','#869c83','round','Islay gin with 22 locally foraged botanicals alongside classic gin ingredients. The number 22 is not represented as its total recipe size.')
variant('botanist',p,'Standard','International',46,700,'botanist-spec')
recipe('botanist',p,31,'botanist-spec',['Apple mint','Chamomile','Creeping thistle','Downy birch','Elder','Gorse','Lemon balm','Hawthorn','Bog myrtle','Sweet cicely','Lady’s bedstraw','Spearmint','Water mint','Meadowsweet','Red clover','Tansy','Mugwort','White clover','Heather','Wood sage','Wild thyme','Juniper'],'Distilled at Bruichladdich, Islay.','22 locally foraged botanicals plus 9 classic gin botanicals. The 22 local ingredients are indexed; the classic nine are not enumerated by this source. Juniper here refers to the local sprig.')
C={}
for key,name,cas,note in [('myristicin','Myristicin','607-91-0','Nutmeg constituent. Finished-beverage concentration unknown; intoxication literature cannot establish an effect from a glass of gin.'),('linalool','Linalool','78-70-6','Aroma compound. Human lavender-oil preparations, animal inhalation studies and beverage exposure are different contexts.'),('thujone','Thujone','','Composition depends on botanical species and chemotype. No Monkey 47 measurement is available.'),('bcp','Beta-caryophyllene','87-44-5','Selective CB2 agonism does not imply THC-like intoxication.'),('melissa-extract','Lemon balm extract','','A botanical preparation, not one isolated molecule. Included to preserve the intervention actually tested.')]:
    C[key]=add('compounds',key,slug=key,name=name,cas=cas,notes=note)
for key,ingredient,src,note in [('myristicin','Nutmeg','nutmeg','Plant constituent only; finished-drink concentration unknown.'),('linalool','Coriander','ginchem','Coriander can contribute linalool; no product-specific measurement.'),('linalool','Lavender','lavender','Lavender preparation contains linalool; no product-specific measurement.'),('melissa-extract','Lemon balm','melissa','Study uses an extract of this plant; do not equate it with a single compound or distillate.')]:
    add('ingredient_compounds',key+'/'+ingredient,ingredient_id=I[ingredient],compound_id=C[key],source_id=s[src],notes=note)
studies=[('metabolism','myristicin','metabolites','Nutmeg metabolite analysis','Human case + animal analytical study','Intoxication case and rat urine','Measured metabolites did not establish the proposed amphetamine derivatives.','Not a gin study; does not quantify exposure from any catalogue product.'),('lavender','linalool','lavender','Lavender oil abuse-potential trial','Randomized double-blind crossover','40 randomized healthy recreational CNS-depressant users','Standardized lavender oil was similar to placebo on drug-liking and did not show sedative effects in this trial.','Oil preparation rather than pure linalool or gin; no alcohol co-administration inference.'),('melissa','melissa-extract','melissa','Acute lemon balm and stress','Randomized placebo-controlled crossover','18 healthy volunteers','A standardized extract increased self-rated calmness and reduced alertness at the higher studied dose.','Small trial of an oral extract; no proof that active constituents transfer to distilled spirits.'),('thujone','thujone','thujone','Thujone with matched alcohol','Controlled crossover','25 enrolled healthy volunteers','High-thujone condition affected attention and temporarily counteracted alcohol-related anxiety reduction.','Not Monkey 47; effects depended on concentration; no evidence of a mushroom-like effect.'),('caryophyllene','bcp','bcp','Beta-caryophyllene receptor study','Cell assays and mouse experiments','Cells and mice','Selective functional CB2 agonism and anti-inflammatory effects were observed.','Preclinical findings; nonpsychotropic CB2 activity is not evidence of THC-like intoxication.')]
for key,c,src,title,design,pop,finding,limit in studies: add('studies',key,title=title,compound_id=C[c],source_id=s[src],design=design,population=pop,finding=finding,limitation=limit,beverage_evidence=False)

# Additional spirit categories: ingredients are disclosed inputs, not reconstructed formulas.
s['bacardi']=source('bacardi','BACARDI Superior — white rum','https://www.bacardi.com/us/en/our-rums/superior-rum/','Bacardi')
s['havana']=source('havana','Havana Club 7 Años — Cuban rum','https://www.pernod-ricard.com/en/brands/havana-club','Pernod Ricard')
s['jack']=source('jack','Old No. 7 — producer fact sheet','https://pressroom.jackdaniels.com/wp-content/uploads/2015/01/Old-No.7-Fact-Sheet.pdf','Jack Daniel Distillery')
s['jameson']=source('jameson','Jameson — Midleton and whiskey production','https://www.pernod-ricard.com/en/brands/jameson','Pernod Ricard')
s['disaronno']=source('disaronno','Disaronno Originale — supplier specifications','https://pim.norex.fi/tmpe/Igqc0v2AGRBNdk/product_100004_en.pdf','Norex / manufacturer product information','secondary')
s['absolut']=source('absolut','Absolut Original — winter wheat and water','https://www.absolut.com/en-us/products/absolut-vodka/','The Absolut Company')
s['campari']=source('campari','Campari — product profile','https://www.camparigroup.com/en/brands/campari','Campari Group')
s['cointreau']=source('cointreau','Cointreau L’Unique — original orange liqueur','https://www.cointreau.com/int/en/products/cointreau-lunique','Cointreau')
for key,name,country,url in [('bacardi','Bacardí','Puerto Rico','https://www.bacardi.com'),('havana-club','Havana Club','Cuba','https://havana-club.com'),('jack-daniels','Jack Daniel’s','United States','https://www.jackdaniels.com'),('jameson','Jameson','Ireland','https://www.jamesonwhiskey.com'),('disaronno','Disaronno','Italy','https://www.disaronno.com'),('absolut','Absolut','Sweden','https://www.absolut.com'),('campari','Campari','Italy','https://www.campari.com'),('cointreau','Cointreau','France','https://www.cointreau.com')]:
    brands[key]=add('brands',key,slug=key,name=name,country=country,website=url)
extra_products=[
('bacardi-carta-blanca','bacardi','Carta Blanca / Superior','Rum','#8aa8a2','round','A filtered white rum. The public product profile is not a complete manufacturing formula.',40,750,'bacardi',[],'US 40% edition; other markets may use different strengths.'),
('havana-club-7','havana-club','7 Años','Rum','#8b3e16','round','Cuban aged rum. Oak-derived aromas are not automatically added ingredients.',40,700,'havana',[],'Production and ageing are documented; a complete formula is not indexed.'),
('jack-daniels-old-no7','jack-daniels','Old No. 7','Whisky','#a64f1c','square','Tennessee whiskey made with corn, rye and malted barley, charcoal mellowed and matured in new charred white oak.',40,750,'jack',['Corn','Rye','Malted barley','Water'],'Grains are fermentation inputs. Maple charcoal and oak are process materials, not declared added botanicals.'),
('jameson-original','jameson','Original','Whisky','#40733c','round','A blend of pot still and grain whiskeys produced in Midleton, County Cork.',40,700,'jameson',['Malted barley','Unmalted barley'],'Only disclosed ingredients are indexed. Grain-whiskey inputs and all blend proportions remain incomplete.'),
('disaronno-originale','disaronno','Originale','Amaretto','#b95a17','square','Italian amaretto-style liqueur from Saronno. An almond-like aroma does not by itself establish almond as an ingredient.',28,700,'disaronno',['Apricot kernel oil'],'Apricot-kernel input is supplier reported; the rest of the secret formula remains undisclosed. This record is not an allergen certificate.'),
('absolut-original','absolut','Original Vodka','Vodka','#a4c4cc','round','Swedish vodka made from winter wheat and local well water. Produced in the Åhus community.',40,750,'absolut',['Winter wheat','Water'],'Disclosed principal inputs; not a complete batch analysis or allergen determination.'),
('campari-bitter','campari','Bitter','Aperitif','#bb2f22','round','Italian bitter aperitif with a proprietary formula. Flavour descriptors do not identify its secret ingredients.',24,700,'campari',[],'Strength varies by market. The 24% edition is represented; the full botanical recipe is unknown.'),
('cointreau-original','cointreau','L’Unique','Liqueur','#ad5926','square','French orange liqueur built around sweet and bitter orange peels.',40,700,'cointreau',['Sweet orange peel','Bitter orange peel'],'Only named orange inputs are indexed; the ingredient set and proportions are incomplete.')]
for slug,brand,name,category,color,shape,desc,abv,ml,src,ingredients,note in extra_products:
    p=product(slug,brand,name,color,shape,desc,category=category)
    variant(slug,p,'Reference edition','US' if ml==750 else 'Selected international markets',abv,ml,src)
    r=recipe(slug,p,None,src,ingredients,'See linked producer or supplier record for disclosed process.',note)
    for row in T['recipe_ingredients']:
        if row['recipe_id']==r:
            row['stage']='fermentation input' if category in ['Rum','Whisky','Vodka'] else 'formulation input'
            if src=='disaronno': row['certainty']='reported'
# Named localities are textual, source-linked areas, not invented GPS coordinates.
places={}
origins=[('black-forest','Black Forest','Baden-Württemberg','Germany','monkey'),('hampshire','Hampshire','England','United Kingdom','bombay'),('girvan','Girvan','Scotland','United Kingdom','hendricks'),('japan','Japan','','Japan','roku'),('scotland','Scotland','','United Kingdom','tanq'),('islay','Islay','Scotland','United Kingdom','botanist-spec'),('puerto-rico','Puerto Rico','','Puerto Rico','bacardi'),('cuba','Cuba','','Cuba','havana'),('lynchburg','Lynchburg','Tennessee','United States','jack'),('midleton','Midleton','County Cork','Ireland','jameson'),('saronno','Saronno','Lombardy','Italy','disaronno'),('ahus','Åhus','Skåne','Sweden','absolut'),('italy','Italy','','Italy','campari'),('angers','Angers','Loire Valley','France','cointreau')]
for key,name,region,country,src in origins: places[key]=add('places',key,slug=key,name=name,region=region,country=country,source_id=s[src],notes='Production locality at the granularity supported by the linked reference. Not a precise distillery geolocation.')
place_by_brand={'monkey-47':'black-forest','bombay':'hampshire','hendricks':'girvan','roku':'japan','tanqueray':'scotland','the-botanist':'islay','bacardi':'puerto-rico','havana-club':'cuba','jack-daniels':'lynchburg','jameson':'midleton','disaronno':'saronno','absolut':'ahus','campari':'italy','cointreau':'angers'}
# Expanded discovery collection. Identity is curated; undisclosed specifications remain absent.
expanded=[
('Suntory','Toki Blended Japanese Whisky','Whisky','Japan','https://house.suntory.com/products'),
('Suntory','Hibiki Japanese Harmony','Whisky','Japan','https://house.suntory.com/products'),
('Suntory','Yamazaki 12 Years Old','Whisky','Japan','https://house.suntory.com/products'),
('Suntory','Hakushu 12 Years Old','Whisky','Japan','https://house.suntory.com/products'),
('Suntory','Chita Single Grain Whisky','Whisky','Japan','https://house.suntory.com/products'),
('Suntory','Ao Blended World Whisky','Whisky','Japan','https://house.suntory.com/products'),
('Suntory','Kakubin Blended Whisky','Whisky','Japan','https://house.suntory.com/products'),
('Suntory','Haku Vodka','Vodka','Japan','https://house.suntory.com/'),
('Beefeater','London Dry Gin','Gin','United Kingdom','https://www.beefeatergin.com/'),
('Plymouth','Original Gin','Gin','United Kingdom','https://www.plymouthgin.com/'),
('KI NO BI','Kyoto Dry Gin','Gin','Japan','https://www.kyotodistillery.jp/en/'),
('Malfy','Originale','Gin','Italy','https://www.malfygin.com/'),
('The Glenlivet','12 Year Old','Whisky','United Kingdom','https://www.theglenlivet.com/'),
('Aberlour','12 Year Old','Whisky','United Kingdom','https://www.aberlour.com/'),
('Chivas Regal','12 Year Old','Whisky','United Kingdom','https://www.chivas.com/'),
('Ballantine’s','Finest','Whisky','United Kingdom','https://www.ballantines.com/'),
('Four Roses','Small Batch Bourbon','Whisky','United States','https://www.fourrosesbourbon.com/'),
('Kahlúa','Original Coffee Liqueur','Liqueur','Mexico','https://www.kahlua.com/'),
('Malibu','Original','Liqueur','Barbados','https://www.malibudrinks.com/'),
('Altos','Plata','Tequila','Mexico','https://olmecaaltos.com/'),
('Del Maguey','Vida Clásico','Mezcal','Mexico','https://delmaguey.com/'),
('Citadelle','Original','Gin','France','https://citadellegin.com/'),
('Sipsmith','London Dry Gin','Gin','United Kingdom','https://sipsmith.com/'),
('Gin Mare','Mediterranean Gin','Gin','Spain','https://www.ginmare.com/'),
('Nordés','Atlantic Galician Gin','Gin','Spain','https://nordesgin.com/'),
('Isle of Harris','Gin','Gin','United Kingdom','https://harrisdistillery.com/'),
('Isle of Raasay','Hebridean Gin','Gin','United Kingdom','https://raasaydistillery.com/'),
('Kyrö','Gin','Gin','Finland','https://kyrodistillery.com/'),
('St. George','Terroir Gin','Gin','United States','https://stgeorgespirits.com/'),
('Ferdinand’s','Saar Dry Gin','Gin','Germany','https://www.ferdinandsgin.de/'),
('Christian Drouin','Le Gin','Gin','France','https://www.calvados-drouin.com/'),
('Dingle','Original Gin','Gin','Ireland','https://dingledistillery.ie/'),
('Diplomático','Reserva Exclusiva','Rum','Venezuela','https://rondiplomatico.com/'),
('Mount Gay','Eclipse','Rum','Barbados','https://www.mountgayrum.com/'),
('Appleton Estate','Signature','Rum','Jamaica','https://appletonestate.com/'),
('Don Papa','7 Years Old','Rum','Philippines','https://www.donpaparum.com/'),
('Hennessy','V.S','Cognac','France','https://www.hennessy.com/'),
('Rémy Martin','VSOP','Cognac','France','https://www.remymartin.com/'),
('Chartreuse','Green Chartreuse','Liqueur','France','https://www.chartreuse.fr/'),
('Luxardo','Amaretto di Saschira','Amaretto','Italy','https://www.luxardo.it/')]
import re
for brand,name,category,country,url in expanded:
    key=re.sub('[^a-z0-9]+','-',brand.lower()).strip('-')
    if key not in brands:brands[key]=add('brands',key,slug=key,name=brand,country=country,website=url)
    slug=key+'-'+re.sub('[^a-z0-9]+','-',name.lower()).strip('-')
    src=s['identity-'+slug]=source('identity-'+slug,brand+' — '+name+' official range',url,brand)
    pid=product(slug,key,name,'#92704a','round','A source-linked entry in the '+brand+' range. Bottling specifications and ingredient membership require edition-specific verification.','unknown',category)
    row=T['products'][-1];row['history']='This entry belongs to the '+brand+' portfolio, associated with '+country+'. Consult the official range for the producer’s account of its heritage. Dates, founders and cultural claims are not reconstructed from secondary listings.';row['history_source_id']=src
    recipe(slug,pid,None,'identity-'+slug,[],'No recipe reconstructed from tasting notes or retailer listings.','Recipe membership and proportions have not yet been curated. No botanical is inferred from category or brand identity.')
# Original summaries; the critic retains its own scoring scale.
critic=source('citadelle-critic','Citadelle Gin review','https://theginisin.com/gin-reviews/citadelle-gin/','the GIN is IN','secondary')
add('critic_reviews','citadelle-review',product_id=uid('products/citadelle-original'),critic='the GIN is IN',source_id=critic,summary='The reviewer describes a juniper foundation with citrus, floral aromas and a spice-led finish, and finds that its character stands out more clearly in some mixed drinks than others.',score='3.5',score_max=5,published_on=None)

brands['heering']=add('brands','heering',slug='heering',name='Heering',country='Denmark',website='https://www.heering.com/')
product('heering-cherry-liqueur','heering','Cherry Liqueur','#53251d','round','Cherry liqueur documented here through attributed front and rear packaging photographs. Historical packaging reference; current-market strength and the complete formulation have not been verified.',disclosure='unknown',category='Liqueur')

for row in T['products']:
    brand=next(k for k,v in brands.items() if v==row['brand_id']);row['place_id']=places[place_by_brand[brand]] if brand in place_by_brand else None
# Openly licensed, locally hosted real photographs. Rights are preserved per asset.
assets_path=ROOT/'data/assets.json'
if assets_path.exists():
    for asset in json.loads(assets_path.read_text()):
        p=next((p for p in T['products'] if p['slug']==asset['product_slug']),None)
        if p: add('bottle_assets',p['slug']+('/'+asset['view'] if asset.get('view','front')!='front' else ''),view=asset.get('view','front'),product_id=p['id'],local_path=asset['file'],source_page=asset['source_page'],author=asset['author'][:500],license=asset['license'],license_url=asset['license_url'],sha256=asset['sha256'],edition_note=asset['edition_note'])
# Additional primary research and explicit mechanism assertions.
s['ethanol']=source('ethanol','Lovinger et al. 1989 — ethanol and NMDA current','https://pubmed.ncbi.nlm.nih.gov/2467382/','Science','research')
s['linalool-mice']=source('linalool-mice','Harada et al. 2018 — linalool odour and anxiety','https://pubmed.ncbi.nlm.nih.gov/30405369/','Frontiers in Behavioral Neuroscience','research')
s['odours-human']=source('odours-human','Odour inhalation, anxiety and physiological responses','https://pubmed.ncbi.nlm.nih.gov/39430514/','Primary human inhalation study','research')
s['chamomile-human']=source('chamomile-human','Amsterdam et al. 2009 — chamomile extract trial','https://pubmed.ncbi.nlm.nih.gov/19593179/','Journal of Clinical Psychopharmacology','research')
C['ethanol']=add('compounds','ethanol',slug='ethanol',name='Ethanol',cas='64-17-5',notes='Present in alcoholic bottlings according to their declared ABV. Neural activity depends on exposure and context; the visualisation is not a blood-alcohol or impairment model.')
C['chamomile-extract']=add('compounds','chamomile-extract',slug='chamomile-extract',name='Chamomile extract',cas='',notes='Whole-plant intervention; not a single molecule. Results from an extract cannot be assigned to a distilled beverage.')
add('ingredient_compounds','chamomile-extract/Chamomile',ingredient_id=I['Chamomile'],compound_id=C['chamomile-extract'],source_id=s['chamomile-human'],notes='The trial used a chamomile extract. Transfer of its active constituents to this product is not established.')
for key,c,src,title,design,pop,finding,limit in [
('ethanol-nmda','ethanol','ethanol','Ethanol and NMDA ion currents','Patch-clamp electrophysiology','Cultured hippocampal neurons','Ethanol inhibited NMDA-activated currents in a concentration-dependent manner.','Cellular experiment, not an individualized brain simulation or a product-specific comparison.'),
('linalool-mice','linalool','linalool-mice','Linalool odour and anxiety-like behaviour','Controlled animal experiment','Mice','Odour exposure reduced anxiety-like behaviours; effects required olfaction and were blocked by flumazenil.','Animal inhalation experiment. No gin exposure or human intoxication conclusion.'),
('odours-human','bcp','odours-human','Odour exposure and stress responses','Controlled four-group experiment','48 human participants','Certain odour groups showed changes in anxiety ratings and physiological measures.','Small inhalation study, not drinking, not a demonstration of a cannabinoid high.'),
('chamomile-human','chamomile-extract','chamomile-human','Chamomile extract for generalized anxiety','Randomized double-blind placebo-controlled','57 patients over eight weeks','The trial suggested modest improvement in anxiety scores with oral chamomile extract.','Chronic extract administration; not evidence of acute intoxication or activity in gin.')]:
    add('studies',key,title=title,compound_id=C[c],source_id=s[src],design=design,population=pop,finding=finding,limitation=limit,beverage_evidence=False)
for key,c,target,action,ctx,src,limit in [
('ethanol-nmda','ethanol','NMDA receptor','Inhibition of NMDA-activated ion current','Cultured hippocampal neurons','ethanol','One documented target among many; no regional brain activation or dose-response prediction is visualized.'),
('linalool-gaba','linalool','GABA-A-linked signalling','Odour-mediated anxiolytic pathway; flumazenil-sensitive','Mouse odour experiment','linalool-mice','Not proof of direct receptor binding, human effects or exposure from a bottle.'),
('bcp-cb2','bcp','CB2 receptor','Selective functional agonism','Cell assays and mouse experiments','bcp','CB2 activity is not equivalent to THC-like CB1 intoxication.'),
('thujone-gaba','thujone','GABA-A-related signalling','May oppose some alcohol-related effects at high exposure','Controlled human alcohol/thujone experiment','thujone','No thujone measurement in catalogue bottles; cannot infer a product effect.')]:
    add('mechanisms',key,compound_id=C[c],target=target,action=action,evidence_context=ctx,source_id=s[src],limitation=limit)

# Historical claims remain tied to the producer's own account.
heritage=source('suntory-heritage','Suntory historical timeline','https://house.suntory.com/heritage','The House of Suntory')
for row in T['products']:
    if row['brand_id']==brands.get('suntory'):
        row['history']='Shinjiro Torii founded Torii Shoten in Osaka in 1899. Construction of Yamazaki began in 1923; Hakushu followed in 1973. The house developed several identities around blending, place and Japanese craft: Kakubin appeared in 1937 and Hibiki in 1989. This bottle belongs to that evolving portfolio, rather than representing a separate distillery in every case.'
        row['history_source_id']=heritage
    if row['slug']=='isle-of-harris-gin':
        row['history']='The distillery opened in September 2015 with a community ambition: build lasting employment on Harris. Its own account presents the business as a social distillery, linking a commercial spirit to the survival of island life. That community narrative is part of the product’s cultural identity, not a pharmacological property.'
        row['history_source_id']=source('harris-impact','The Isle of Harris — community impact','https://www.harrisdistillery.com/pages/our-impact','The Isle of Harris Distillery')
    if row['slug']=='kyr-gin':
        row['history']='Kyrö traces its origin to five friends talking about rye whisky in a sauna in 2012. The distillery took shape in an old dairy beside the Kyrönjoki. Its identity connects Finnish rye, local industry and sauna culture; the producer’s story is preserved as an attributed account.'
        row['history_source_id']=source('kyro-story','Kyrö — from the sauna benches','https://kyrodistillery.co.uk/','Kyrö Distillery')

for row in T['products']:
    row.setdefault('history','');row.setdefault('history_source_id',None);row['merged_into_id']=None
    row['edition_of_id']=uid('products/monkey-47-schwarzwald') if row['slug'].startswith('monkey-47-cut-') else None

monkey_history=source('monkey-founder-interview','Alexander Stein — founder interview','https://www.freundevonfreunden.com/food/after-the-gin-flood-how-alexander-stein-turned-monkey-47-into-a-long-running-hit/','Freunde von Freunden — interview with Alexander Stein','secondary')
for row in T['products']:
    if row['slug']=='monkey-47-schwarzwald':
        row['history']='In a published founder interview, Alexander Stein places the start of the project in 2008, before the scale of the gin revival was apparent. His account emphasizes making a distinctive product with limited initial resources rather than treating craft as a new invention. The gin connects the Black Forest’s fruit-distilling culture and botanical landscape with the British gin tradition. Its apothecary-style bottle and numbered identity make that mixture of laboratory, landscape and storytelling visible. The 47-botanical declaration is preserved as a producer claim; it does not reveal the proportions or establish a special neurological effect.'
        row['history_source_id']=monkey_history

# First dated Luxembourg price snapshots; no backfilled or interpolated history.
for key,variant_key,amount,retailer,url in [
('bombay-lu-20261025','bombay-eu','16.95','Centre Bohey via Letzshop','https://letzshop.lu/en/products/bombay-sapphire-e1ec1f'),
('monkey-lu-20261025','monkey-eu','47.28','Munhowen Drinx Sandweiler via Letzshop','https://letzshop.lu/de/sandweiler/products/monkey-47-schwarzwald-dry-gin-47-9517f0')]:
    src=source('price-'+key,retailer+' dated reference',url,retailer,'secondary')
    add('price_observations',key,variant_id=uid('variants/'+variant_key),observed_on='2026-10-25',amount=amount,currency='EUR',country='Luxembourg',retailer=retailer,source_id=src,tax_included=True,promotion=False,notes='Price displayed in the source consulted on this date. Not a checkout guarantee or historical reconstruction; shipping excluded.')

for perspective in json.loads((ROOT/'data/navigation/critic-perspectives.json').read_text()):
    ref=source(perspective['key'],perspective['title'],perspective['url'],perspective['critic'],'secondary')
    add('critic_reviews',perspective['key'],product_id=uid('products/'+perspective['product']),critic=perspective['critic'],source_id=ref,summary=perspective['summary'],score=perspective['score'],score_max=perspective['score_max'],published_on=perspective['published_on'])

navigation=json.loads((ROOT/'data/navigation/ingredient-groups.json').read_text())
for row in T['ingredients']:row['navigation_group']=next((key for key,slugs in navigation.items() if row['slug'] in slugs),'')

doc={'schema_version':'1.0','generated_at':'2026-10-25T00:00:00Z','tables':T}
(ROOT/'data/catalog/seed.json').write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n')
print({k:len(v) for k,v in T.items()})
