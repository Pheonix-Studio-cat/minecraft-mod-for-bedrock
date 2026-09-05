#!/usr/bin/env python3
"""Prueft das Add-On auf Konsistenz, bevor es ins Spiel geht."""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "behavior_packs", "px_weapons_bp")
RP = os.path.join(ROOT, "resource_packs", "px_weapons_rp")

errors = []
checked = 0


def load(path):
    global checked
    with open(path) as fh:
        try:
            data = json.load(fh)
            checked += 1
            return data
        except json.JSONDecodeError as exc:
            errors.append("Ungueltiges JSON in %s: %s" % (path, exc))
            return None


def walk_json(root):
    for base, _, files in os.walk(root):
        for name in files:
            if name.endswith(".json"):
                yield os.path.join(base, name)


# 1) Alle JSON-Dateien parsen
docs = {}
for pack in (BP, RP):
    for path in walk_json(pack):
        docs[path] = load(path)

# 2) Items einsammeln
items = {}
for path, doc in docs.items():
    if isinstance(doc, dict) and "minecraft:item" in doc:
        desc = doc["minecraft:item"]["description"]
        items[desc["identifier"]] = (path, doc["minecraft:item"]["components"])

if not items:
    errors.append("Keine Items gefunden")

# 3) Icons muessen als PNG existieren und in item_texture.json stehen
atlas = docs.get(os.path.join(RP, "textures", "item_texture.json")) or {}
atlas_data = atlas.get("texture_data", {})
for ident, (path, components) in items.items():
    icon = components.get("minecraft:icon", {}).get("texture")
    if not icon:
        errors.append("%s hat kein minecraft:icon" % ident)
        continue
    if icon not in atlas_data:
        errors.append("%s: Textur '%s' fehlt in item_texture.json" % (ident, icon))
    png = os.path.join(RP, "textures", "items", icon + ".png")
    if not os.path.exists(png):
        errors.append("%s: PNG fehlt -> %s" % (ident, png))

for icon, entry in atlas_data.items():
    png = os.path.join(RP, entry["textures"] + ".png")
    if not os.path.exists(png):
        errors.append("item_texture.json verweist auf fehlendes PNG: %s" % png)

# 4) Rezepte pruefen
recipe_results = []
for path, doc in docs.items():
    if not isinstance(doc, dict):
        continue
    shaped = doc.get("minecraft:recipe_shaped")
    shapeless = doc.get("minecraft:recipe_shapeless")
    if shaped:
        pattern = shaped["pattern"]
        widths = {len(row) for row in pattern}
        if len(widths) != 1:
            errors.append("%s: Musterzeilen unterschiedlich lang %s" % (path, sorted(widths)))
        if len(pattern) > 3 or max(widths) > 3:
            errors.append("%s: Muster passt nicht in ein 3x3-Raster" % path)
        used = {ch for row in pattern for ch in row if ch != " "}
        defined = set(shaped["key"])
        if used - defined:
            errors.append("%s: Zeichen ohne Key: %s" % (path, sorted(used - defined)))
        if defined - used:
            errors.append("%s: Key ohne Verwendung: %s" % (path, sorted(defined - used)))
        recipe_results.append((path, shaped["result"]["item"]))
    if shapeless:
        if not shapeless["ingredients"]:
            errors.append("%s: Rezept ohne Zutaten" % path)
        recipe_results.append((path, shapeless["result"]["item"]))

for path, result in recipe_results:
    if result.startswith("px:") and result not in items:
        errors.append("%s: Ergebnis '%s' ist kein definiertes Item" % (path, result))

crafted = {r for _, r in recipe_results}
for ident in items:
    if ident not in crafted:
        errors.append("%s hat kein Crafting-Rezept" % ident)

# 5) Doppelte shapeless-Zutatenmengen wuerden sich gegenseitig blockieren
signatures = {}
for path, doc in docs.items():
    shapeless = doc.get("minecraft:recipe_shapeless") if isinstance(doc, dict) else None
    if not shapeless:
        continue
    sig = tuple(sorted(i["item"] for i in shapeless["ingredients"]))
    if sig in signatures:
        errors.append("Mehrdeutiges Rezept: %s und %s nutzen %s"
                      % (os.path.basename(path), os.path.basename(signatures[sig]), list(sig)))
    signatures[sig] = path

# 6) Sprachschluessel
for lang in ("de_DE", "en_US"):
    path = os.path.join(RP, "texts", lang + ".lang")
    if not os.path.exists(path):
        errors.append("Sprachdatei fehlt: %s" % path)
        continue
    with open(path) as fh:
        keys = {line.split("=", 1)[0] for line in fh if "=" in line}
    for ident in items:
        if "item.%s.name" % ident not in keys:
            errors.append("%s: Schluessel 'item.%s.name' fehlt" % (lang, ident))
    for key in ("pack.name", "pack.description"):
        if key not in keys:
            errors.append("%s: Schluessel '%s' fehlt" % (lang, key))

# 7) Manifeste: Abhaengigkeiten muessen sich gegenseitig treffen
bp_manifest = docs.get(os.path.join(BP, "manifest.json"))
rp_manifest = docs.get(os.path.join(RP, "manifest.json"))
if bp_manifest and rp_manifest:
    bp_uuid = bp_manifest["header"]["uuid"]
    rp_uuid = rp_manifest["header"]["uuid"]
    bp_deps = {d.get("uuid") for d in bp_manifest.get("dependencies", [])}
    rp_deps = {d.get("uuid") for d in rp_manifest.get("dependencies", [])}
    if rp_uuid not in bp_deps:
        errors.append("BP-Manifest verweist nicht auf das RP")
    if bp_uuid not in rp_deps:
        errors.append("RP-Manifest verweist nicht auf das BP")
    uuids = [bp_uuid, rp_uuid] + [m["uuid"] for m in bp_manifest["modules"]] \
        + [m["uuid"] for m in rp_manifest["modules"]]
    if len(set(uuids)) != len(uuids):
        errors.append("Doppelte UUIDs in den Manifesten")
    entry = [m for m in bp_manifest["modules"] if m["type"] == "script"]
    if entry:
        script = os.path.join(BP, entry[0]["entry"])
        if not os.path.exists(script):
            errors.append("Skript-Einstiegspunkt fehlt: %s" % script)

# 8) Entity: Client-Definition, Geometrie und Textur muessen zusammenpassen
client = docs.get(os.path.join(RP, "entity", "px_turret.entity.json"))
if client:
    desc = client["minecraft:client_entity"]["description"]
    geo_id = desc["geometry"]["default"]
    geo_doc = docs.get(os.path.join(RP, "models", "entity", "px_turret.geo.json")) or {}
    geo_ids = {g["description"]["identifier"] for g in geo_doc.get("minecraft:geometry", [])}
    if geo_id not in geo_ids:
        errors.append("Geometrie '%s' nicht gefunden (vorhanden: %s)" % (geo_id, sorted(geo_ids)))
    tex = os.path.join(RP, desc["textures"]["default"] + ".png")
    if not os.path.exists(tex):
        errors.append("Entity-Textur fehlt: %s" % tex)

for pack in (BP, RP):
    if not os.path.exists(os.path.join(pack, "pack_icon.png")):
        errors.append("pack_icon.png fehlt in %s" % pack)

print("%d JSON-Dateien geprueft, %d Items, %d Rezepte"
      % (checked, len(items), len(recipe_results)))
if errors:
    print("\nFEHLER (%d):" % len(errors))
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("Alles konsistent.")
