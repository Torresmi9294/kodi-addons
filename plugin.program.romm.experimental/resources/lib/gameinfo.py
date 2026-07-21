"""IAGL-style game info dialog (WindowXMLDialog backed by
resources/skins/Default/1080i/romm-gameinfo.xml).

Shown when a game is selected (if the on_select setting says so). Buttons:
Launch (3001), Trailer (3002), Download (3003), Close (3004). The chosen
action is exposed as .result ('launch' / 'trailer' / 'download' / None).
"""
import time

import xbmcgui

ACTION_CLOSE = (9, 10, 92)  # back, previousmenu, nav back

BTN_LAUNCH = 3001
BTN_TRAILER = 3002
BTN_DOWNLOAD = 3003
BTN_CLOSE = 3004


def human_size(num_bytes):
    try:
        num_bytes = float(num_bytes)
    except (TypeError, ValueError):
        return ''
    for unit in ('B', 'kB', 'MB', 'GB'):
        if num_bytes < 1024 or unit == 'GB':
            return '%.1f %s' % (num_bytes, unit)
        num_bytes /= 1024.0
    return ''


def release_date(meta):
    """metadatum.first_release_date arrives as an epoch (s or ms) or ISO string."""
    value = meta.get('first_release_date')
    if not value:
        return ''
    try:
        value = float(value)
    except (TypeError, ValueError):
        return str(value)[:10]
    if value > 1e12:  # milliseconds
        value /= 1000.0
    try:
        # time.gmtime() raises OSError on Windows (not just ValueError/
        # OverflowError as on Linux) for timestamps its C runtime can't
        # represent - a bad/out-of-range first_release_date must not be
        # allowed to crash the whole info dialog.
        return time.strftime('%d/%m/%Y', time.gmtime(value))
    except (OSError, OverflowError, ValueError):
        return ''


def build_meta_lines(rom):
    """The right-hand info panel: (line, ...) with empty lines dropped in XML."""
    meta = rom.get('metadatum') or {}
    lines = []

    genres = meta.get('genres') or []
    if genres:
        lines.append('Genre: %s' % ', '.join(genres[:3]))

    date = release_date(meta)
    if date:
        lines.append('Date: %s' % date)

    companies = meta.get('companies') or []
    if companies:
        lines.append('Studio: %s' % companies[0])

    rating = meta.get('average_rating')
    if rating:
        try:
            rating = float(rating)
            if rating > 10:
                rating /= 20.0  # 0-100 -> 0-5 stars
            lines.append('Rating: %.1f' % rating)
        except (TypeError, ValueError):
            pass

    modes = meta.get('game_modes') or []
    if modes:
        lines.append('Modes: %s' % ', '.join(modes[:2]))

    size = human_size(rom.get('fs_size_bytes'))
    if size:
        lines.append('Size: %s' % size)

    return lines


class GameInfoDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, xml_file, addon_path, skin='Default', res='1080i',
                 rom=None, title='', cover='', fanart='', strings=None):
        super().__init__()
        self.rom = rom or {}
        self.title = title
        self.cover = cover
        self.fanart = fanart
        self.strings = strings or {}
        self.result = None

    def onInit(self):
        rom = self.rom
        self.setProperty('title', self.title)
        self.setProperty('platform', rom.get('platform_display_name', ''))
        self.setProperty('summary', rom.get('summary') or '')
        self.setProperty('cover', self.cover)
        self.setProperty('fanart', self.fanart or self.cover)
        self.setProperty('btn_launch', self.strings.get('launch', 'Launch'))
        self.setProperty('btn_trailer', self.strings.get('trailer', 'Trailer'))
        self.setProperty('btn_download', self.strings.get('download', 'Download'))
        self.setProperty('btn_close', self.strings.get('close', 'Close'))

        for i, line in enumerate(build_meta_lines(rom)[:6]):
            self.setProperty('meta%d' % (i + 1), line)

        if not rom.get('youtube_video_id'):
            try:
                self.getControl(BTN_TRAILER).setEnabled(False)
            except Exception:
                pass

    def onClick(self, control_id):
        if control_id == BTN_LAUNCH:
            self.result = 'launch'
        elif control_id == BTN_TRAILER:
            self.result = 'trailer'
        elif control_id == BTN_DOWNLOAD:
            self.result = 'download'
        else:
            self.result = None
        self.close()

    def onAction(self, action):
        if action.getId() in ACTION_CLOSE:
            self.result = None
            self.close()
