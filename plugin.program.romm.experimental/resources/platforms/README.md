# Bundled platform artwork

Drop platform logo/art images here to ship them **inside the addon package**,
so they display even when RomM is unreachable (no network fetch needed for
these). The addon checks this folder first; RomM's own `url_logo` (live,
requires network) is only used as a fallback when no local file matches.

## Naming convention

Filename must be the platform's RomM slug, lowercase, `.png` or `.jpg`:

```
resources/platforms/<fs_slug>.png
```

`fs_slug` is the identifier RomM uses for that platform's folder on its own
filesystem (e.g. `snes`, `n64`, `psx`, `3do`) - it's the most stable
identifier RomM exposes, so prefer it. If a platform has no `fs_slug` for
some reason, the addon falls back to trying `slug` instead.

To find the exact value for a platform on your server: `GET /api/platforms`
on your RomM instance and read the `fs_slug` field, or check the folder name
RomM created for that platform on disk.

## Notes

- No file here for a platform = falls back to RomM's live `url_logo`, same
  as before this feature existed. Nothing breaks by leaving this empty.
- Recommended: square-ish or logo-shaped transparent PNGs work best - these
  get used as the tile's icon *and* thumb/poster art.
- If your `kodi-addons` repo is public, be aware official platform/console
  logos are typically trademarked. That's a call for you to make, not
  something the addon enforces.
