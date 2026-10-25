"""Re-fetch pinned licensed source thumbnails, verifying integrity before replacing assets."""
import json,hashlib,urllib.request,urllib.parse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for asset in json.loads((ROOT/'data/assets.json').read_text()):
    url=asset['download_url']
    if urllib.parse.urlparse(url).hostname not in {'upload.wikimedia.org','thumb.wikimedia.org'}:raise ValueError('Unapproved asset provider')
    req=urllib.request.Request(url,headers={'User-Agent':'Alcooltest/1.0 (https://github.com/nabz0r/AlcooholTest)'})
    with urllib.request.urlopen(req,timeout=45) as response:
        if urllib.parse.urlparse(response.url).hostname not in {'upload.wikimedia.org','thumb.wikimedia.org'}:raise ValueError('Unexpected redirect')
        data=response.read(8*1024*1024+1)
    if hashlib.sha256(data).hexdigest()!=asset['sha256']:raise ValueError('Remote bytes changed; review rights and regenerate the manifest: '+asset['product_slug'])
    path=ROOT/'frontend/public'/asset['file'].lstrip('/');path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
    print(asset['product_slug'],len(data),'verified')
