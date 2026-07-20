# kodi-addons

Personal Kodi addon repository. Push a version bump, Kodi picks it up automatically.

## Layout

- `plugin.video.kronos.example/` — example addon, proves the pipeline works
- `skin.xperience1080/` — fork of [xperience1080/skin.xperience1080](https://github.com/xperience1080/skin.xperience1080) (upstream fork lives separately at [Torresmi9294/skin.xperience1080](https://github.com/Torresmi9294/skin.xperience1080) for pulling upstream changes); this copy is the one Kodi actually installs from. See `skin.xperience1080/ARCHITECTURE.md` for how it's built.
- `skin.xperience1080.experimental/` — separate addon id, installs side by side with the main skin on the same device. In-progress changes get tested here first; once you're happy with them they're promoted into `skin.xperience1080/`. See "Experimental skin workflow" below.
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
5. For the skin: Add-ons → install from repository → **Kronos Kodi Addons** → Look and feel → Skins → **Xperience1080** → Install, then Settings → Interface → Skin → **Xperience1080**.
6. For the experimental skin (optional, only if you're testing in-progress changes): same path → **Xperience1080 (Experimental)** → Install. It shows up as a separate skin in the picker, so you can switch back to the main **Xperience1080** any time without reinstalling anything.

From then on, any version bump you push updates automatically (Kodi's add-on update check interval, default a few hours — you can force it via Add-ons → My add-ons → the addon → Check for updates, or just reinstall from the repository to grab it immediately while testing).

## Editing the skin

Work directly in `skin.xperience1080/` in this repo (not the standalone fork clone). Edit XML/PNGs under `skin.xperience1080/1080i/` and `skin.xperience1080/media/`, bump `version` in `skin.xperience1080/addon.xml`, then push — same update flow as any other addon here. While actively iterating on a change, `ReloadSkin` (Settings → Xperience1080's own Advanced settings category has a "Reload Skin" action) is faster than reinstalling for XML-only edits, but a version bump + repo update is what actually ships the change to a device automatically.

If you want to pull upstream improvements from the original xperience1080 author later, do that in the standalone fork clone (`C:\Users\krono\skin.xperience1080`, remotes `origin`=your fork, `upstream`=original), then copy the updated files over into this repo's `skin.xperience1080/` folder.

## Experimental skin workflow

`skin.xperience1080.experimental/` is a full copy of the main skin under a different addon id
(`skin.xperience1080.experimental` vs `skin.xperience1080`). Kodi treats it as a completely
separate skin, so it installs and updates independently — you can leave the main skin as your
daily driver and switch to the experimental one only when you want to look at a change on a real
device, then switch back.

**Working on something new:**
1. Edit files under `skin.xperience1080.experimental/` (same structure as the main skin —
   `ARCHITECTURE.md` in `skin.xperience1080/` describes both, since they start identical).
2. Bump `version` in `skin.xperience1080.experimental/addon.xml`, push.
3. On your test device: Settings → Interface → Skin → **Xperience1080 (Experimental)** (or
   install it fresh if you haven't yet). Update it from Add-ons → My add-ons like anything else
   in this repo.

**Promoting a change you're happy with into the main skin:**
1. Copy the changed files from `skin.xperience1080.experimental/` over the corresponding paths in
   `skin.xperience1080/` (everything except `addon.xml` — the id/name/description differences
   there are intentional and permanent, don't copy that file wholesale).
2. Bump `version` in `skin.xperience1080/addon.xml`.
3. Push. The main skin updates on every device that has it installed.

The two folders are expected to drift apart while you're mid-experiment — that's the point. If
you want to reset the experimental copy back to exactly match main (discard an experiment),
just re-copy `skin.xperience1080/` over `skin.xperience1080.experimental/` (excluding
`addon.xml` and `ARCHITECTURE.md`) and bump the experimental version.
