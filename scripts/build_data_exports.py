"""Build distribution JSONL and integrity manifest from the curated JSON."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]/'data/catalog'
doc=json.loads((ROOT/'seed.json').read_text())
with (ROOT/'catalog.jsonl').open('w') as stream:
    stream.write(json.dumps({'type':'manifest','schema_version':doc['schema_version'],'generated_at':doc['generated_at']})+'\n')
    for table,rows in doc['tables'].items():
        for row in rows: stream.write(json.dumps({'table':table,'record':row},ensure_ascii=False)+'\n')
manifest={'schema_version':doc['schema_version'],'generated_at':doc['generated_at'],'counts':{k:len(v) for k,v in doc['tables'].items()},'files':{}}
for name in ['seed.json','schema.json','catalog.jsonl']:
    data=(ROOT/name).read_bytes();manifest['files'][name]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
(ROOT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
