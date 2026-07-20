# kodi-addons

Personal Kodi addon repository. Push a version bump, Kodi picks it up automatically.

## Layout

- `plugin.video.kronos.example/` — example addon, proves the pipeline works
- `repository.kronos/` — the repository addon Kodi installs once; it points at this repo's `zips/` folder
- `tools/build.py` — builds `zips/` (per-addon zips + `addons.xml` + `addons.xml.md5`) from the addon folders
- `.github/workflows/build.yml` — runs `tools/build.py` and commits `zips/` on every push to `main`

## Adding a new addon

1. Create a new folder at the repo root named after the addon id (e.g. `plugin.video.something`), with a valid `addon.xml`.
2. Push. The GitHub Action rebuilds `zips/` and commits it.

## Updating an existing addon

1. Bump the `version` attribute in that addon's `addon.xml`.
2. Push. Kodi checks `repository.kronos` periodically and will offer/apply the update.

You can also build locally before pushing: `python tools/build.py`.

## Installing on Kodi (one-time setup)

1. Settings → System → Add-ons → turn on **Unknown sources**.
2. Settings → File manager → **Add source** → enter:
   `https://raw.githubusercontent.com/Torresmi9294/kodi-addons/main/zips/repository.kronos/`
   Name it e.g. `kronos-repo`.
3. Add-ons → install from zip file → the source you just added → `repository.kronos-1.0.0.zip`.
4. Add-ons → install from repository → **Kronos Kodi Addons** → Video add-ons → **Kronos Example** → Install.

From then on, any version bump you push updates automatically (Kodi's add-on update check interval, default a few hours — you can force it via Add-ons → My add-ons → the addon → Check for updates, or just reinstall from the repository to grab it immediately while testing).
