#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
if [ ! -f .env ]; then
  umask 077
  python3 - <<'PY'
import secrets
from pathlib import Path
s=Path('.env.example').read_text()
for key in ['SECRET_KEY','POSTGRES_PASSWORD','SETUP_TOKEN']:
    s=s.replace(key+'=\n',key+'='+secrets.token_urlsafe(48)+'\n')
Path('.env').write_text(s)
PY
fi
docker compose up -d --build
printf '\nAlcooltest: http://localhost:8088\nOpen Setup in the interface, then retrieve your local one-time token with scripts/setup-token.sh.\n'
