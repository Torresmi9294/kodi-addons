import json
import os
import random
import shutil
import subprocess
import sys
import time
import urllib.parse
import zipfile

import xbmc
import xbmcaddon
import xbmcgui
import xbmcplugin
import xbmcvfs

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'resources', 'lib'))
from client import RommClient, RommError  # noqa: E402
from gameinfo import GameInfoDialog  # noqa: E402

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
PLUGIN_URL = sys.argv[0]

CONTENT_TYPES = {0: 'games', 1: 'movies', 2: 'tvshows'}
PLATFORM_ART_DIR = os.path.join(ADDON.getAddonInfo('path'), 'resources', 'platforms')


def L(string_id):
    return ADDON.getLocalizedString(string_id)


def build_url(**kwargs):
    return PLUGIN_URL + '?' + urllib.parse.urlencode(kwargs)


def notify(message, icon=xbmcgui.NOTIFICATION_INFO):
    xbmcgui.Dialog().notification(ADDON.getAddonInfo('name'), message, icon, 4000)


def profile_path(filename):
    profile = xbmcvfs.translatePath(ADDON.getAddonInfo('profile'))
    if not os.path.isdir(profile):
        os.makedirs(profile, exist_ok=True)
    return os.path.join(profile, filename)


def load_json(filename, default):
    path = profile_path(filename)
    if os.path.isfile(path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            pass
    return default


def save_json(filename, data):
    with open(profile_path(filename), 'w', encoding='utf-8') as f:
        json.dump(data, f)


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


def download_dir(rom=None):
    path = ADDON.getSetting('download_path').strip()
    if not path:
        path = 'special://profile/addon_data/%s/downloads/' % ADDON.getAddonInfo('id')
    resolved = xbmcvfs.translatePath(path)
    if rom is not None and ADDON.getSettingBool('organize_by_platform'):
        slug = rom.get('platform_fs_slug') or rom.get('platform_slug') or ''
        if slug:
            resolved = os.path.join(resolved, slug)
    if not os.path.isdir(resolved):
        os.makedirs(resolved, exist_ok=True)
    return resolved


def page_size():
    try:
        return max(10, ADDON.getSettingInt('page_size'))
    except Exception:
        return 100


def local_platform_art(platform):
    """Bundled-in-the-addon artwork for a platform, if present.

    Ships offline: these files are part of the addon package (zipped and
    installed with it), so they're available even if RomM is unreachable.
    Checked before any network art - see resources/platforms/README.md for
    the naming convention. Returns '' if nothing local matches.
    """
    candidates = [platform.get('fs_slug'), platform.get('slug')]
    for name in candidates:
        if not name:
            continue
        for ext in ('png', 'jpg'):
            path = os.path.join(PLATFORM_ART_DIR, '%s.%s' % (name.lower(), ext))
            if os.path.isfile(path):
                return path
    return ''


def rom_label(rom):
    if ADDON.getSettingBool('clean_titles'):
        return rom.get('name') or rom.get('fs_name_no_tags') or rom.get('fs_name', '?')
    return rom.get('fs_name') or rom.get('name', '?')


# ---------------------------------------------------------------- directories

def list_root():
    entries = [(build_url(action='platforms'), L(32011), 'DefaultAddonGame.png')]
    if ADDON.getSettingBool('show_favorites'):
        entries.append((build_url(action='roms', favorite=1, label=L(32022)), L(32022), 'DefaultFavourites.png'))
    if ADDON.getSettingBool('show_collections'):
        entries.append((build_url(action='collections'), L(32023), 'DefaultPlaylist.png'))
    if ADDON.getSettingBool('show_recent'):
        entries.append((build_url(action='roms', order_by='created_at', order_dir='desc', label=L(32012)), L(32012), 'DefaultRecentlyAddedEpisodes.png'))
    if ADDON.getSettingBool('show_lastplayed'):
        entries.append((build_url(action='lastplayed'), L(32024), 'DefaultYear.png'))
    if ADDON.getSettingBool('show_random'):
        entries.append((build_url(action='random'), L(32025), 'DefaultAddonsUpdates.png'))
    entries.append((build_url(action='search'), L(32013), 'DefaultAddonsSearch.png'))
    entries.append((build_url(action='tools'), L(32026), 'DefaultAddonProgram.png'))
    entries.append((build_url(action='settings'), L(32014), 'DefaultAddonService.png'))

    for url, label, icon in entries:
        item = xbmcgui.ListItem(label=label)
        item.setArt({'icon': icon})
        is_folder = 'action=settings' not in url
        xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder=is_folder)
    xbmcplugin.endOfDirectory(HANDLE)


def list_platforms(client):
    try:
        platforms = client.platforms()
    except RommError as e:
        notify(L(32019) % str(e), xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        return
    hidden = load_json('hidden.json', [])
    for p in platforms:
        if p['id'] in hidden:
            continue
        name = p.get('display_name') or p.get('name') or p.get('slug', '?')
        label = '%s  (%s)' % (name, p.get('rom_count', 0))
        item = xbmcgui.ListItem(label=label)
        logo = local_platform_art(p) or client.platform_logo_url(p)
        if logo:
            item.setArt({'thumb': logo, 'poster': logo, 'icon': logo})
        else:
            item.setArt({'icon': 'DefaultAddonGame.png'})
        item.addContextMenuItems([
            (L(32034), 'RunPlugin(%s)' % build_url(action='hide_platform', platform_id=p['id'])),
            (L(32035), 'RunPlugin(%s)' % build_url(action='choose_core', platform=p.get('fs_slug') or p.get('slug', ''))),
        ])
        url = build_url(action='roms', platform_id=p['id'], label=name)
        xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE)


def list_collections(client):
    try:
        cols = client.collections()
    except RommError as e:
        notify(L(32019) % str(e), xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        return
    for c in cols:
        count = c.get('rom_count')
        label = c.get('name', '?') if count is None else '%s  (%s)' % (c.get('name', '?'), count)
        item = xbmcgui.ListItem(label=label)
        item.setArt({'icon': 'DefaultPlaylist.png'})
        url = build_url(action='roms', collection_id=c['id'], label=c.get('name', ''))
        xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder=True)
    xbmcplugin.endOfDirectory(HANDLE)


def add_rom_item(client, rom):
    name = rom_label(rom)
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
    item.addContextMenuItems([
        (L(32010), 'RunPlugin(%s)' % build_url(action='download', rom_id=rom['id'])),
        (L(32035), 'RunPlugin(%s)' % build_url(action='choose_core', platform=rom.get('platform_fs_slug') or rom.get('platform_slug', ''))),
    ])
    url = build_url(action='select', rom_id=rom['id'])
    xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder=False)


def list_roms(client, params):
    """Fetch every page from RomM internally and hand Kodi one combined,
    unpaginated listing - no "Next page" item, just one long scrollable list
    (Kodi has no true infinite/lazy-loaded scroll for plugin directories;
    this is the practical equivalent)."""
    batch_size = page_size()
    items = []
    try:
        offset = 0
        while True:
            data = client.roms(
                platform_id=params.get('platform_id'),
                search_term=params.get('search_term'),
                collection_id=params.get('collection_id'),
                favorite=True if params.get('favorite') else None,
                limit=batch_size, offset=offset,
                order_by=params.get('order_by'),
                order_dir=params.get('order_dir'),
            )
            batch = data.get('items', [])
            items.extend(batch)
            total = data.get('total', len(items))
            offset += batch_size
            if not batch or offset >= total:
                break
    except RommError as e:
        notify(L(32019) % str(e), xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        return

    if not items:
        notify(L(32020))

    for rom in items:
        add_rom_item(client, rom)

    xbmcplugin.setContent(HANDLE, CONTENT_TYPES.get(ADDON.getSettingInt('content_type'), 'games'))
    xbmcplugin.endOfDirectory(HANDLE)


def list_random(client):
    limit = page_size()
    try:
        total = client.roms(limit=1).get('total', 0)
        offset = random.randint(0, max(0, total - limit))
        data = client.roms(limit=limit, offset=offset)
    except RommError as e:
        notify(L(32019) % str(e), xbmcgui.NOTIFICATION_ERROR)
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        return
    items = data.get('items', [])
    random.shuffle(items)
    for rom in items:
        add_rom_item(client, rom)
    xbmcplugin.setContent(HANDLE, CONTENT_TYPES.get(ADDON.getSettingInt('content_type'), 'games'))
    xbmcplugin.endOfDirectory(HANDLE)


def list_lastplayed(client):
    history = load_json('history.json', [])
    for entry in history:
        item = xbmcgui.ListItem(label=entry.get('name', '?'))
        cover = entry.get('cover') or ''
        if cover:
            item.setArt({'thumb': cover, 'poster': cover, 'icon': 'DefaultAddonGame.png'})
        else:
            item.setArt({'icon': 'DefaultAddonGame.png'})
        url = build_url(action='select', rom_id=entry['id'])
        xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder=False)
    xbmcplugin.setContent(HANDLE, CONTENT_TYPES.get(ADDON.getSettingInt('content_type'), 'games'))
    xbmcplugin.endOfDirectory(HANDLE)


def search(client):
    keyboard = xbmcgui.Dialog().input(L(32018))
    if not keyboard:
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        return
    list_roms(client, {'action': 'roms', 'search_term': keyboard})


def list_tools():
    entries = [
        (build_url(action='test'), L(32027), 'DefaultAddonService.png'),
        (build_url(action='stats'), L(32029), 'DefaultSystemInfo.png'),
        (build_url(action='clear_cache'), L(32030), 'DefaultAddonsZip.png'),
        (build_url(action='unhide'), L(32032), 'DefaultAddonNone.png'),
        (build_url(action='reset_cores'), L(32036), 'DefaultAddonGame.png'),
    ]
    for url, label, icon in entries:
        item = xbmcgui.ListItem(label=label)
        item.setArt({'icon': icon})
        xbmcplugin.addDirectoryItem(HANDLE, url, item, isFolder=False)
    xbmcplugin.endOfDirectory(HANDLE)


# --------------------------------------------------------------------- tools

def tool_test(client):
    try:
        platforms = client.platforms()
        notify(L(32028) % len(platforms))
    except RommError as e:
        notify(L(32019) % str(e), xbmcgui.NOTIFICATION_ERROR)


def tool_stats(client):
    try:
        stats = client.stats()
    except RommError as e:
        notify(L(32019) % str(e), xbmcgui.NOTIFICATION_ERROR)
        return
    size_gb = stats.get('TOTAL_FILESIZE_BYTES', 0) / (1024.0 ** 3)
    lines = [
        'Platforms: %s' % stats.get('PLATFORMS', '?'),
        'Games: %s' % stats.get('ROMS', '?'),
        'Saves: %s' % stats.get('SAVES', '?'),
        'States: %s' % stats.get('STATES', '?'),
        'Screenshots: %s' % stats.get('SCREENSHOTS', '?'),
        'Library size: %.1f GB' % size_gb,
    ]
    xbmcgui.Dialog().textviewer(L(32029), '\n'.join(lines))


def tool_clear_cache():
    base = download_dir()
    for entry in os.listdir(base):
        path = os.path.join(base, entry)
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        else:
            os.remove(path)
    notify(L(32031))


def tool_unhide():
    save_json('hidden.json', [])
    notify(L(32033))
    xbmc.executebuiltin('Container.Refresh')


def tool_reset_cores():
    save_json('cores.json', {})
    notify(L(32037))


def hide_platform(platform_id):
    hidden = load_json('hidden.json', [])
    if platform_id not in hidden:
        hidden.append(platform_id)
        save_json('hidden.json', hidden)
    xbmc.executebuiltin('Container.Refresh')


# ------------------------------------------------------------ core selection

def choose_core(platform_slug):
    cores_path = ADDON.getSetting('cores_path').strip()
    if not cores_path:
        notify(L(32041), xbmcgui.NOTIFICATION_WARNING)
        return None
    cores_dir = xbmcvfs.translatePath(cores_path)
    try:
        cores = sorted(f for f in os.listdir(cores_dir)
                       if f.endswith(('.dll', '.so', '.dylib')))
    except OSError:
        cores = []
    if not cores:
        notify(L(32041), xbmcgui.NOTIFICATION_WARNING)
        return None
    idx = xbmcgui.Dialog().select(L(32035), cores)
    if idx < 0:
        return None
    core = os.path.join(cores_dir, cores[idx])
    core_map = load_json('cores.json', {})
    core_map[platform_slug] = core
    save_json('cores.json', core_map)
    notify(L(32042) % platform_slug)
    return core


def core_for(platform_slug):
    core_map = load_json('cores.json', {})
    return core_map.get(platform_slug) or choose_core(platform_slug)


# ------------------------------------------------------- download and launch

def purge_cache(keep_path):
    limit_gb = ADDON.getSettingInt('cache_limit')
    if limit_gb <= 0:
        return
    limit = limit_gb * (1024 ** 3)
    base = download_dir()
    entries = []
    for root, _dirs, files in os.walk(base):
        for f in files:
            p = os.path.join(root, f)
            try:
                entries.append((os.path.getmtime(p), os.path.getsize(p), p))
            except OSError:
                pass
    total = sum(e[1] for e in entries)
    entries.sort()  # oldest first
    for mtime, size, path in entries:
        if total <= limit:
            break
        if os.path.abspath(path) == os.path.abspath(keep_path):
            continue
        try:
            os.remove(path)
            total -= size
        except OSError:
            pass


def extract_zip(zip_path, rom):
    """Extract a multi-part zip next to itself; return the file to launch."""
    out_dir = os.path.join(os.path.dirname(zip_path), rom.get('fs_name', 'extracted'))
    dialog = xbmcgui.DialogProgress()
    dialog.create(ADDON.getAddonInfo('name'), L(32040))
    try:
        with zipfile.ZipFile(zip_path) as z:
            names = z.namelist()
            for i, member in enumerate(names):
                z.extract(member, out_dir)
                dialog.update(int((i + 1) * 100 / len(names)))
    finally:
        dialog.close()
    os.remove(zip_path)
    files = sorted(os.listdir(out_dir))
    m3u = [f for f in files if f.lower().endswith('.m3u')]
    target = m3u[0] if m3u else (files[0] if files else None)
    return os.path.join(out_dir, target) if target else None


def needs_extraction():
    """Kodi's own RetroPlayer (launch_method 0) can't open a raw multi-part zip -
    PlayMedia() on a bare .zip has no game-core route and lands in VideoPlayer,
    which fails outright. Extraction is only truly optional for the external
    launch methods, which may (RetroArch) or may not (custom command, Android)
    handle zips on their own."""
    return ADDON.getSettingBool('extract_zips') or ADDON.getSettingInt('launch_method') == 0


def fetch_rom_to_disk(client, rom_or_id):
    """Download a rom (respecting the existing-file policy). Returns (path, rom).

    Accepts either a rom id or an already-fetched rom detail dict."""
    rom = rom_or_id if isinstance(rom_or_id, dict) else client.rom(rom_or_id)
    files = rom.get('files') or []
    multi = len(files) > 1
    if not multi:
        out_name = (files[0].get('file_name') if files else None) or rom.get('fs_name', 'rom.bin')
    else:
        out_name = (rom.get('fs_name') or 'rom') + '.zip'
    # RomM's own "multi-file" flag isn't the only case that lands as a .zip on
    # disk - a single-file rom can itself be a zip-compressed dump (e.g. some
    # compilation carts). Either way, if what we're about to hand Kodi is a
    # .zip, it needs extracting for launch_method 0: Kodi's playercorefactory
    # dispatches purely on file extension, and most game cores don't register
    # .zip as a valid extension.
    is_zip = out_name.lower().endswith('.zip')
    dest_dir = download_dir(rom)
    dest = os.path.join(dest_dir, out_name)

    # for extracted zips, the extracted folder is the cache marker
    extracted_dir = os.path.join(dest_dir, rom.get('fs_name', ''))
    if is_zip and needs_extraction() and os.path.isdir(extracted_dir):
        existing = extracted_dir
    elif os.path.isfile(dest) and os.path.getsize(dest) > 0:
        existing = dest
    else:
        existing = None

    if existing:
        policy = ADDON.getSettingInt('existing_action')
        if policy == 2:
            use_existing = xbmcgui.Dialog().yesno(
                L(32038), L(32039), yeslabel=L(32043), nolabel=L(32044))
        else:
            use_existing = (policy == 0)
        if use_existing:
            if os.path.isdir(existing):
                files_in = sorted(os.listdir(existing))
                m3u = [f for f in files_in if f.lower().endswith('.m3u')]
                target = m3u[0] if m3u else (files_in[0] if files_in else None)
                if target:
                    return os.path.join(existing, target), rom
            elif is_zip and needs_extraction():
                # a cached raw zip from before extraction was required/enabled -
                # extract it now rather than handing the raw zip back unplayable
                launched = extract_zip(existing, rom)
                if launched:
                    return launched, rom
            else:
                return existing, rom
        if os.path.isdir(existing):
            shutil.rmtree(existing, ignore_errors=True)
        elif os.path.isfile(existing):
            os.remove(existing)

    name = rom_label(rom)
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

    if is_zip and needs_extraction():
        launched = extract_zip(dest, rom)
        if launched:
            dest = launched

    purge_cache(dest)
    return dest, rom


def record_history(client, rom):
    history = load_json('history.json', [])
    history = [h for h in history if h.get('id') != rom['id']]
    history.insert(0, {
        'id': rom['id'],
        'name': rom_label(rom),
        'platform': rom.get('platform_display_name', ''),
        'cover': client.cover_url(rom),
        'ts': int(time.time()),
    })
    try:
        size = max(5, ADDON.getSettingInt('history_size'))
    except Exception:
        size = 25
    save_json('history.json', history[:size])


def launch(client, path, rom):
    if ADDON.getSettingBool('stop_media'):
        xbmc.Player().stop()
    method = ADDON.getSettingInt('launch_method')

    if method == 1:  # external RetroArch
        ra = xbmcvfs.translatePath(ADDON.getSetting('retroarch_path').strip())
        if not ra:
            notify(L(32019) % 'RetroArch path not set', xbmcgui.NOTIFICATION_ERROR)
            return
        slug = rom.get('platform_fs_slug') or rom.get('platform_slug', '')
        core = core_for(slug)
        cmd = [ra, '-L', core, path] if core else [ra, path]
        subprocess.Popen(cmd)
    elif method == 2:  # custom command
        template = ADDON.getSetting('custom_cmd').strip()
        if not template or '%ROM%' not in template:
            notify(L(32019) % 'Custom command not set', xbmcgui.NOTIFICATION_ERROR)
            return
        subprocess.Popen(template.replace('%ROM%', '"%s"' % path), shell=True)
    elif method == 3:  # Android RetroArch via StartAndroidActivity
        pkg = ADDON.getSetting('android_package').strip() or 'com.retroarch'
        xbmc.executebuiltin(
            'StartAndroidActivity("%s","android.intent.action.VIEW","","file://%s")'
            % (pkg, path))
    else:  # Kodi RetroPlayer
        xbmc.executebuiltin('PlayMedia("%s")' % path)

    record_history(client, rom)


def play_trailer(rom):
    video_id = rom.get('youtube_video_id')
    if video_id:
        xbmc.executebuiltin(
            'PlayMedia("plugin://plugin.video.youtube/play/?video_id=%s")' % video_id)


def show_game_info(client, rom):
    """IAGL-style info dialog; returns the chosen action or None."""
    dialog = GameInfoDialog(
        'romm-gameinfo.xml', ADDON.getAddonInfo('path'), 'Default', '1080i',
        rom=rom,
        title=rom_label(rom),
        cover=client.cover_url(rom),
        fanart=client.fanart_url(rom),
        strings={
            'launch': L(32046),
            'trailer': L(32047),
            'download': L(32010),
            'close': L(32048),
        })
    dialog.doModal()
    result = dialog.result
    del dialog
    return result


def do_launch_flow(client, rom):
    try:
        dest, rom = fetch_rom_to_disk(client, rom)
    except RommError as e:
        if str(e) != 'cancelled':
            notify(L(32019) % str(e), xbmcgui.NOTIFICATION_ERROR)
        return
    launch(client, dest, rom)


def select_rom(client, rom_id):
    mode = ADDON.getSettingInt('on_select')
    if mode == 2:  # download only
        download_rom(client, rom_id)
        return
    if mode == 1:  # straight to download + launch
        do_launch_flow(client, rom_id)
        return

    # default: game info dialog first
    try:
        rom = client.rom(rom_id)
    except RommError as e:
        notify(L(32019) % str(e), xbmcgui.NOTIFICATION_ERROR)
        return
    result = show_game_info(client, rom)
    if result == 'launch':
        do_launch_flow(client, rom)
    elif result == 'download':
        download_rom(client, rom)
    elif result == 'trailer':
        play_trailer(rom)


def download_rom(client, rom_or_id):
    try:
        fetch_rom_to_disk(client, rom_or_id)
        notify(L(32017))
    except RommError as e:
        if str(e) != 'cancelled':
            notify(L(32019) % str(e), xbmcgui.NOTIFICATION_ERROR)


# -------------------------------------------------------------------- router

def router(paramstring):
    params = dict(urllib.parse.parse_qsl(paramstring))
    action = params.get('action')

    if action == 'settings':
        ADDON.openSettings()
        return
    if not action:
        list_root()
        return
    if action == 'tools':
        list_tools()
        return
    if action == 'clear_cache':
        tool_clear_cache()
        return
    if action == 'unhide':
        tool_unhide()
        return
    if action == 'reset_cores':
        tool_reset_cores()
        return
    if action == 'hide_platform':
        hide_platform(int(params['platform_id']))
        return
    if action == 'choose_core':
        choose_core(params.get('platform', ''))
        return

    client = get_client()
    if client is None:
        xbmcplugin.endOfDirectory(HANDLE, succeeded=False)
        return

    if action == 'platforms':
        list_platforms(client)
    elif action == 'roms':
        list_roms(client, params)
    elif action == 'collections':
        list_collections(client)
    elif action == 'random':
        list_random(client)
    elif action == 'lastplayed':
        list_lastplayed(client)
    elif action == 'search':
        search(client)
    elif action == 'test':
        tool_test(client)
    elif action == 'stats':
        tool_stats(client)
    elif action == 'select':
        select_rom(client, params['rom_id'])
    elif action == 'download':
        download_rom(client, params['rom_id'])
    else:
        list_root()


if __name__ == '__main__':
    router(sys.argv[2][1:])
