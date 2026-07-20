import os
import sys
import urllib.parse

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'resources', 'lib'))
from client import RommClient, RommError  # noqa: E402

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
PLUGIN_URL = sys.argv[0]


def L(string_id):
    return ADDON.getLocalizedString(string_id)


def build_url(**kwargs):
    return PLUGIN_URL + '?' + urllib.parse.urlencode(kwargs)


def notify(message, icon=xbmcgui.NOTIFICATION_INFO):
    xbmcgui.Dialog().notification(ADDON.getAddonInfo('name'), message, icon, 4000)


def get_client():
    host = ADDON.getSetting('host').strip()
    if not host:
        notify(L(32021), xbmcgui.NOTIFICATION_WARNING)
        ADDON.openSettings()
        return None
    if not host.startswith('http'):
        host = 'http://' + host
    return RommClient(
        host,
        username=ADDON.getSetting('username'),
        password=ADDON.getSetting('password'),
        token=ADDON.getSetting('token').strip(),
        insecure=ADDON.getSettingBool('insecure'),
    )


def download_dir():
    path = ADDON.getSetting('download_path').strip()
    if not path:
        path = 'special://profile/addon_data/%s/downloads/' % ADDON.getAddonInfo('id')
    resolved = xbmcvfs.translatePath(path)
    if not os.path.isdir(resolved):
        os.makedirs(resolved, exist_ok=True)
    return resolved


def page_size():
    try:
        return max(10, ADDON.getSettingInt('page_size'))
    except Exception:
        return 100


def list_root():
    items = [
        (build_url(action='platforms'), L(32011), 'DefaultAddonGame.png', True),
        (build_url(action='roms', order_by='created_at', order_dir='desc', label=L(32012)), L(32012), 'DefaultRecentlyAddedEpisodes.png', True),
        (build_url(action='search'), L(32013), 'DefaultAddonsSearch.png', True),
        (build_url(action='settings'), L(32014), 'DefaultAddonService.png', False),
    ]
    for url, label, icon, is_folder in items:
        item = xbmcgui.ListItem(label=label)
        item.setArt({'icon': icon})
        xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder=is_folder)
    xbmcplugin.endOfDirectory(HANDLE)


def list_platforms(client):
    try:
        platforms = client.platforms()
    except RommError as e:
        notify(L(32019) % str(e), xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        return
    for p in platforms:
        name = p.get('display_name') or p.get('name') or p.get('slug', '?')
        label = '%s  (%s)' % (name, p.get('rom_count', 0))
        item = xbmcgui.ListItem(label=label)
        item.setArt({'icon': 'DefaultAddonGame.png'})
        url = build_url(action='roms', platform_id=p['id'], label=name)
        xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE)


def list_roms(client, params):
    platform_id = params.get('platform_id')
    search_term = params.get('search_term')
    order_by = params.get('order_by')
    order_dir = params.get('order_dir')
    offset = int(params.get('offset', 0))
    limit = page_size()

    try:
        data = client.roms(platform_id=platform_id, search_term=search_term,
                           limit=limit, offset=offset,
                           order_by=order_by, order_dir=order_dir)
    except RommError as e:
        notify(L(32019) % str(e), xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        return

    items = data.get('items', [])
    total = data.get('total', len(items))
    if not items and offset == 0:
        notify(L(32020))

    for rom in items:
        name = rom.get('name') or rom.get('fs_name_no_tags') or rom.get('fs_name', '?')
        item = xbmcgui.ListItem(label=name)
        cover = client.cover_url(rom)
        if cover:
            item.setArt({'thumb': cover, 'poster': cover, 'icon': 'DefaultAddonGame.png'})
        else:
            item.setArt({'icon': 'DefaultAddonGame.png'})
        try:
            item.setInfo('game', {
                'title': name,
                'platform': rom.get('platform_display_name', ''),
                'overview': rom.get('summary') or '',
            })
        except Exception:
            pass
        url = build_url(action='select', rom_id=rom['id'])
        item.addContextMenuItems([
            (L(32010), 'RunPlugin(%s)' % build_url(action='download', rom_id=rom['id'])),
        ])
        xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder=False)

    if offset + limit < total:
        next_params = {k: v for k, v in params.items() if k != 'offset'}
        next_params['offset'] = offset + limit
        item = xbmcgui.ListItem(label=L(32015))
        item.setArt({'icon': 'DefaultFolder.png'})
        xbmcplugin.addDirectoryItem(HANDLE, build_url(**next_params), item, isFolder=True)

    xbmcplugin.setContent(HANDLE, 'games')
    xbmcplugin.endOfDirectory(HANDLE)


def search(client):
    keyboard = xbmcgui.Dialog().input(L(32018))
    if not keyboard:
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        return
    list_roms(client, {'action': 'roms', 'search_term': keyboard})


def fetch_rom_to_disk(client, rom_id):
    """Download a rom if not already cached locally. Returns local file path."""
    rom = client.rom(rom_id)
    files = rom.get('files') or []
    if len(files) == 1:
        out_name = files[0].get('file_name') or rom.get('fs_name', 'rom.bin')
    else:
        out_name = (rom.get('fs_name') or 'rom') + '.zip'
    dest = os.path.join(download_dir(), out_name)
    if os.path.isfile(dest) and os.path.getsize(dest) > 0:
        return dest

    name = rom.get('name') or rom.get('fs_name', '?')
    dialog = xbmcgui.DialogProgress()
    dialog.create(ADDON.getAddonInfo('name'), L(32016) % name)

    def progress(done, total):
        if total:
            dialog.update(int(done * 100 / total))
        if dialog.iscanceled():
            raise RommError('cancelled')

    try:
        client.download(rom, dest, progress_cb=progress)
    except RommError:
        dialog.close()
        if os.path.isfile(dest):
            os.remove(dest)
        raise
    dialog.close()
    return dest


def select_rom(client, rom_id):
    """Default click action: download (if needed) then launch, or download only."""
    try:
        dest = fetch_rom_to_disk(client, rom_id)
    except RommError as e:
        if str(e) != 'cancelled':
            notify(L(32019) % str(e), xbmcgui.NOTIFICATION_ERROR)
        return
    if ADDON.getSettingInt('on_select') == 1:
        notify(L(32017))
        return
    xbmc.executebuiltin('PlayMedia("%s")' % dest)


def download_rom(client, rom_id):
    try:
        fetch_rom_to_disk(client, rom_id)
        notify(L(32017))
    except RommError as e:
        if str(e) != 'cancelled':
            notify(L(32019) % str(e), xbmcgui.NOTIFICATION_ERROR)


def router(paramstring):
    params = dict(urllib.parse.parse_qsl(paramstring))
    action = params.get('action')

    if action == 'settings':
        ADDON.openSettings()
        return
    if not action:
        list_root()
        return

    client = get_client()
    if client is None:
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        return

    if action == 'platforms':
        list_platforms(client)
    elif action == 'roms':
        list_roms(client, params)
    elif action == 'search':
        search(client)
    elif action == 'select':
        select_rom(client, params['rom_id'])
    elif action == 'download':
        download_rom(client, params['rom_id'])
    else:
        list_root()


if __name__ == '__main__':
    router(sys.argv[2][1:])
