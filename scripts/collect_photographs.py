"""Collect bounded Wikimedia photograph leads without publishing image assets.

Source side, exact expression and reuse rights still require editorial review.
Pinned/accepted files are restored separately by fetch_assets.py.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import html
import json
from pathlib import Path
import re
import time
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
ENDPOINT = 'https://commons.wikimedia.org/w/api.php'
MAX_RESPONSE_BYTES = 4 * 1024 * 1024
USER_AGENT = 'Alcooltest/1.0 (https://github.com/nabz0r/AlcooholTest) photograph provenance research'


class CommonsRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, newurl):
        parsed = urllib.parse.urlsplit(newurl)
        if parsed.scheme != 'https' or parsed.hostname != 'commons.wikimedia.org' or parsed.username or parsed.password:
            raise ValueError('Unexpected metadata provider redirect')
        return super().redirect_request(request, response, code, message, headers, newurl)


def source_query(target):
    return ENDPOINT + '?' + urllib.parse.urlencode({
        'action': 'query', 'format': 'json', 'generator': 'search',
        'gsrsearch': target['commons_query'], 'gsrnamespace': 6, 'gsrlimit': 15,
        'prop': 'imageinfo', 'iiprop': 'url|extmetadata|size', 'iiurlwidth': 640,
    })


def normalise(target, payload, request_url):
    # Cached normalized metadata and the native MediaWiki response are accepted.
    # Neither format is permitted to set an accepted asset or a photograph side.
    if 'candidates' in payload:
        candidates = payload['candidates']
    else:
        candidates = []
        for page in payload.get('query', {}).get('pages', {}).values():
            info = page.get('imageinfo', [{}])[0]
            metadata = info.get('extmetadata', {})
            def plain(key):
                value = metadata.get(key, {}).get('value', '')
                return re.sub(r'<[^>]*>', '', html.unescape(value)).strip()[:2000]
            candidates.append({
                'title': page.get('title', ''), 'pageid': page.get('pageid'),
                'source_page': info.get('descriptionurl', ''),
                'download_url': info.get('thumburl', info.get('url', '')),
                'author': plain('Artist'), 'license': plain('LicenseShortName'),
                'license_url': plain('LicenseUrl'),
                'width': info.get('width'), 'height': info.get('height'),
            })
    allowed = {'title', 'pageid', 'source_page', 'download_url', 'author', 'license', 'license_url', 'width', 'height'}
    reviewed = [{**{k: v for k, v in candidate.items() if k in allowed},
                 'side': 'unreviewed', 'status': 'needs-editorial-review'}
                for candidate in candidates[:15]]
    return {
        'product_slug': target['product_slug'], 'query': target['commons_query'],
        'request_url': request_url, 'retrieved_on': datetime.now(timezone.utc).date().isoformat(),
        'provider': 'wikimedia', 'candidates': reviewed,
    }


def collect(target, cache_dir, cache_only=False, refresh=False):
    slug = target['product_slug']
    if not re.fullmatch(r'[-a-z0-9]{1,120}', slug):
        raise ValueError('Invalid canonical product slug')
    request_url = source_query(target)
    cache_file = cache_dir / (slug + '.json')
    if cache_file.exists() and not refresh:
        payload = json.loads(cache_file.read_text())
        if payload.get('request_url') != request_url:
            raise ValueError('Cached query differs from the reviewed target; refresh explicitly')
        result = normalise(target, payload, request_url)
        result['retrieved_on'] = payload.get('retrieved_on', result['retrieved_on'])
        result['cache_hit'] = True
        return result
    if cache_only:
        return {'product_slug': slug, 'request_url': request_url, 'provider': 'wikimedia',
                'error': 'No cached response for this reviewed query', 'candidates': []}
    request = urllib.request.Request(request_url, headers={'User-Agent': USER_AGENT})
    opener = urllib.request.build_opener(CommonsRedirectHandler())
    with opener.open(request, timeout=35) as response:
        raw = response.read(MAX_RESPONSE_BYTES + 1)
    if len(raw) > MAX_RESPONSE_BYTES:
        raise ValueError('Metadata response exceeds the 4 MiB limit')
    payload = json.loads(raw)
    if payload.get('error'):
        raise ValueError('MediaWiki returned an API error')
    result = normalise(target, payload, request_url)
    result['response_sha256'] = hashlib.sha256(raw).hexdigest()
    cache_dir.mkdir(parents=True, exist_ok=True)
    temporary = cache_file.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n')
    temporary.replace(cache_file)
    result['cache_hit'] = False
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--product', help='One canonical product slug from the reviewed target registry.')
    group.add_argument('--all', action='store_true', help='Collect at most55 canonical target searches, paced sequentially.')
    parser.add_argument('--cache-dir', type=Path, default=ROOT / 'work/photo-discovery')
    parser.add_argument('--cache-only', action='store_true')
    parser.add_argument('--refresh', action='store_true')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.cache_only and args.refresh:
        parser.error('--cache-only and --refresh cannot be combined')
    targets = json.loads((ROOT / 'data/photography/targets.json').read_text())['targets']
    selected = targets[:55] if args.all else [target for target in targets if target['product_slug'] == args.product]
    if not selected:
        parser.error('Unknown canonical product slug')
    results = []
    for target in selected:
        try:
            result = collect(target, args.cache_dir, args.cache_only, args.refresh)
        except (OSError, ValueError, KeyError) as error:
            result = {'product_slug': target['product_slug'], 'provider': 'wikimedia',
                      'request_url': source_query(target), 'error': str(error), 'candidates': []}
        results.append(result)
        if not args.cache_only and not result.get('cache_hit', False):
            time.sleep(1.05)
    output = {
        'schema_version': '1.0', 'generated_at': datetime.now(timezone.utc).isoformat(),
        'publication_status': 'unreviewed-metadata-only',
        'counts': {'products': len(results), 'candidates': sum(len(result['candidates']) for result in results),
                   'errors': sum(bool(result.get('error')) for result in results)},
        'results': results,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(output, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(output['counts']))


if __name__ == '__main__':
    main()
