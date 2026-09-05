#!/usr/bin/env python3
"""Packt Behavior- und Resource-Pack zu dist/PX_Weapons.mcaddon.

Ausfuehren mit:  python3 tools/build.py
Die entstandene Datei laesst sich auf Windows/Android/iOS direkt oeffnen und
importiert beide Packs in Minecraft Bedrock.
"""
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
PACKS = ["behavior_packs/px_weapons_bp", "resource_packs/px_weapons_rp"]
SKIP = {".DS_Store", "Thumbs.db"}


def main():
    os.makedirs(DIST, exist_ok=True)
    target = os.path.join(DIST, "PX_Weapons.mcaddon")
    count = 0
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for pack in PACKS:
            root = os.path.join(ROOT, pack)
            top = os.path.basename(pack)
            for base, _, files in os.walk(root):
                for name in sorted(files):
                    if name in SKIP:
                        continue
                    full = os.path.join(base, name)
                    rel = os.path.relpath(full, root)
                    archive.write(full, os.path.join(top, rel))
                    count += 1
    size = os.path.getsize(target)
    print("%s (%d Dateien, %.1f KB)" % (os.path.relpath(target, ROOT), count, size / 1024))


if __name__ == "__main__":
    main()
