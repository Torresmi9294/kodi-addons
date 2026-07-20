"""Xbox-game-hub-style game info dialog (WindowXMLDialog backed by
resources/skins/Default/1080i/romm-gameinfo.xml).

Layout mirrors the Xbox Series X|S game page: big title + dot-separated meta
line, age-rating block top right, a row of rounded cards (cover / game details
/ about / screenshots), and a bottom button row with a green primary PLAY.

Buttons: Launch (3001), Trailer (3002), Download (3003), Close (3004). The
chosen action is exposed as .result ('launch' / 'trailer' / 'download' / None).
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
        if value > 1e12:  # milliseconds
            value /= 1000.0
        return time.strftime('%d/%m/%Y', time.gmtime(value))
    except (TypeError, ValueError):
        return str(value)[:10]


def release_year(meta):
    date = release_date(meta)
    return date[-4:] if len(date) >= 4 else ''


def age_rating(meta):
    ratings = meta.get('age_ratings') or []
    if not ratings:
        return ''
    first = ratings[0]
    if isinstance(first, dict):
        first = first.get('rating') or first.get('name') or ''
    return str(first)


def star_rating(meta):
    rating = meta.get('average_rating')
    if not rating:
        return ''
    try:
        rating = float(rating)
        if rating > 10:
            rating /= 20.0  # 0-100 -> 0-5 stars
        return 'Rating: %.1f / 5' % rating
    except (TypeError, ValueError):
        return ''


class GameInfoDialog(xbmcgui.WindowXMLDialog):
    def __init__(self, xml_file, addon_path, skin='Default', res='1080i',
                 rom=None, title='', cover='', fanart='', shots=None, strings=None):
        super().__init__()
        self.rom = rom or {}
        self.title = title
        self.cover = cover
        self.fanart = fanart
        self.shots = shots or []
        self.strings = strings or {}
        self.result = None

    def onInit(self):
        rom = self.rom
        meta = rom.get('metadatum') or {}

        self.setProperty('title', self.title)
        self.setProperty('summary', rom.get('summary') or '')
        self.setProperty('cover', self.cover)
        self.setProperty('fanart', self.fanart or self.cover)

        # header meta line, Xbox style: Studio - Year - Size - Genres
        companies = meta.get('companies') or []
        genres = meta.get('genres') or []
        parts = [
            companies[0] if companies else '',
            release_year(meta),
            human_size(rom.get('fs_size_bytes')),
            ', '.join(genres[:2]),
        ]
        self.setProperty('metaline', '  •  '.join(p for p in parts if p))

        # rating block, top right
        self.setProperty('agerating', age_rating(meta))
        self.setProperty('ratingline', star_rating(meta))
        modes = meta.get('game_modes') or []
        self.setProperty('modesline', ', '.join(modes[:3]))

        # card headers
        self.setProperty('statscard', 'Game details')
        self.setProperty('aboutcard', 'About this game')
        self.setProperty('capturescard', 'Screenshots')
        self.setProperty('noshots', 'No screenshots available for this game.')

        # game details card: caption/value pairs, empty ones collapse
        pairs = [
            ('Platform', rom.get('platform_display_name', '')),
            ('Genre', ', '.join(genres[:3])),
            ('Released', release_date(meta)),
            ('Studio', companies[0] if companies else ''),
            ('Size', human_size(rom.get('fs_size_bytes'))),
        ]
        shown = [(label, value) for label, value in pairs if value][:5]
        for i, (label, value) in enumerate(shown):
            self.setProperty('stat%dlabel' % (i + 1), label)
            self.setProperty('stat%dvalue' % (i + 1), value)

        # screenshots card
        if self.shots:
            self.setProperty('shot1', self.shots[0])
        if len(self.shots) > 1:
            self.setProperty('shot2', self.shots[1])

        # buttons
        self.setProperty('btn_launch', self.strings.get('launch', 'Play'))
        self.setProperty('btn_trailer', self.strings.get('trailer', 'Trailer'))
        self.setProperty('btn_download', self.strings.get('download', 'Download'))

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
