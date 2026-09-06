#!/usr/bin/env python3
"""Packt jedes in addons.json eingetragene Add-On zu einer .mcaddon-Datei.

Ausfuehren mit:  python3 tools/build.py
Ergebnis liegt in dist/ und laesst sich auf Windows/Android/iOS direkt oeffnen.
"""
import json
import os
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
MANIFEST = os.path.join(ROOT, "addons.json")
SKIP = {".DS_Store", "Thumbs.db"}


def load_manifest():
    with open(MANIFEST) as fh:
        return json.load(fh)


def filename(addon):
    return "%s-%s.mcaddon" % (addon["id"], addon["version"])


def build(addon):
    target = os.path.join(DIST, filename(addon))
    count = 0
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as archive:
        for pack in addon["packs"]:
            root = os.path.join(ROOT, pack)
            if not os.path.isdir(root):
                raise SystemExit("Pack-Ordner fehlt: %s" % pack)
            # Ordnername traegt die Version: so ueberschreiben sich zwei
            # Fassungen bei manueller Installation nach com.mojang nicht.
            top = "%s-%s" % (os.path.basename(pack.rstrip("/")), addon["version"])
            for base, _, files in os.walk(root):
                for name in sorted(files):
                    if name in SKIP:
                        continue
                    full = os.path.join(base, name)
                    rel = os.path.relpath(full, root)
                    archive.write(full, os.path.join(top, rel))
                    count += 1
    return target, count, os.path.getsize(target)


def main():
    os.makedirs(DIST, exist_ok=True)
    manifest = load_manifest()
    for addon in manifest["addons"]:
        target, count, size = build(addon)
        print("%-34s %3d Dateien  %7.1f KB"
              % (os.path.relpath(target, ROOT), count, size / 1024))
    print("%d Add-On(s) gebaut." % len(manifest["addons"]))


if __name__ == "__main__":
    main()
