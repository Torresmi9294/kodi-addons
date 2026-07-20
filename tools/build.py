#!/usr/bin/env python3
"""Build the Kodi repository data dir (zips/addons.xml, zips/addons.xml.md5, per-addon zips)
from the addon source folders at the repo root. Run from the repo root:

    python tools/build.py

Any top-level folder containing an addon.xml is treated as an addon. The .github,
tools, and zips folders are always skipped.
"""
import hashlib
import shutil
import xml.etree.ElementTree as ET
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
ZIPS_DIR = REPO_ROOT / 'zips'
SKIP_DIRS = {'.git', '.github', 'tools', 'zips'}


def find_addon_dirs():
    for entry in sorted(REPO_ROOT.iterdir()):
        if not entry.is_dir() or entry.name in SKIP_DIRS or entry.name.startswith('.'):
            continue
        if (entry / 'addon.xml').is_file():
            yield entry


def build_addon(addon_dir: Path) -> str:
    addon_xml_path = addon_dir / 'addon.xml'
    tree = ET.parse(addon_xml_path)
    root = tree.getroot()
    addon_id = root.get('id')
    version = root.get('version')

    out_dir = ZIPS_DIR / addon_id
    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    zip_base = out_dir / f'{addon_id}-{version}'
    shutil.make_archive(str(zip_base), 'zip', root_dir=addon_dir.parent, base_dir=addon_dir.name)

    shutil.copy2(addon_xml_path, out_dir / 'addon.xml')
    for asset in ('icon.png', 'fanart.jpg'):
        asset_path = addon_dir / asset
        if asset_path.is_file():
            shutil.copy2(asset_path, out_dir / asset)

    print(f'  built {addon_id} {version}')
    return addon_xml_path.read_text(encoding='utf-8').split('\n', 1)[1].strip()


def main():
    if ZIPS_DIR.exists():
        shutil.rmtree(ZIPS_DIR)
    ZIPS_DIR.mkdir()

    addon_blocks = []
    for addon_dir in find_addon_dirs():
        addon_blocks.append(build_addon(addon_dir))

    addons_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<addons>\n'
    addons_xml += '\n'.join(addon_blocks)
    addons_xml += '\n</addons>\n'

    addons_xml_path = ZIPS_DIR / 'addons.xml'
    addons_xml_path.write_text(addons_xml, encoding='utf-8')

    md5 = hashlib.md5(addons_xml_path.read_bytes()).hexdigest()
    (ZIPS_DIR / 'addons.xml.md5').write_text(md5, encoding='utf-8')

    print(f'Wrote {addons_xml_path} and addons.xml.md5 ({md5})')


if __name__ == '__main__':
    main()
