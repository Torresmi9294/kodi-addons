# plugin.program.romm — architecture reference

Internal reference for working on this addon (and its experimental twin). Same idea as
`skin.xperience1080/ARCHITECTURE.md`: a map so future edits don't start from zero.

## What it is

A Kodi program addon that browses a self-hosted [RomM](https://romm.app) server, downloads a
selected ROM to local storage, and hands it to Kodi's game player (`PlayMedia` → RetroPlayer
core picker, or whatever game addon handles the file type). It deliberately mirrors the
user-facing framework of [IAGL](https://github.com/zach-morris/plugin.program.iagl) — root menu
of Browse-by-Platform / Recently Added / Search, paginated game lists with cover art, select =
download+launch — but is a clean implementation, **not** a fork: IAGL's internals are built
around static XML game-list databases shipped for archive.org, while RomM is a live
authenticated REST API, so almost none of IAGL's code applies.

## Files

```
plugin.program.romm/
  addon.xml                     id/name/provides; <provides>executable game</provides> is what
                                makes it appear under Program add-ons and in the skin's
                                "Other Program Addon..." picker (xbmc.addon.executable)
  main.py                       router + all UI (directory listings, download dialog, launch)
  resources/
    settings.xml                Kodi "new-format" (version="1") settings definition
    language/resource.language.en_gb/strings.po   ids #32001+
    lib/client.py               RommClient - stdlib-only REST client (urllib, no requests dep)
  ARCHITECTURE.md               this file (main copy only, not in .experimental)
```

## RomM API surface used (grounded from RomM backend source, backend/endpoints/)

Auth (either):
- HTTP Basic — `Authorization: Basic base64(user:pass)` on every request.
- Client API token — RomM Administration → Client API Tokens, format `rmm_` + 64 hex chars,
  sent as `Authorization: Bearer <token>`. The `token` setting, when non-empty, wins over
  username/password (see `RommClient.auth_header`).

Endpoints:
- `GET /api/platforms` → list of PlatformSchema. Fields used: `id`, `display_name` (computed:
  custom_name or name), `name`, `slug`, `rom_count`. Client filters out `rom_count == 0` and
  sorts by display name.
- `GET /api/roms` → fastapi-pagination LimitOffsetPage: `{"items": [...], "total": n,
  "limit": l, "offset": o}`. Query params used: `platform_ids` (repeatable int), `search_term`,
  `limit`, `offset`, `order_by`/`order_dir` (Recently Added uses `created_at`/`desc`), plus
  `with_char_index=false&with_filter_values=false&with_rom_id_index=false` to skip the heavy
  index payloads meant for RomM's own web UI (they default to true).
- `GET /api/roms/{id}` → full RomSchema, fetched at download time for the `files[]` array.
- `GET /api/roms/{id}/content/{file_name}` → the download. Server sends a single-file rom as
  the raw file and a multi-part rom (multi-disc etc.) as a zip incl. `.m3u`. Optional
  `file_ids=` comma list narrows multi-part downloads (not currently used).

Rom fields used: `id`, `name`, `fs_name`, `fs_name_no_tags`, `platform_display_name`,
`summary`, `url_cover`, `path_cover_large`/`path_cover_small`, `files[]` (`file_name`).

Cover art: prefer `url_cover` (metadata-provider CDN, public). Fallback: server-local
`{host}/assets/romm/resources/{path_cover_large}` — that route needs auth, which is why
`cover_url()` appends Kodi's `|Header=Value` image-URL suffix carrying the Authorization
header.

## Flow

1. `main.py` router dispatches on `action` param: none→root, `platforms`, `roms` (handles
   platform browse, search results, and Recently Added — differing only in query params),
   `search` (keyboard prompt then delegates to roms), `select` (click), `download` (context
   menu), `settings`.
2. `select` → `fetch_rom_to_disk`: GET rom detail, decide output name (single file → its
   `file_name`; multi-part → `fs_name + '.zip'`), skip download if the file already exists
   non-empty in the download dir (cheap re-launch), else stream with a DialogProgress
   (cancel-aware — cancellation raises RommError('cancelled') from the progress callback and
   deletes the partial file). Then `PlayMedia("<path>")` unless the `on_select` setting is
   "Download only".
3. Download dir setting empty → defaults to
   `special://profile/addon_data/plugin.program.romm/downloads/`.

## Settings (resources/settings.xml, new format)

`host` (string), `username`, `password` (hidden edit), `token` (level 1 = advanced),
`insecure` (bool; builds an unverified SSL context for self-signed https), `page_size`
(int slider 25–500 step 25, default 100), `download_path` (path picker), `on_select`
(0 = download+launch, 1 = download only).

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
main copy.

## Known constraints / untested edges

- Built against the RomM API as of July 2026 (source-inspected, master branch). Older RomM
  versions that return a plain list from `/api/roms` are handled defensively in
  `RommClient.roms`.
- `order_by=created_at` for Recently Added is the frontend's convention; if a server rejects
  it, the roms call errors visibly (notification) rather than silently mislisting.
- Launching relies on the platform file being something RetroPlayer (or an installed game
  addon) can open; multi-part zips launch only if the target core handles zip/m3u content.
- No runtime testing has been possible without a live RomM server — first on-device run should
  exercise: server connect, platform list, cover art (both CDN and server-local fallback),
  download progress + cancel, and launch.
