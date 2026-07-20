"""Thin client for the RomM REST API (https://docs.romm.app).

Auth: HTTP Basic (username/password) or a long-lived client API token
("rmm_" + 64 hex chars, generated in RomM under Administration -> Client API
Tokens) sent as a Bearer token. Endpoints used:

    GET /api/platforms                          -> [PlatformSchema, ...]
    GET /api/roms?...                           -> {"items": [...], "total": n, "limit": l, "offset": o}
    GET /api/roms/{id}                          -> RomSchema (includes files[])
    GET /api/roms/{id}/content/{file_name}      -> raw file (single-file rom) or zip (multi-part)

Uses only the Python stdlib so the addon has no dependency beyond xbmc.python.
"""
import base64
import json
import ssl
import urllib.error
import urllib.parse
import urllib.request

CHUNK_SIZE = 1024 * 1024


class RommError(Exception):
    pass


class RommClient:
    def __init__(self, base_url, username='', password='', token='', insecure=False):
        self.base_url = base_url.rstrip('/')
        self.username = username
        self.password = password
        self.token = token
        self.context = None
        if insecure:
            self.context = ssl.create_default_context()
            self.context.check_hostname = False
            self.context.verify_mode = ssl.CERT_NONE

    def auth_header(self):
        if self.token:
            return 'Bearer %s' % self.token
        creds = '%s:%s' % (self.username, self.password)
        return 'Basic %s' % base64.b64encode(creds.encode('utf-8')).decode('ascii')

    def _open(self, path, params=None):
        url = self.base_url + path
        if params:
            url += '?' + urllib.parse.urlencode(params, doseq=True)
        req = urllib.request.Request(url, headers={
            'Authorization': self.auth_header(),
            'User-Agent': 'plugin.program.romm',
        })
        try:
            return urllib.request.urlopen(req, timeout=30, context=self.context)
        except urllib.error.HTTPError as e:
            raise RommError('HTTP %s on %s: %s' % (e.code, path, e.reason))
        except urllib.error.URLError as e:
            raise RommError('Cannot reach %s: %s' % (self.base_url, e.reason))

    def get_json(self, path, params=None):
        with self._open(path, params) as resp:
            return json.loads(resp.read().decode('utf-8'))

    def platforms(self):
        """Platforms that actually contain roms, sorted by display name."""
        platforms = self.get_json('/api/platforms')
        platforms = [p for p in platforms if p.get('rom_count', 0) > 0]
        platforms.sort(key=lambda p: (p.get('display_name') or p.get('name') or '').lower())
        return platforms

    def roms(self, platform_id=None, search_term=None, limit=100, offset=0,
             order_by=None, order_dir=None):
        params = {
            'limit': limit,
            'offset': offset,
            # skip the heavyweight index/filter payloads meant for the web UI
            'with_char_index': 'false',
            'with_filter_values': 'false',
            'with_rom_id_index': 'false',
        }
        if platform_id is not None:
            params['platform_ids'] = platform_id
        if search_term:
            params['search_term'] = search_term
        if order_by:
            params['order_by'] = order_by
        if order_dir:
            params['order_dir'] = order_dir
        data = self.get_json('/api/roms', params)
        if isinstance(data, list):  # older servers returned a plain list
            return {'items': data, 'total': len(data), 'limit': limit, 'offset': offset}
        return data

    def rom(self, rom_id):
        return self.get_json('/api/roms/%s' % rom_id)

    def cover_url(self, rom):
        """Best cover image URL for a rom, with auth header piped for Kodi.

        Prefers the metadata-provider URL (public CDN, no auth needed); falls
        back to the server-local resource, which needs our auth header - Kodi
        supports `url|Header=Value` suffixes on image paths for that.
        """
        url = rom.get('url_cover')
        if url and url.startswith('http'):
            return url
        path = rom.get('path_cover_large') or rom.get('path_cover_small')
        if not path:
            return ''
        local = '%s/assets/romm/resources/%s' % (self.base_url, path.lstrip('/'))
        return local + '|' + urllib.parse.urlencode({'Authorization': self.auth_header()})

    def download(self, rom, dest_path, progress_cb=None):
        """Stream a rom's content to dest_path.

        Server behavior: single-file roms come back as the raw file; multi-part
        roms come back as a zip (with .m3u where applicable).
        """
        fs_name = rom.get('fs_name', '')
        path = '/api/roms/%s/content/%s' % (rom['id'], urllib.parse.quote(fs_name))
        with self._open(path) as resp:
            total = int(resp.headers.get('Content-Length') or 0)
            done = 0
            with open(dest_path, 'wb') as out:
                while True:
                    chunk = resp.read(CHUNK_SIZE)
                    if not chunk:
                        break
                    out.write(chunk)
                    done += len(chunk)
                    if progress_cb:
                        progress_cb(done, total)
        return dest_path
