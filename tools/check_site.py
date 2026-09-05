#!/usr/bin/env python3
"""Prueft die erzeugte Website auf tote Links, fehlende Assets und Anker."""
import os
import re
import sys
from urllib.parse import urlparse, unquote

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITE = os.path.join(ROOT, "site")

REF = re.compile(r'(?:href|src)\s*=\s*"([^"]+)"')
ID = re.compile(r'\bid\s*=\s*"([^"]+)"')

errors = []
pages = []

for base, _, files in os.walk(SITE):
    for name in files:
        if name.endswith(".html"):
            pages.append(os.path.join(base, name))

if not pages:
    errors.append("Keine HTML-Seiten in site/ gefunden")

ids = {}
for page in pages:
    with open(page, encoding="utf-8") as fh:
        ids[page] = set(ID.findall(fh.read()))

checked = 0
for page in pages:
    with open(page, encoding="utf-8") as fh:
        content = fh.read()
    here = os.path.dirname(page)
    for ref in REF.findall(content):
        parsed = urlparse(ref)
        if parsed.scheme in ("http", "https", "mailto"):
            continue  # externe Links werden nicht aufgeloest
        checked += 1
        path, anchor = parsed.path, parsed.fragment
        if not path:
            if anchor and anchor not in ids[page]:
                errors.append("%s: Anker #%s existiert nicht auf derselben Seite"
                              % (os.path.relpath(page, ROOT), anchor))
            continue
        target = os.path.normpath(os.path.join(here, unquote(path)))
        if not os.path.exists(target):
            errors.append("%s: verweist auf fehlende Datei %s"
                          % (os.path.relpath(page, ROOT), ref))
            continue
        if not target.startswith(SITE):
            errors.append("%s: verweist aus site/ heraus: %s"
                          % (os.path.relpath(page, ROOT), ref))
            continue
        if anchor and target.endswith(".html") and anchor not in ids.get(target, set()):
            errors.append("%s: Anker #%s fehlt in %s"
                          % (os.path.relpath(page, ROOT), anchor,
                             os.path.relpath(target, ROOT)))

    if ref_absolute := [r for r in REF.findall(content)
                        if r.startswith("/") and not r.startswith("//")]:
        errors.append("%s: absolute Pfade funktionieren unter /<repo>/ nicht: %s"
                      % (os.path.relpath(page, ROOT), ref_absolute))

    for required in ("<!doctype html>", '<html lang="de">', "<title>", "viewport"):
        if required not in content.lower() and required not in content:
            errors.append("%s: '%s' fehlt" % (os.path.relpath(page, ROOT), required))

if not os.path.exists(os.path.join(SITE, ".nojekyll")):
    errors.append(".nojekyll fehlt - GitHub Pages wuerde die Seite durch Jekyll schleusen")

downloads = os.path.join(SITE, "downloads")
if not os.path.isdir(downloads) or not os.listdir(downloads):
    errors.append("Keine Downloads in site/downloads/")

print("%d Seite(n), %d interne Verweise geprueft" % (len(pages), checked))
if errors:
    print("\nFEHLER (%d):" % len(errors))
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("Alle Verweise loesen auf.")
