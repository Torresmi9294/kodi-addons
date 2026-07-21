# plugin.program.romm — architecture reference

Internal reference for working on this addon (and its experimental twin). Same idea as
`skin.xperience1080/ARCHITECTURE.md`: a map so future edits don't start from zero.

## What it is

A Kodi program addon that browses a self-hosted [RomM](https://romm.app) server, downloads a
selected ROM to local storage, and hands it to Kodi's game player (`PlayMedia` → RetroPlayer
core picker, external RetroArch, a custom command, or Android RetroArch via
StartAndroidActivity). It deliberately mirrors the user-facing framework of
[IAGL](https://github.com/zach-morris/plugin.program.iagl) — root menu of Browse-by-Platform /
Favorites / Collections / Recently Added / Last Played / Random / Search / Tools, a game-info
dialog on select, per-platform view of RetroArch cores — but is a clean implementation, **not**
a fork: IAGL's internals are built around static XML game-list databases shipped for
archive.org, while RomM is a live authenticated REST API, so almost none of IAGL's code
applies. Where IAGL had a settings concept with no RomM equivalent, that setting was dropped
(archive.org login, download threads); where RomM has native features IAGL never needed
(Favorites, Collections, platform metadata with real logos), those replaced or extended the
IAGL-shaped feature.

## Files

```
plugin.program.romm/
  addon.xml                     id/name/provides; <provides>executable game</provides> is what
                                makes it appear under Program add-ons and in the skin's
                                "Other Program Addon..." picker (xbmc.addon.executable)
  main.py                       router + all UI (directory listings, tools, download, launch)
  resources/
    settings.xml                Kodi "new-format" (version="1") settings definition
    language/resource.language.en_gb/strings.po   ids #32001+
    lib/
      client.py                 RommClient - stdlib-only REST client (urllib, no requests dep)
      gameinfo.py                GameInfoDialog (WindowXMLDialog) shown on game select
    skins/Default/
      1080i/romm-gameinfo.xml   the game-info dialog's own bundled skin XML
      media/white.png            8x8 solid white PNG, diffused for dialog panel backgrounds
    platforms/                  bundled offline platform logos, see platforms/README.md
  ARCHITECTURE.md               this file (main copy only, not in .experimental)
```

Local per-user state lives in the Kodi profile dir (`special://profile/addon_data/
plugin.program.romm/`), not in the addon folder: `hidden.json` (hidden platform ids),
`cores.json` (platform slug → chosen RetroArch core path), `history.json` (last-played list,
newest first, capped at the `history_size` setting), plus `downloads/` (the default download
directory when the `download_path` setting is empty).

## RomM API surface used (grounded from RomM backend source, backend/endpoints/)

Auth (either):
- HTTP Basic — `Authorization: Basic base64(user:pass)` on every request.
- Client API token — RomM Administration → Client API Tokens, format `rmm_` + 64 hex chars,
  sent as `Authorization: Bearer <token>`. The `token` setting, when non-empty, wins over
  username/password (see `RommClient.auth_header`).

Endpoints:
- `GET /api/platforms` → list of PlatformSchema. Fields used: `id`, `display_name` (computed:
  custom_name or name), `name`, `slug`, `fs_slug`, `rom_count`, `url_logo` (platform artwork,
  public CDN URL — see "Platform artwork" below). Client filters out `rom_count == 0` and
  sorts by display name.
- `GET /api/roms` → fastapi-pagination LimitOffsetPage: `{"items": [...], "total": n,
  "limit": l, "offset": o}`. Query params used: `platform_ids` (repeatable int),
  `collection_id`, `favorite` (`true`/`false`), `search_term`, `limit`, `offset`,
  `order_by`/`order_dir` (Recently Added uses `created_at`/`desc`), plus
  `with_char_index=false&with_filter_values=false&with_rom_id_index=false` to skip the heavy
  index payloads meant for RomM's own web UI (they default to true). **Fetched in a loop until
  exhausted** rather than one page at a time — see "Unpaginated listings" below.
- `GET /api/roms/{id}` → full RomSchema, fetched at select/download time. Fields used beyond the
  list view: `files[]` (`file_name`), `metadatum` (`genres`, `first_release_date`, `companies`,
  `average_rating`, `game_modes` — used to build the game-info dialog's detail panel and header
  meta line), `youtube_video_id` (trailer), `merged_screenshots`/`path_screenshots`/
  `url_screenshots` (fanart + "Screenshots" card in the game-info dialog).
- `GET /api/roms/{id}/content/{file_name}` → the download. Server sends a single-file rom as
  the raw file and a multi-part rom (multi-disc etc.) as a zip incl. `.m3u`. Optional
  `file_ids=` comma list narrows multi-part downloads (not currently used).
- `GET /api/collections` → list of CollectionSchema (`id`, `name`, `rom_count`).
- `GET /api/stats` → `{"PLATFORMS": n, "ROMS": n, "SAVES": n, "STATES": n, "SCREENSHOTS": n,
  "TOTAL_FILESIZE_BYTES": n}` — shown verbatim in the Tools → "RomM statistics" text viewer.

Cover art: prefer `url_cover` (metadata-provider CDN, public). Fallback: server-local
`{host}/assets/romm/resources/{path_cover_large}` via `RommClient.resource_url()` — that route
needs auth, which is why it appends Kodi's `|Header=Value` image-URL suffix carrying the
Authorization header. `screenshot_urls()`/`fanart_url()` use the same resource_url() fallback
for screenshots that aren't already public URLs.

## Unpaginated listings

`list_roms()` has no "Next page" folder item and takes no `offset` param from the caller —
Kodi has no true lazy/infinite-scroll for plugin directories (a plugin populates a directory
once, then Kodi just scrolls what it got), so the practical equivalent is fetching *every* page
from RomM internally, in a loop, before ever calling `xbmcplugin.endOfDirectory()`, and handing
Kodi one fully-assembled list. The `page_size` setting (relabeled "Server fetch batch size" —
it's no longer a user-facing page size) controls the batch size of that internal loop, not
anything visible. Tradeoff: for a huge unfiltered listing (e.g. Recently Added across a
library with thousands of ROMs), Kodi shows its native busy spinner for longer up front instead
of paging incrementally — accepted as the cost of "no next-page button," not a bug.
`list_random()` is unrelated to this — it picks one random offset window on each call by
design, not exhaustive fetching.

## Flow

1. `main.py` router dispatches on `action`: none→root, `platforms`, `roms` (handles platform
   browse, Favorites, Collections, and Recently Added/search results — differing only in query
   params), `collections`, `random`, `lastplayed`, `search` (keyboard prompt → delegates to
   `roms`), `tools` (submenu), `test`/`stats`/`clear_cache`/`unhide`/`reset_cores` (tools
   actions), `hide_platform`/`choose_core` (context-menu actions), `select`, `download`,
   `settings`.
2. `select` branches on the `on_select` setting: **0 (default) shows the game-info dialog**
   first (`show_game_info` → `GameInfoDialog`, see below) and acts on its result
   (`launch`/`download`/`trailer`/none); **1** skips straight to download+launch
   (`do_launch_flow`); **2** downloads only.
3. `fetch_rom_to_disk` (download core): GET rom detail if not already a dict, decide output
   name (single file → its `file_name`; multi-part → `fs_name + '.zip'`), check the
   `existing_action` setting (0 launch existing / 1 always re-download / 2 ask via yes/no
   dialog) against a cached file or, for multi-disc, an already-extracted folder. Downloads
   stream via `RommClient.download()` with a cancel-aware `DialogProgress` (cancelling raises
   `RommError('cancelled')` and deletes the partial file). If `extract_zips` is on and the rom
   is multi-part, `extract_zip()` unpacks it next to itself and launches the `.m3u` if present,
   else the first file, then deletes the source zip. `purge_cache()` runs after every download,
   evicting oldest-mtime files first until under the `cache_limit` (GB, 0 = unlimited) setting.
4. `launch()` dispatches on the `launch_method` setting: 0 Kodi `PlayMedia` (RetroPlayer core
   picker), 1 external RetroArch (`retroarch_path` + a per-platform core from `cores.json`,
   prompting via `choose_core()` the first time a platform is launched externally), 2 a custom
   shell command (`custom_cmd`, `%ROM%` placeholder), 3 Android `StartAndroidActivity` with
   `android_package`. `stop_media` setting stops any playing Kodi media first. Every successful
   launch calls `record_history()` (prepends to `history.json`, capped at `history_size`).
5. Download dir setting empty → defaults to
   `special://profile/addon_data/plugin.program.romm/downloads/`; `organize_by_platform`
   nests it one level deeper by `platform_fs_slug`/`platform_slug`.

## Game info dialog (`resources/lib/gameinfo.py` + `resources/skins/Default/1080i/romm-gameinfo.xml`)

A `WindowXMLDialog` bundled inside the addon with its own skin XML — same mechanism IAGL uses
for its info popup, shown by default on game select (unless `on_select` skips it). Layout:
centered title/platform header, cover art left, scrolling summary center, a metadata panel
right (Genre/Date/Studio/Rating/Modes/Size — built from `metadatum`, empty lines collapse),
and four buttons: Launch (3001) / Trailer (3002, disabled via `setEnabled(False)` if the rom
has no `youtube_video_id`) / Download (3003) / Close (3004). `onAction` closes on back/previous
menu. Result is read back via `.result` (`'launch'`/`'trailer'`/`'download'`/`None`) by
`show_game_info()` in main.py. Trailer plays through `plugin.video.youtube`
(`plugin://plugin.video.youtube/play/?video_id=...`) — requires that addon installed to
actually play, degrades to nothing if it isn't. Uses only fonts every Kodi skin defines
(`font13`/`font30`/etc.), not skin-specific ones, so it renders reasonably on both
Xperience1080 and stock Estuary. An earlier "Xbox game-hub" restyle (rounded cards, green Play
button) was tried and explicitly rolled back per user preference — that version still exists
in git history if worth revisiting piecemeal later, but the shipped design is the simpler
original.

## Platform artwork (`resources/platforms/`)

Two-tier: `local_platform_art(platform)` checks
`resources/platforms/<fs_slug or slug>.png` (or `.jpg`) first — bundled inside the addon
package, so it renders even with RomM unreachable — falling back to
`RommClient.platform_logo_url()` (RomM's live `url_logo`, needs network) and finally to a
generic `DefaultAddonGame.png` icon if neither exists. Naming convention and how to add more
are documented in `resources/platforms/README.md`; current set (~220 files, ~21 MB) is a bulk
system-logo pack covering far more platforms than any one RomM library will have — unmatched
files are inert, not an error. Flagged once already and worth repeating: if this repo is
public, official platform/console logos are typically trademarked — a call for whoever
maintains the repo, not something the addon enforces or blocks on.

## Settings (resources/settings.xml, new format)

- **Server**: `host`, `username`, `password` (hidden edit), `token` (level 1 — wins over
  username/password if set), `insecure` (level 1 — unverified SSL context for self-signed
  https).
- **Browsing**: `page_size` (25–500 step 25, default 100 — internal fetch batch size, see
  "Unpaginated listings"), `clean_titles` (bool — RomM's cleaned `name` vs raw `fs_name`),
  `content_type` (0 games/1 movies/2 tvshows — passed to `xbmcplugin.setContent`, lets a skin's
  view-type chooser offer richer video-style views), `history_size` (5–100 step 5, default 25),
  and a group of show/hide toggles for the root menu: `show_favorites`, `show_collections`,
  `show_recent`, `show_lastplayed`, `show_random`.
- **Downloads**: `download_path`, `organize_by_platform` (bool), `existing_action` (0 launch
  existing/1 always re-download/2 ask), `cache_limit` (GB, 0–200, 0 = unlimited),
  `extract_zips` (bool), `on_select` (0 show game-info dialog/1 download+launch/2 download
  only).
- **Launching**: `launch_method` (0 Kodi RetroPlayer/1 external RetroArch/2 custom command/3
  Android RetroArch), `retroarch_path`, `cores_path`, `custom_cmd` (level 1, `%ROM%`
  placeholder), `android_package` (level 1, default `com.retroarch`), `stop_media` (bool).

## Skin integration (skin.xperience1080 Games tab)

Nothing addon-side is needed: `<provides>executable game</provides>` makes this addon
selectable anywhere the skin uses `Skin.SetAddon(..., xbmc.addon.executable)` — the Games
tab's tile editor and the widget picker's "Other Program Addon..." option both qualify. To
make RomM a *named/default* option in the skin's Games widget picker, that's a skin-side edit
(`Includes_SettingsCustomHomeWidgets.xml` widget-6 items + `Widget.6.Games` variable in
`Includes_HomeWidgets.xml`), pointing at `plugin://plugin.program.romm/`.

## Main vs experimental

`plugin.program.romm.experimental` is the same tree under a different id/name (`addon.xml`
differences are intentional and permanent). Same workflow as the skin pair: changes go to
experimental first, get tested on a device, then are promoted by copying changed files (never
`addon.xml`) into this folder and bumping this version. This ARCHITECTURE.md lives only in the
main copy, updated at promotion time.

## Known constraints / untested edges

- Built against the RomM API as of July 2026 (source-inspected, master branch). Older RomM
  versions that return a plain list from `/api/roms` are handled defensively in
  `RommClient.roms`.
- `order_by=created_at` for Recently Added is the frontend's convention; if a server rejects
  it, the roms call errors visibly (notification) rather than silently mislisting.
- Launching relies on the platform file being something RetroPlayer (or the configured external
  launcher) can open; multi-part zips launch only if the target core handles zip/m3u content,
  or `extract_zips` unpacks them first.
- Whether a given platform actually has an RomM-side `url_logo` depends on RomM's own IGDB
  metadata matching, not on this addon; whether it has *local* art depends on whether someone
  dropped a matching file in `resources/platforms/`.
- This has now had real on-device testing against a live RomM server (download, launch,
  favorites/collections, game-info dialog, view switching, platform art) — the areas *not yet
  exercised* on-device: external RetroArch launching + core picker, the custom-command launch
  method, Android StartAndroidActivity, multi-disc zip extraction, and the download-cache
  purge/existing-file-policy paths.
