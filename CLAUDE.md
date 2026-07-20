# Repo instructions

This is a Kodi addon repository (see `README.md` for the push-to-update pipeline: edit an
addon, bump its `version`, push — a GitHub Action rebuilds `zips/` automatically).

## skin.xperience1080

`skin.xperience1080/ARCHITECTURE.md` is a maintained reference for that skin's structure
(includes system, Home screen layout, settings mechanism, views, windows/dialogs, colors,
fonts, media, strings, dev conventions).

**When editing anything under `skin.xperience1080/` that changes structure** — a new home menu
item or window id, a renamed/added include, a new settings pattern, a reorganized folder — update
the relevant section of `ARCHITECTURE.md` in the same commit. Small content-only edits (tweaking
a color value, adjusting layout coordinates, fixing a label) don't need a doc update. When in
doubt about whether something is structural, err toward updating the doc — it's cheap, and a
stale doc is worse than no doc.
