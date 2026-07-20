import sys
from urllib.parse import urlencode, parse_qsl

import xbmcgui
import xbmcplugin
import xbmcaddon

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])


def build_url(query):
    return sys.argv[0] + '?' + urlencode(query)


def list_items():
    version = ADDON.getAddonInfo('version')
    label = f'Hello from Kronos Example v{version}'
    item = xbmcgui.ListItem(label=label)
    item.setInfo('video', {'title': label})
    xbmcplugin.addDirectoryItem(HANDLE, build_url({'action': 'noop'}), item, isFolder=False)
    xbmcplugin.endOfDirectory(HANDLE)


def router(paramstring):
    params = dict(parse_qsl(paramstring))
    if params.get('action') == 'noop':
        xbmcgui.Dialog().notification(
            ADDON.getAddonInfo('name'), 'It works!', xbmcgui.NOTIFICATION_INFO, 3000
        )
    else:
        list_items()


if __name__ == '__main__':
    router(sys.argv[2][1:])
