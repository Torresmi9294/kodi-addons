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

## skin.xperience1080.experimental

A separate-addon-id copy of the main skin, used to test in-progress changes on a real Kodi
device without touching the daily-driver install. See "Experimental skin workflow" in
`README.md` for the edit/promote/reset cycle.

- **Default assumption:** unless the user says otherwise, skin changes they ask for should go
  into `skin.xperience1080.experimental/`, not `skin.xperience1080/` directly — that's the whole
  point of having it. Only touch `skin.xperience1080/` directly for a promotion (moving
  already-tested experimental changes over) or a trivial fix the user explicitly says to apply
  straight to main.
- `ARCHITECTURE.md` lives only in `skin.xperience1080/` and documents both copies' structure
  (they start identical). If an edit to the experimental copy changes something structural
  enough that `ARCHITECTURE.md` would need updating, update it at promotion time rather than
  mid-experiment — no need to track in-flux experimental structure in a doc meant to describe
  the stable main skin.
- `addon.xml` differences between the two (`id`, `name`, `description`) are intentional and
  permanent — never overwrite one with the other wholesale.
