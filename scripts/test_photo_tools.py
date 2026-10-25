"""Security and publication-boundary checks for photograph tooling."""
import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import urllib.request

import collect_photographs
import fetch_assets


class PhotoToolTests(unittest.TestCase):
    def test_rejects_unreviewed_hosts_and_credentials(self):
        for url in ['http://upload.wikimedia.org/a.jpg', 'https://upload.wikimedia.org.evil.invalid/a.jpg',
                    'https://user:secret@upload.wikimedia.org/a.jpg', 'https://127.0.0.1/a.jpg',
                    'https://upload.wikimedia.org:8443/a.jpg', 'https://upload.wikimedia.org/a.jpg#fragment']:
            with self.subTest(url=url), self.assertRaises(ValueError):
                fetch_assets.approved_url(url)

    def test_exact_s3_dataset_host_is_accepted(self):
        url = 'https://openfoodfacts-images.s3.eu-west-3.amazonaws.com/data/000/004/221/3277/2.jpg'
        self.assertEqual(fetch_assets.approved_url(url), url)

    def test_bad_redirect_is_rejected_before_following(self):
        request = urllib.request.Request('https://upload.wikimedia.org/a.jpg')
        with self.assertRaises(ValueError):
            fetch_assets.ReviewedRedirectHandler().redirect_request(
                request, None, 302, 'Found', {}, 'http://127.0.0.1/private')

    def test_integrity_and_size_mismatch_are_rejected(self):
        record = {'sha256': hashlib.sha256(b'photo').hexdigest(), 'bytes': 5, 'product_slug': 'example'}
        fetch_assets.verify_bytes(b'photo', record)
        with self.assertRaises(ValueError):
            fetch_assets.verify_bytes(b'changed', record)
        with self.assertRaises(ValueError):
            fetch_assets.verify_bytes(b'photo', {**record, 'bytes': 4})
        with mock.patch.object(fetch_assets, 'MAX_BYTES', 4), self.assertRaises(ValueError):
            fetch_assets.verify_bytes(b'photo', record)

    def test_paths_cannot_escape_the_bottle_directory(self):
        for path in ['/bottles/../../settings.py', '/tmp/photo.jpg', '/bottles/name.svg', '/bottles/a b.jpg']:
            with self.subTest(path=path), self.assertRaises(ValueError):
                fetch_assets.asset_path({'file': path})

    def test_provider_payload_cannot_self_publish_or_assign_side(self):
        target = {'product_slug': 'example', 'commons_query': 'example'}
        payload = {'candidates': [{'title': 'A picture', 'view': 'back', 'side': 'back',
                                   'accepted': True, 'local_path': '/bottles/a.jpg'}]}
        result = collect_photographs.normalise(target, payload, collect_photographs.source_query(target))
        self.assertEqual(result['candidates'][0], {
            'title': 'A picture', 'side': 'unreviewed', 'status': 'needs-editorial-review'})

    def test_cache_only_never_uses_the_network(self):
        with tempfile.TemporaryDirectory() as directory, mock.patch('urllib.request.build_opener') as opener:
            result = collect_photographs.collect({'product_slug': 'example', 'commons_query': 'example'},
                                                 Path(directory), cache_only=True)
        opener.assert_not_called()
        self.assertEqual(result['candidates'], [])
        self.assertIn('error', result)


if __name__ == '__main__':
    unittest.main()
