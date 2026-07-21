# Xperience1080 — architecture reference

Internal reference for working on this skin. Not shipped as user-facing docs, just a map so
future edits don't require re-deriving the structure from scratch.

Target: Kodi 21 "Omega" (`xbmc.gui` 5.17.0), addon id `skin.xperience1080`. Resolution folder
is `1080i` despite being true 1920x1080 — legacy naming, not a real interlaced/progressive
distinction. Everything lives flat in `1080i/` — there are **no** `windows/`, `dialogs/`, or
`views/` subfolders, and `colors/` is a single file, not a folder of themes.

## 1. Includes system

`1080i/Includes.xml` is the root manifest, auto-loaded by Kodi for every window. Include order:

```
Defaults.xml
Includes_Commons.xml
Includes_Animations.xml
Includes_ContextMenu.xml
Includes_HomeWidgets.xml
Includes_HomeCommons.xml
Includes_Home.xml
Includes_WindowContents.xml
Includes_ViewHeader.xml
Includes_Views.xml
Includes_Flags.xml
Includes_Keyboard.xml
Includes_GuideInterface.xml
Includes_Settings.xml
Includes_SettingsCustomHomeItems.xml
Includes_SettingsCustomHomeWidgets.xml
Includes_SettingsCustomGuideItems.xml
Includes_TVGuide.xml
Includes_OSD.xml
Includes_DialogConfirm.xml
Includes_Dialogs.xml
Includes_DialogSettings.xml
Includes_Weather.xml
Includes_PVR.xml
```

Also defines module constants `FanartCrossfadeTime`/`IconCrossfadeTime` (both `400`) and small
parametrized includes: `SpinControlDefault`/`SpinControlReversed`, `MenuControl`.

Not pulled in by `Includes.xml` directly but referenced from `Includes_Views.xml`:
`ViewtypesVideos.xml`, `ViewtypesMusic.xml`, `ViewtypesPictures.xml`, `ViewtypesPrograms.xml`,
`ViewtypesAddons.xml`.

Per-file cheat sheet (representative `<include name="...">` entries, not exhaustive):

- **Includes_Commons.xml** — cross-window chrome: `OptionsMenu`, `OptionsMenuButton`,
  `CommonNowPlaying`, `CommonClock`, `CommonHomeInfo`, `CommonInfo`, `CommonInfoNoOptions`.
- **Includes_Animations.xml** — `OptionsShutdownAnimation`, `OpenButtonMenuAnimation`,
  `OpenCloseAnimationContext`, `Animation_FanartFade`, `visiblehidefade`/`visiblehidefadeflags`,
  `homebuttonsanim`–`homebuttonsanim4`, `defaultfocusanim`, `ThumbnailAnimationsPanel`/
  `Poster`/`Shadow`, `CommonViewAnimations`, `BannerListAnimations`.
- **Includes_Dialogs.xml** — `DialogButtonVars`, `DialogButtonDimensions(RightAlign/Small)`,
  `ArtDialogPanelWidthPoster`/`Landscape`/`Square`/`Banner`, `DialogAddonSettings`(+OSD),
  `DialogSelect`(+OSD), `DialogTextViewerDefault`, `FileBrowserDefault`/`Art`.
- **Includes_Flags.xml** — video/audio flag-icon layout: `AspectDimensionsSmall`,
  `ResDimensionsSmall`, `aChannelsDimensions`, `aCodecDimensionsSmall`, `vCodecDimensionsSmall`,
  `MPAADimensionsSmall`, `InfoFlags`, `TVRatingFlagLayout`/`TVRatingFlags`/`TVRatingFlagsSmall`.
- **Includes_ContextMenu.xml** — `ContextMenuBackgroundVars`, `ContextMenuGroupListVars`,
  `ContextMenuButtonVars`, `ContextMenuDefault`, `ContextMenuHome`,
  `ContextMenuPVRChannelManager`, `ContextMenuFileManager`, `ContextMenuAddonInfo`,
  `ContextMenuVideoBookmarks`.
- **Includes_DialogSettings.xml** — `OSDDialogSettings`, `DialogSettings` (native video/audio
  settings popup).
- **Includes_DialogConfirm.xml** — `DialogConfirmDefault`, `DialogConfirmProgress`.
- **Includes_Settings.xml** — building blocks for the custom settings UI: `SettingsButtonVars`,
  `SettingsButtonBackground`, `SettingsLabelVars`, `SettingsFocusImageVars`,
  `SettingsCategoryButtonVars`, `SettingsCategoryDefaultButtonVars`,
  `SettingsCategoryRadioButtonVars`, `SettingsCategoryReloadSkin`,
  `SettingsCategoryGrouplistVars`, `SettingsDialogRadioButtonVars`,
  `SettingsDialogGrouplistVars`, `SettingsCustomDialogButtonVars`,
  `SettingsCustomDialogRadioButtonVars`.
- **Includes_Home.xml** (~450 KB, the biggest file in the skin) — the actual `HomeItems`
  control tree; see section 2.
- **Includes_HomeCommons.xml** — `FocusPosition`, `FocusSettingsCategory`,
  `HomeWidgetContextMenuOverlay`, `HomeWidgetActions`, `HomeShutdownFavouritesButtons`,
  `HomeLabel`, `HomeProfileInfoLabel`, `HomeProfileInfo`, `HomeCategoryLabels`.
- **Includes_HomeWidgets.xml** — `HomeWidgets.Initialization` (widget content paths on load).
  The Games widget (`Widget.6.Games`, widget slot 6) is keyed off `HomeWidget.6.Type`: `30` =
  `plugin.program.romm` (random-across-platforms listing), `32` = `plugin.program.romm.experimental`
  (same, for pointing the widget at whatever's being tested there without touching main), `31` =
  Advanced Emulator Launcher, `34` = any other program addon via `GamesWidgetPath`
  (`Includes_SettingsCustomHomeWidgets.xml` is the type picker). The widget's click handler
  (`Includes_Home.xml`, group `1002`) runs `RunPlugin()` on the focused item's path rather than
  `ShowPicture()` — it was copy-built from the original Pictures widget this tab replaced, and
  `ShowPicture()` was a leftover from that heritage that never did anything useful for a game
  item; `RunPlugin()` re-enters whichever addon supplied the item exactly as a normal directory
  selection would, so it launches per that addon's own on-select behavior.
- **Includes_Views.xml** — pulls in the `Viewtypes*.xml` files, assembles per-media-type view
  lists (`VideoViews`, `MusicViews`, `PictureViews`, `ProgramViews`, `AddonViews`,
  `MusicPlaylistViewIds`/`VideoPlaylistViewIds`), plus a large block of art-fallback
  `<variable>`s (`WidgetPoster`, `DefaultListPoster`, `ExtendedViewThumb`, `ListItem.Label`...).
- **Includes_WindowContents.xml** — `FullscreenDimensions`, `CommonOverlay`, `CommonItemsHome`,
  `CommonItems`, `CommonSettingsItems`, `CommonPVRItems`, `CommonWeatherItems`,
  `HomeCustomBackdrops`, `CommonContent`, `BackgroundFanart`(+MusicOSD), `FadeBackgroundDialog`/
  `FadeBackground`, `SortLetterFileBrowser`/`SortLetterSelectDialog`.

## 2. Home screen

`1080i/Home.xml` is thin — it just assembles includes and handles startup routing:

```xml
<window>
    <defaultcontrol>525</defaultcontrol>
    <onload condition="!Skin.HasSetting(Skin.Initialization)">SetProperty(Skin.Initialization,1,startup)</onload>
    <onload condition="!Skin.HasSetting(Skin.Initialization) | String.IsEmpty(Window(startup).Property(Started))">ReplaceWindow(startup)</onload>
    <include condition="!String.IsEmpty(Window.Property(CategoryChanged))">FocusSettingsCategory</include>
    <onunload>SetProperty(HomeCategory,$INFO[Container(20).CurrentItem])</onunload>
    <controls>
        <include>CommonItemsHome</include>
        <include>HomeCategoryLabels</include>
        <include>HomeItems</include>
        <include>HomeProfileInfo</include>
        <include condition="!Skin.HasSetting(HideHomeButtons)">HomeShutdownFavouritesButtons</include>
        <include>CommonHomeInfo</include>
    </controls>
</window>
```

All the real work is in `HomeItems`, defined in `1080i/Includes_Home.xml`. It's a horizontal
`<grouplist id="40">` (`itemgap="-815"`, panels overlap into a filmstrip). The main-menu focus
container is `Container(20)`. Each home category is a `<control type="group" id="N00">` inside
that grouplist — **the grouplist lays out children in XML document order**, so the category's
*visual/navigation position* is literally where its `<control type="group">` block sits in the
file, left-to-right:

| group id | category | notes |
|---|---|---|
| 100 | Search (only if `System.HasAddon(script.globalsearch)`) | |
| 500 | Home (dashboard tile, search fallback) | |
| 1000 | **Games** | repurposed from the original "Pictures" tab (Kodi's picture library was never a great fit for a home-screen headline item on this skin); defaults its main click and one widget slot to [IAGL](https://github.com/zach-morris/plugin.program.iagl) (`plugin.program.iagl`), with Advanced Emulator Launcher (`plugin.program.advanced.launcher`) as an alternate, or any other installed Program addon via a picker. Internal `Skin.String`/`Skin.HasSetting` keys are `HomeGames*` (renamed from `HomePictures*` when repurposed — a plain literal-string rename, ~192 occurrences, no numeric control/panel ids were touched). |
| 900 | Live TV | |
| 200 | Movies | |
| 300 | TV Shows | |
| 400 | Music | |
| 600 | Programs | |
| 700 | Weather | |
| 800 | Settings (always visible, `<onclick>ActivateWindow(4)</onclick>`) | |

Every category except Search and Settings is gated by `Skin.HasSetting(HomeXxx)` (e.g.
`HomeTV`, `HomeMovies`, `HomeTVShows`, `HomeMusic`, `HomeGames`, `HomePrograms`,
`HomeWeather`). Toggling one off means neighboring groups' `<onleft>`/`<onright>` chains skip
past it, e.g.:

```xml
<onright condition="!Skin.HasSetting(HomeGames)">1025</onright>
<onright condition="!Skin.HasSetting(HomeTV)">925</onright>
```

**This nav-chain pattern repeats at every focus boundary in the file** — duplicated across each
category's main button *and* its 1-2 side panels (e.g. Movies has button `225` plus panels `201`
[left]/`203` [right]; a category with no submenu split, like Games, still has button `1025` plus
panels `1001`[left]/`1003`[right]). **Reordering or adding a category means editing this chain
in every neighboring category's button and panels, not just the one moving.** Concretely, when
Games was moved from last position to right after Home:

- Every group whose left/right neighbor changed needed its `onleft`/`onright` updated — that
  ended up being 7 of the 9 categories, not just Games and its new immediate neighbors.
- **Multiple conditional `<onleft>`/`<onright>` tags use first-match-wins**, evaluated top to
  bottom (confirmed against the [Kodi Skinning Manual](https://kodi.wiki/view/Skinning_Manual) —
  not documented anywhere in this codebase, easy to get backwards). An unconditional fallback
  entry (e.g. `<onright>Control.Move(20,1)</onright>`) **must be listed last**, or every
  conditional entry after it becomes dead code. The original skin is inconsistent about this in
  a few spots (unconditional fallback listed mid-chain) — evidently harmless in practice because
  Kodi's plain directional container scroll already skips hidden items as a side effect, but
  don't copy that quirk into new code; put fallbacks last.
- Cross-tab "enter the next category from its **left** panel, leave from its **right** panel"
  convention: a category's right-side panel's `onright` should point at the *next visible
  category's left panel* (e.g. Movies panel `203`'s onright → TVShows panel `301`, not `303`).
  Getting the left/right panel id backwards here doesn't break navigation, it just makes you
  enter the neighboring tab already-focused on the wrong tile (this exact mistake shipped once
  during the Games reorder: Games panel `1003`'s onright pointed at Live TV's right panel `903`
  instead of its left panel `901`, so moving right from Games landed on "Guide" instead of "TV
  channels").
- **There are two independent places the category's name/order is rendered, not one:**
  1. `1080i/Includes_HomeCommons.xml`'s `HomeCategoryLabels` include has an invisible
     2x2px `<wraplist id="20">` ("Category list") whose `<content><item>` order drives
     `Container(20).CurrentItem`/focus-position bookkeeping — reordering this matters for
     internal state but **does not** move anything on screen.
  2. The **visible** category-name text row is a separate `<control type="grouplist">`
     ("Category labels") in that same include, containing one discrete
     `<control type="label">` per category (each with its own
     `Container(20).HasFocus(itemId)`-gated fade animation) — **this is also a grouplist, so
     it lays out in document order too**, independently of #1. Moving a category means
     reordering its label block here as well, or the nav order and the visible tab-name order
     will disagree (exactly what happened the first time Games was reordered: nav worked,
     names didn't move).

Reusing/repointing an existing slot (as Games did, from "Pictures") stays much cheaper than
inventing a brand-new numbered group, since the button id, panel ids, tile-editor wiring
(`Includes_SettingsCustomHomeItems.xml`), and widget-picker settings screen
(`Includes_SettingsCustomHomeWidgets.xml`) all already exist and just need their `Skin.String`
key prefix renamed and their default content/actions repointed.

Each category group also owns its home-widget content controls and a quick-submenu popup.

**Submenus** (`Custom_HomeSubmenu*.xml`) are small popup dialog windows — a horizontal button
strip listing sub-sections (Files/Genres/Years/Actors/Directors/Studios/Countries/Tags/library
update icon):

| file | window id |
|---|---|
| `Custom_HomeSubmenuMovies.xml` | 3020 |
| `Custom_HomeSubmenuTVShows.xml` | 3021 |
| `Custom_HomeSubmenuMusic.xml` | 3022 |
| `Custom_HomeSubmenuLiveTV.xml` | 3023 |

Structure: a `GroupList` of `<control type="label">` items (using shared `HomeLabel` include)
with fade/zoom animations tied to `Container(3).HasFocus(n)`, paired with a hidden
`wraplist id="3"` whose `<content><item id="n">` entries carry the real navigation, e.g.:

```xml
<item id="3"><onclick>PreviousMenu</onclick><onclick>ActivateWindow(videos,moviegenres,return)</onclick></item>
```

**To add a new top-level home item:** add a `Skin.ToggleSetting(HomeXxx)` toggle in
`Custom_SettingsDialog.xml`'s Home category grouplist → add a new `<control type="group"
id="N00">` block to `HomeItems` following the existing pattern (button id `N25`, content group
id `N50`, tile art, widget controls) → thread the new group id into the nav chains of its
neighbors and of Home (500)/Settings (800).

## 3. Skin settings mechanism

No `SkinShortcuts` addon integration is actually used. `.gitignore` has a defensive
`1080i/script-skinshortcuts-includes.xml` line but nothing references that file — leftover, not
a real feature.

Settings are plain native Kodi skin settings (`Skin.HasSetting`, `Skin.ToggleSetting`,
`Skin.String`, `Skin.SetString`, `Skin.SetBool`, `Skin.SetFile`, `Skin.SetAddon`, `Skin.Reset`)
surfaced through custom dialog windows, coordinated via `Window(skinsettings).property(...)`:

1. **`1080i/SkinSettings.xml`** (window `skinsettings`) — the main settings hub. Left-hand
   category list (`control type="list" id="30"`, items 31–38: General/Home/Media/OSD/
   Background/Quick-Nav/Advanced/Add-on Settings), right-hand `grouplist id="5"` panels gated
   `<visible>Container(30).HasFocus(3x)</visible>`. Simple toggles are `radiobutton`s:
   ```xml
   <control type="radiobutton" id="1002">
       <selected>Skin.HasSetting(BackgroundVideo)</selected>
       <onclick>Skin.ToggleSetting(BackgroundVideo)</onclick>
       <label>$LOCALIZE[31102]</label>
   </control>
   ```
   Multi-value settings cycle via spin buttons calling `Skin.SetString`/`Skin.String` chains
   (e.g. default music view cycles `Skin.SetString(music.name, ...)` /
   `Skin.SetString(music.path, ...)`). File pickers use `Skin.SetFile(...)` (e.g.
   `StartupPlaylist.Path`); addon pickers use `Skin.SetAddon(...)` (e.g. `LyricScript_Path`).
   `onload` bootstraps default string values: `Skin.SetString(music.name,$LOCALIZE[14022])`,
   `Skin.SetString(rss.setting,$LOCALIZE[1223])` if unset.

2. **`1080i/Custom_SettingsDialog.xml`** (window id `3001`) — floating popup reused for several
   settings sub-screens, switching content via
   `String.IsEqual(Window(skinsettings).property(Dialog),$LOCALIZE[xxxxx])` — the caller sets
   `Window(skinsettings).Property(Dialog)` before `ActivateWindow(3001)`. **This is where the
   Home-tile on/off toggles live**:
   ```xml
   <control type="radiobutton" id="2101">
       <selected>!Skin.HasSetting(HomeTV)</selected>
       <onclick>Skin.ToggleSetting(HomeTV)</onclick>
       <onclick>SetProperty(CategoryChanged,1,Home)</onclick>
       <label>$LOCALIZE[19020]</label>
   </control>
   ```
   (same pattern for `HomeMovies`, `HomeTVShows`, `HomeMusic`, `HomeGames`, `HomePrograms`,
   `HomeWeather`). `SetProperty(CategoryChanged,1,Home)` is what `Home.xml`'s
   `FocusSettingsCategory` include picks up to refresh Home after a toggle.

3. **`1080i/Custom_SettingsBackgroundDialog.xml`** (window id `3002`) — same
   `Window(skinsettings).property(Dialog)`/`property(CustomDialog)` pattern, for background
   pickers.

4. **`1080i/Custom_PanelDialog.xml`** (window id `3003`) — the Home tile editor
   (icon/label/type/path per user-customizable tile slot). Backed by `Skin.String(...)` keys
   like `HomeHomeTile1.Label`, `HomeHomeTile1.Icon`, `HomeHomeTile1.Type`, `HomeHomeTile1.Path`.
   `1080i/Includes_SettingsCustomHomeItems.xml` defines `HomeTileEditLabel`/`HomeTileEditIcon`/
   `HomeTileEditTypeName` variables that switch on `Window(3003).Property(SingleDialog)`
   (`item1`…`item42`) to read the right `Skin.String(...)` for whichever slot is being edited
   (video tiles 1/2/5/6, TV-show tiles 1–4, music tiles 1–6, program tiles 1–10, home tiles 1–2,
   game tiles 1–4 [`HomeGamesTile1-4`, renamed from `HomePicturesTile1-4`]).

5. **`1080i/Custom_LanguageDialog.xml`** (window id `3006`) — MPAA/subtitle language filter
   picker, also settings-adjacent (`Skin.SetString`).

**Pattern for adding a new toggle setting:** add a `radiobutton` to the right category
`grouplist` (in `SkinSettings.xml` or a sub-dialog), bind `<selected>Skin.HasSetting(YourSetting)
</selected>` + `<onclick>Skin.ToggleSetting(YourSetting)</onclick>`, give it a `$LOCALIZE[id]`
label (add a string id to `language/resource.language.en_gb/strings.po` if none free), then
consume it anywhere as `Skin.HasSetting(YourSetting)` in a `<visible>`/`<enable>`/condition, or
`Skin.String(YourSetting)`/`$INFO[Skin.String(YourSetting)]` for string-valued settings. No
separate settings-definition file needed — Kodi persists these automatically per-user.

## 4. Views

No `1080i/views/` folder. View layouts live in five files directly under `1080i/`:
`ViewtypesVideos.xml`, `ViewtypesMusic.xml`, `ViewtypesPictures.xml`, `ViewtypesPrograms.xml`,
`ViewtypesAddons.xml`. Each defines `<include name="Viewtype-XXX">` blocks (`Viewtype-List`,
`Viewtype-InfoList`, `Viewtype-Panel`, `Viewtype-Landscape`, `Viewtype-Poster`,
`Viewtype-Thumbnail`, `Viewtype-ThumbnailVideo`, `Viewtype-Banner`, `Viewtype-Fanart`,
`Viewtype-MusicList`, `Viewtype-CoverView`, `Viewtype-PictureView`, `Viewtype-ProgramPanel`,
...), each wrapping `<control type="group"><visible>Control.IsVisible(NN)</visible>...
<control type="list" id="NN"><viewtype label="LOCID">list</viewtype>...`, numbered by Kodi's
standard view-id convention (e.g. `id="50"` = List view).

`1080i/Includes_Views.xml` aggregates: includes the five `Viewtypes*.xml` files, then bundles
individual `Viewtype-*` includes into composite includes (`VideoViews`, `MusicViews`,
`MusicFileViews`, `PictureViews`, `ProgramViews`, `GamesViews`, `AddonViews`,
`VideoPlaylistViews`, `MusicPlaylistViews`) plus raw `<views>id,id,...</views>` lists
(`MusicPlaylistViewIds`, `VideoPlaylistViewIds`). Window files (`MyVideoNav.xml`,
`MyMusicNav.xml`, etc.) declare `<views>50,52,53,54,55,500,501,502,60</views>` and
`<include>VideoViews</include>` to wire up available views.

Naming convention: **`Viewtype-<Style>`** include name ↔ numeric Kodi view id baked into the
control's `id` and `<viewtype label="$LOCALIZE[id]">stylekeyword</viewtype>`. Texture paths
reference `media/views/<style>/...` (e.g. `views/list/panel/panel.png`,
`views/fallbacks/DefaultVideo.png`).

**All view types are unlocked for all content/plugins** (as of this doc). Originally, most
non-List views in every media window were gated on content type or, for Programs, literally
`$EXP[IsPluginAdvancedLauncher]` — meaning a generic addon (any Program addon that isn't
Advanced Launcher) only ever got List and Thumbnail, with every other view chooser button
either hidden or, if visible, silently falling back to List when clicked. Two separate gates
had to be found and removed, in two different places:

1. **The chooser buttons** (`MyVideoNav.xml`, `MyMusicNav.xml`, `MyPics.xml`,
   `MyPrograms.xml`, `AddonBrowser.xml`, `MyGames.xml` — the `<control type="radiobutton"
   id="2NN">` entries with `onclick>Container.SetViewMode(N)` inside the `OptionsMenu`
   popup): had `<visible>` conditions like `$EXP[IsPluginAdvancedLauncher]` or
   `Container.Content(Artists)` gating whether the option even showed up in the menu.
2. **The actual view containers** (the `<control type="list|panel|wraplist|fixedlist"
   id="N">` declared inside each `Viewtype-*` include, registered via the window's `<views>`
   tag) — these had the *same kind* of gate directly on themselves, independent of the
   chooser buttons. This is the one that actually matters functionally: Kodi's
   `CGUIViewControl::UpdateViewVisibility()` filters which views are even *switchable* by
   evaluating each candidate's current visibility before applying `Container.SetViewMode`,
   so a view gated this way can never become the active view via a click — fixing only the
   buttons (unlocking the menu) without also fixing the containers (unlocking the
   destination) is purely cosmetic. Removing the button gate without removing the container
   gate reproduces the exact "shows the option, but clicking it does nothing" symptom.

Fixed by stripping the `<visible>` tag from both layers, everywhere, across all five
`Viewtypes*.xml` files (`MyGames.xml` was also upgraded from the 2-view `GamesViews` set to
the full 13-view `ProgramViews` set it already declared in `<views>` but never shipped).

**Cover/thumb art aspect ratio is `keep`** (image size ≤ box size, full image visible,
proportional, no crop/distortion — Kodi's `CAspectRatio` enum, confirmed via
`xbmc/guilib/AspectRatio.h`) on every `ListItem.Thumb`/`ListItem.Icon`/`ListItem.Art(fanart)`
image across every `Viewtype-*` include in all five files. It was previously an inconsistent
mix of `scale` (crop-to-cover), `stretch` (distort-to-fill), and — for a couple of controls
that had no `<aspectratio>` tag at all — a silent default of `stretch` (Kodi's
`CAspectRatio` constructor default). `keep` may show thin letterbox/pillarbox bars when a
box art's aspect ratio doesn't exactly match the tile's; that trade-off (over crop or
distortion) was a deliberate, explicit choice, not a default — reconsider before changing it
skin-wide again.

## 5. Windows and dialogs

No `1080i/windows/` or `1080i/dialogs/` subfolders — those are only texture-path prefixes under
`media/`. All window/dialog XML sits flat in `1080i/` (122 files), grouped by purpose:

**Home / core nav** — `Home.xml`, `Includes_Home.xml`, `Includes_HomeCommons.xml`,
`Includes_HomeWidgets.xml`, `Custom_HomeSubmenuMovies.xml`, `Custom_HomeSubmenuTVShows.xml`,
`Custom_HomeSubmenuMusic.xml`, `Custom_HomeSubmenuLiveTV.xml`, `Custom_BounceLeftDummy.xml`,
`Custom_BounceRightDummy.xml`, `Pointer.xml`, `Startup.xml`, `LoginScreen.xml`.

**Video** — `MyVideoNav.xml`, `VideoFullScreen.xml`, `VideoOSD.xml`, `VideoOSDBookmarks.xml`,
`DialogVideoInfo.xml`, `DialogPlayerProcessInfo.xml`, `DialogSubtitles.xml`,
`ViewtypesVideos.xml`, `GameOSD.xml`, `MyGames.xml`, `DialogGameControllers.xml`,
`Custom_GameInfo.xml`.

**Music** — `MyMusicNav.xml`, `MyMusicPlaylistEditor.xml`, `MusicOSD.xml`,
`MusicVisualisation.xml`, `DialogMusicInfo.xml`, `Custom_MusicFullscreenEnabler.xml`,
`ViewtypesMusic.xml`, `script-cu-lrclyrics-main.xml`.

**Pictures** — `MyPics.xml`, `SlideShow.xml`, `DialogPictureInfo.xml`, `ViewtypesPictures.xml`.

**PVR / Live TV** — `MyPVRChannels.xml`, `MyPVRGuide.xml`, `MyPVRRecordings.xml`,
`MyPVRSearch.xml`, `MyPVRTimers.xml`, `DialogPVRChannelGuide.xml`,
`DialogPVRChannelManager.xml`, `DialogPVRChannelsOSD.xml`, `DialogPVRGroupManager.xml`,
`DialogPVRGuideSearch.xml`, `DialogPVRInfo.xml`, `DialogPVRRadioRDSInfo.xml`,
`Includes_PVR.xml`, `Includes_TVGuide.xml`, `Includes_GuideInterface.xml`.

**Programs / addons** — `MyPrograms.xml`, `AddonBrowser.xml`, `DialogAddonInfo.xml`,
`DialogAddonSettings.xml`, `ViewtypesPrograms.xml`, `ViewtypesAddons.xml`,
`script-globalsearch.xml`, `script-script.extendedinfo-DialogInfo.xml`,
`script-trakt-ContextMenu.xml`, `script-trakt-RatingDialog.xml`,
`script-videoextras-context.xml`, `script-videoextras-main.xml`,
`script-RSS_Editor-rssEditor.xml`, `script-RSS_Editor-setEditor.xml`, `Custom_RSS.xml`.

**Settings / skin config** — `Settings.xml`, `SettingsCategory.xml`, `SettingsProfile.xml`,
`SettingsScreenCalibration.xml`, `SettingsSystemInfo.xml`, `SkinSettings.xml`,
`Custom_SettingsDialog.xml`, `Custom_SettingsBackgroundDialog.xml`, `Custom_PanelDialog.xml`,
`Custom_LanguageDialog.xml`, `Includes_Settings.xml`, `Includes_SettingsCustomHomeItems.xml`,
`Includes_SettingsCustomHomeWidgets.xml`, `Includes_SettingsCustomGuideItems.xml`,
`Includes_DialogSettings.xml`.

**Generic/native dialogs** (standard Kodi set) — `DialogBusy.xml`, `DialogButtonMenu.xml`,
`DialogConfirm.xml`, `DialogContextMenu.xml`, `DialogExtendedProgressBar.xml`,
`DialogFullScreenInfo.xml`, `DialogKeyboard.xml`, `DialogMediaSource.xml`,
`DialogNotification.xml`, `DialogNumeric.xml`, `DialogSeekBar.xml`, `DialogSelect.xml`,
`DialogSettings.xml`, `DialogSlider.xml`, `DialogTextViewer.xml`, `DialogVolumeBar.xml`,
`EventLog.xml`, `FileBrowser.xml`, `FileManager.xml`, `PlayerControls.xml`, `MyFavourites.xml`,
`MyPlaylist.xml`, `MyWeather.xml`, `SmartPlaylistEditor.xml`, `SmartPlaylistRule.xml`,
`Includes_Keyboard.xml`, `Includes_OSD.xml`, `Includes_Weather.xml`,
`Includes_DialogConfirm.xml`, `Includes_Dialogs.xml`, `Includes_ContextMenu.xml`,
`Includes_Flags.xml`, `Includes_ViewHeader.xml`, `Includes_WindowContents.xml`,
`Includes_Animations.xml`, `Includes_Commons.xml`, `Font.xml`, `Defaults.xml`, `Includes.xml`.

Custom window ids (all `type="dialog"`, 3000-range to avoid Kodi's reserved core ids): `3001`
Custom_SettingsDialog, `3002` Custom_SettingsBackgroundDialog, `3003` Custom_PanelDialog, `3005`
Custom_RSS, `3006` Custom_LanguageDialog, `3008`/`3009` Bounce Left/Right Dummy, `3010`
Custom_MusicFullscreenEnabler, `3020`–`3023` the four Home submenus.

**RetroPlayer's savestate picker** (window name `gamesaves`, `CDialogGameSaves` in Kodi core,
launched when a game with existing saves is selected) renders through `DialogSelect.xml` like
everything else in the generic/native dialog list above — but it doesn't use the same control
ids as the rest of that shared layout (`DialogSelect`/`DialogSelectOSD`, control 3/6 etc). It
has its own fixed set: list `3` (the savestates, art via `ListItem.Art(screenshot)`), heading
`10820`, caption `10822`, emulator name/version/icon `10823`/`10828`/`10824`, New-game button
`10825`, Cancel button `10826` — all defined by Kodi core
(`xbmc/games/dialogs/DialogGameDefines.h`), not something the skin gets to renumber. The
skin originally had no layout at all for these ids, so `DialogSelect.xml`'s generic chrome
(gated on `Control.IsVisible(6)`, the detail-list layout meant for addon browsing) and this
window's own content drew on top of each other simultaneously — misaligned background,
double-drawn item counter, an orphaned "Author" panel from the addon-detail layout that has
no meaning here. Fixed with a **dedicated `DialogSelectGameSaves` include** in
`Includes_Dialogs.xml`, routed in `DialogSelect.xml` via
`<include condition="Window.IsActive(gamesaves)">DialogSelectGameSaves</include>` ahead of
the normal `DialogSelect`/`DialogSelectOSD` routing (which now both carry an added
`!Window.IsActive(gamesaves)` guard so they stop competing for the same window). The in-game
saves manager (opened from the game OSD mid-play, window `ingamesaves`) is a *different* Kodi
code path (`CDialogInGameSaves` extends `CDialogGameVideoSelect`, not
`CDialogGameSaves`/`DialogSelect.xml`) and was not covered by this fix — if it has similar
gaps, that's a separate investigation.

## 6. Colors & themes

`colors/defaults.xml` is the **only** color file (no `colors/flat/` subfolder, no multiple color
schemes). ~30 named colors as flat 8-hex-digit ARGB values:

```xml
<color name="black">FF000000</color>
<color name="white">FFFFFFFF</color>
<color name="homelabelbig">FFFFFFFF</color>
<color name="homelabelsmall">FF62BEFE</color>
<color name="MenuBlue">FF55B2FA</color>
<color name="MenuGrey">CC484848</color>
<color name="SettingsBlue">FF55b4e7</color>
<color name="DialogSelected">FF4ea1e7</color>
<color name="SelectedBlue">FF31D0FF</color>
<color name="77white">77FFFFFF</color>
```

Referenced by name in `<textcolor>`, `<shadowcolor>`, `[COLOR=Name]...[/COLOR]`. **Not
everything routes through this file** — plenty of XML uses raw inline hex
(`<textcolor>96FFFFFF</textcolor>`) directly; both patterns are normal in this codebase.

**"Theme" = texture theme, not color theme.** `themes/flat/` mirrors `media/`'s subfolder
layout — Kodi's native alternate-texture-set mechanism (Settings → Interface → Skin → skin
theme), not skin XML. It's the only theme folder present, so the theme picker effectively has
one option today. `media/` and `themes/flat/` are near-duplicate asset sets; `media/` is what
loads by default (texture paths are relative to it), `themes/flat/` is the packaged alternate
copy Kodi's theme system swaps in — per the upstream README, it's only selectable once textures
are compiled into an `.xbt` at release-package time. `.gitignore` excludes `*.xbt` — no packed
textures are committed, only loose PNGs.

## 7. Fonts

`1080i/Font.xml` defines one `<fontset id="Default">`. Two font families:

- **`OpenSansCond.ttf`** (Open Sans Condensed) — primary UI font, named
  **`Font-Condensed-S<size>`** / **`Font-Condensed-S<size>-B`** (bold), e.g.
  `Font-Condensed-S20`, `Font-Condensed-S25-B`, `Font-Condensed-S30-B`, up to
  `Font-Condensed-S100`. This is the naming convention used everywhere, e.g.
  `<font>Font-Condensed-S30-B</font>`.
- **`Roboto-Regular.ttf`/`Roboto-Bold.ttf`** and **`DejaVuSans-Bold-Caps.ttf`** — legacy
  Confluence-style names (`font10`, `font12`, `font13`, `font14`, `font16`, `font30`,
  `fontContextMenu`, `font10_title`…`font45caps_title`, `font_MainMenu`) kept so third-party
  addon UIs (which often hardcode Confluence font names) render sanely in this skin.
  `WeatherTemp` (Roboto-Bold, size 120) drives the big temperature display.

Font files live in `fonts/`. To add a new size: add a `<font>` block with a fresh
`Font-Condensed-S<size>[-B]` name to `Font.xml`, reference it by name in any control's
`<font>` tag.

## 8. Media / textures

`media/` is loose PNGs, not a packed `Textures.xbt` (`.gitignore` excludes `*.xbt` — packing
only happens at release time). Top-level `media/` has 10 subfolders plus ~90 root-level
`DefaultXxx.png` fallback icons matching Kodi's standard `Default*` naming convention.

| folder | contents |
|---|---|
| `media/buttons/` | Spin control / radio button / OSD button state textures (`osd`, `radio`, `spinctrl`). |
| `media/calibrate/` | Screen-calibration overlay graphics. |
| `media/dialogs/` | Per-dialog-type background/frame chrome (`addon-info`, `album-info`, `context`, `default`, `extendedinfo`, `extendedprogress`, `favourites`, `filebrowser`, `filestacking`, `keyboard`, `mediasource`, `music-info`, `notifications`, `options`, `other`). |
| `media/fade/` | Fullscreen fade/dim gradient textures. |
| `media/flags/` | Codec/resolution/MPAA/language/channel-count badge icons (`aspectratio`, `audio`, `audioosd`, `channels`, `defs`, `discnumber`, `fileextension`, `language`, `mpaa`, `other`, `res`, `video`). |
| `media/osd/` | Player/lyrics/media-guide OSD controls (`bookmarks`, `fullscreen`[+buttons,progress], `lyrics`[+buttons], `media-guide`[+buttons,settings,upnext]). |
| `media/overlays/` | List-item badges — watched/unwatched, mouse cursor, notifications, now-playing, scan spinner, volume (`addons`, `mouse`, `notification`, `nowplaying`[+progress], `scan`, `volume`[+progress], `OverlayWatched.png`/`OverlayUnwatched.png`). |
| `media/views/` | Panel/list/thumbnail chrome + per-media-type fallback art (`banner`[+diffuse,other], `extended`, `fallbacks`, `fanart`, `list`, `other`, `panel`, `posterview`, `pvr`, `thumb`). |
| `media/weather/` | Weather condition icons at multiple sizes (`home`, `medium`, `moon`, `small`). |
| `media/windows/` | Per-window background/decoration art (`common`, `filemanager`[+icons], `home`, `logon`, `pvr`, `settings`, `tvguide`). |

## 9. Language / strings

`language/` has 72 `resource.language.<locale>` subfolders (full modern Kodi locale set), each
containing one **`strings.po`** (gettext, not legacy `strings.xml`). `en_gb`
(`language/resource.language.en_gb/strings.po`) is the master locale; others are translated via
Transifex per the upstream README. To add a new skin string: add a `msgctxt "#3xxxx"` /
`msgid ""` / `msgstr "Your Text"` entry to `en_gb/strings.po`, reference it as `$LOCALIZE[3xxxx]`.

## 10. Build/dev tooling

No CI, no TexturePacker config, no build scripts anywhere in the skin's own tree — source-only,
loose PNGs loaded at runtime by Kodi directly. (This repo's own `tools/build.py` and
`.github/workflows/build.yml`, one level up, are what actually package and publish this skin —
see the top-level `README.md`.)

`.gitignore` (skin-specific) also flags: Sublime Text project files ignored (author develops in
Sublime Text), `*.psd` ignored (Photoshop source art not checked in), a defensive/unused
`script-skinshortcuts-includes.xml` line.

Dev loop for XML-only changes: edit, then use the skin's own **Reload Skin** action (Advanced
settings category, `<onclick>ReloadSkin</onclick>`) instead of reinstalling. A full version bump
+ push is what actually ships the change to a device automatically via this repo's pipeline.

**Upstream branch/version mapping** (from the original xperience1080 repo, read via
`.git/packed-refs` since multiple Kodi-version branches exist there):

| branch | Kodi version |
|---|---|
| `Helix` | Kodi 14 |
| `Isengard` | Kodi 15 |
| `Jarvis` | Kodi 16 |
| `Krypton` | Kodi 17 |
| `Leia` | Kodi 18 |
| `Nexus` | Kodi 19 |
| `matrix` | Kodi 19 (older/alt branch name, superseded) |
| `master` | current/active — Kodi 21 "Omega" |

No separate "Omega" branch — `master` **is** the Omega-era branch; recent versions advance in
place rather than branching per release. This copy tracks `master`.

## 11. `extras/`, `playlists/`, `resources/`

- **`extras/backgrounds/`** — 8 JPGs (`01.jpg`–`08.jpg`), default/fallback fanart offered in the
  background-picker settings dialog.
- **`extras/fade/`** — fade-percentage overlays (`5.png`, `10.png`, ... `90.png`) plus
  `blue.png`/`green.png` tints, for background dim/tint level pickers.
- **`extras/icons/`** — `home`/`launcher` subfolders, alternate home-tile icon packs.
- **`extras/weather/`** — weather-related extra assets.
- **`playlists/`** — 5 smart playlists (`.xsp`) powering home widgets: `ongoing_episodes.xsp`,
  `random_albums.xsp`, `random_songs.xsp`, `recommended_albums.xsp`, `spotlight_movies.xsp`
  (backs e.g. the Movies "Spotlight" widget row, group `502` in `Includes_Home.xml`).
- **`resources/`** — addon-store metadata: `icon.png`, `fanart.jpg`,
  `screenshots/screenshot00.png`…`screenshot16.png` (17 screenshots referenced in `addon.xml`'s
  `<assets>` block).
