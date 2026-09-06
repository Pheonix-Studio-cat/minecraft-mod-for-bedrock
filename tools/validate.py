#!/usr/bin/env python3
"""Prueft alle Add-Ons des Katalogs auf Konsistenz, bevor sie ins Spiel gehen.

Ausfuehren mit:  python3 tools/validate.py

Die Pruefungen richten sich nach addons.json. Ein neues Add-On wird damit
automatisch mitgeprueft, sobald es dort eingetragen ist.
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "addons.json")

errors = []
notes = []

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ingredients import LETTER  # noqa: E402


def fail(message):
    errors.append(message)


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        fail("Datei fehlt: %s" % os.path.relpath(path, ROOT))
    except json.JSONDecodeError as exc:
        fail("Ungueltiges JSON in %s: %s" % (os.path.relpath(path, ROOT), exc))
    return None


def walk_json(root):
    for base, _, files in os.walk(root):
        for name in sorted(files):
            if name.endswith(".json"):
                yield os.path.join(base, name)


def read_lang(path):
    with open(path, encoding="utf-8") as fh:
        return dict(line.rstrip("\n").split("=", 1) for line in fh if "=" in line)


# ---------------------------------------------------------------------------
# Katalog
# ---------------------------------------------------------------------------

library = load(MANIFEST) or {}
if not isinstance(library, dict):
    print("addons.json ist kein Objekt")
    sys.exit(1)

for key in ("studio", "title", "tagline", "intro", "repository", "addons"):
    if key not in library:
        fail("addons.json: Feld '%s' fehlt" % key)

seen_ids = set()
total_json = 0


def check_addon(addon):
    """Prueft ein einzelnes Add-On aus dem Katalog."""
    global total_json
    name = addon.get("id", "<ohne id>")
    tag = "addons.json/%s" % name

    for key in ("id", "name", "tagline", "description", "version",
                "minEngineVersion", "accent", "packs"):
        if key not in addon:
            fail("%s: Feld '%s' fehlt" % (tag, key))
    if addon.get("id") in seen_ids:
        fail("addons.json: doppelte id '%s'" % name)
    seen_ids.add(addon.get("id"))

    accent = addon.get("accent", "")
    if not (isinstance(accent, str) and accent.startswith("#") and len(accent) in (4, 7)):
        fail("%s: 'accent' ist keine Hex-Farbe (%r)" % (tag, accent))

    version = str(addon.get("version", "0.0.0"))
    if len(version.split(".")) != 3:
        fail("%s: 'version' erwartet x.y.z (%r)" % (tag, version))

    behavior = next((p for p in addon.get("packs", [])
                     if p.startswith("behavior_packs")), None)
    resource = next((p for p in addon.get("packs", [])
                     if p.startswith("resource_packs")), None)
    if not behavior or not resource:
        fail("%s: braucht je ein Behavior- und ein Resource-Pack" % tag)
        return

    BP = os.path.join(ROOT, behavior)
    RP = os.path.join(ROOT, resource)
    for pack in (BP, RP):
        if not os.path.isdir(pack):
            fail("%s: Ordner fehlt -> %s" % (tag, os.path.relpath(pack, ROOT)))
            return

    # --- alle JSON-Dateien parsen -----------------------------------------
    docs = {}
    for pack in (BP, RP):
        for path in walk_json(pack):
            docs[path] = load(path)
            total_json += 1

    # --- Manifeste ---------------------------------------------------------
    bp_manifest = docs.get(os.path.join(BP, "manifest.json"))
    rp_manifest = docs.get(os.path.join(RP, "manifest.json"))
    if not (isinstance(bp_manifest, dict) and isinstance(rp_manifest, dict)):
        fail("%s: Manifest fehlt oder ist ungueltig" % tag)
        return

    wanted = [int(x) for x in version.split(".")]
    uuids = []
    for manifest, pack, label in ((bp_manifest, BP, "Behavior-Pack"),
                                  (rp_manifest, RP, "Resource-Pack")):
        if manifest["header"]["version"] != wanted:
            fail("%s/%s: Manifest-Version %s passt nicht zum Katalog (%s)"
                 % (tag, label, manifest["header"]["version"], wanted))
        uuids.append(manifest["header"]["uuid"])
        uuids.extend(m["uuid"] for m in manifest["modules"])

    if rp_manifest["header"]["uuid"] not in {d.get("uuid") for d in bp_manifest.get("dependencies", [])}:
        fail("%s: Behavior-Pack verweist nicht auf das Resource-Pack" % tag)
    if bp_manifest["header"]["uuid"] not in {d.get("uuid") for d in rp_manifest.get("dependencies", [])}:
        fail("%s: Resource-Pack verweist nicht auf das Behavior-Pack" % tag)
    if len(set(uuids)) != len(uuids):
        fail("%s: doppelte UUIDs in den Manifesten" % tag)

    script = None
    for module in bp_manifest["modules"]:
        if module["type"] == "script":
            script = os.path.join(BP, module["entry"])
            if not os.path.exists(script):
                fail("%s: Skript-Einstiegspunkt fehlt -> %s" % (tag, module["entry"]))
                script = None

    for pack in (BP, RP):
        if not os.path.exists(os.path.join(pack, "pack_icon.png")):
            fail("%s: pack_icon.png fehlt in %s"
                 % (tag, os.path.relpath(pack, ROOT)))

    # --- Sprachdateien und Paketnamen --------------------------------------
    descriptions = {}
    for manifest, pack, label in ((bp_manifest, BP, "Behavior-Pack"),
                                  (rp_manifest, RP, "Resource-Pack")):
        declared = manifest["header"].get("name", "")
        for lang in ("de_DE", "en_US"):
            path = os.path.join(pack, "texts", lang + ".lang")
            if not os.path.exists(path):
                fail("%s/%s: %s.lang fehlt - die Paketliste zeigt sonst den "
                     "rohen Schluessel '%s'" % (tag, label, lang, declared))
                continue
            entries = read_lang(path)
            if declared.startswith("pack.") and declared not in entries:
                fail("%s/%s/%s: Manifest verweist auf '%s', der Schluessel fehlt"
                     % (tag, label, lang, declared))
            pack_name = entries.get("pack.name", "")
            if pack_name and version not in pack_name:
                fail("%s/%s/%s: Paketname '%s' enthaelt die Version %s nicht"
                     % (tag, label, lang, pack_name, version))
            if "pack.description" not in entries:
                fail("%s/%s/%s: 'pack.description' fehlt" % (tag, label, lang))
            if lang == "de_DE":
                descriptions[label] = entries.get("pack.description", "")

    if len(descriptions) == 2 and len(set(descriptions.values())) == 1:
        fail("%s: Behavior- und Resource-Pack haben dieselbe Beschreibung" % tag)

    # --- Inhalte: Items und Bloecke ----------------------------------------
    contents = {}          # id -> (Art, Textur-Kurzname)
    for path, doc in docs.items():
        if not isinstance(doc, dict):
            continue
        if "minecraft:item" in doc:
            entry = doc["minecraft:item"]
            ident = entry["description"]["identifier"]
            raw = entry["components"].get("minecraft:icon")
            icon = raw if isinstance(raw, str) else (raw or {}).get("texture")
            if not icon:
                fail("%s: %s hat kein minecraft:icon" % (tag, ident))
            contents[ident] = ("item", icon)
        if "minecraft:block" in doc:
            entry = doc["minecraft:block"]
            ident = entry["description"]["identifier"]
            material = entry["components"].get("minecraft:material_instances", {})
            texture = next((i.get("texture") for i in material.values()
                            if isinstance(i, dict) and i.get("texture")), None)
            if not texture:
                fail("%s: %s hat keine Textur in minecraft:material_instances"
                     % (tag, ident))
            contents[ident] = ("block", texture)

            geometry = entry["components"].get("minecraft:geometry")
            if geometry:
                found = False
                for geo_path in walk_json(os.path.join(RP, "models")):
                    geo = docs.get(geo_path) or load(geo_path)
                    for shape in (geo or {}).get("minecraft:geometry", []):
                        if shape["description"]["identifier"] == geometry:
                            found = True
                if not found:
                    fail("%s: %s verweist auf Geometrie '%s', die es nicht gibt"
                         % (tag, ident, geometry))

    if not contents:
        fail("%s: weder Items noch Bloecke gefunden" % tag)

    # --- Texturatlanten ----------------------------------------------------
    atlases = {}
    for atlas_name, folder in (("item_texture.json", "items"),
                               ("terrain_texture.json", "blocks")):
        path = os.path.join(RP, "textures", atlas_name)
        if os.path.exists(path):
            data = docs.get(path) or load(path) or {}
            for short, entry in data.get("texture_data", {}).items():
                atlases[short] = entry["textures"]
                png = os.path.join(RP, entry["textures"] + ".png")
                if not os.path.exists(png):
                    fail("%s: %s verweist auf fehlendes PNG %s"
                         % (tag, atlas_name, os.path.relpath(png, ROOT)))

    for ident, (kind, texture) in contents.items():
        if texture and texture not in atlases:
            fail("%s: %s nutzt Textur '%s', die in keinem Atlas steht"
                 % (tag, ident, texture))

    # --- Namen fuer jeden Inhalt ------------------------------------------
    for lang in ("de_DE", "en_US"):
        path = os.path.join(RP, "texts", lang + ".lang")
        if not os.path.exists(path):
            continue
        keys = set(read_lang(path))
        for ident, (kind, _) in contents.items():
            prefix = "tile." if kind == "block" else "item."
            if "%s%s.name" % (prefix, ident) not in keys:
                fail("%s/%s: Schluessel '%s%s.name' fehlt"
                     % (tag, lang, prefix, ident))

    # --- Rezepte -----------------------------------------------------------
    crafted = set()
    signatures = {}
    recipe_strings = []
    for path, doc in docs.items():
        if not isinstance(doc, dict):
            continue

        shaped = doc.get("minecraft:recipe_shaped")
        if shaped:
            pattern = shaped["pattern"]
            widths = {len(row) for row in pattern}
            if len(widths) != 1:
                fail("%s: %s Musterzeilen unterschiedlich lang %s"
                     % (tag, os.path.basename(path), sorted(widths)))
            if len(pattern) > 3 or max(widths) > 3:
                fail("%s: %s passt nicht in ein 3x3-Raster"
                     % (tag, os.path.basename(path)))
            used = {ch for row in pattern for ch in row if ch != " "}
            defined = set(shaped["key"])
            if used - defined:
                fail("%s: %s Zeichen ohne Key %s"
                     % (tag, os.path.basename(path), sorted(used - defined)))
            if defined - used:
                fail("%s: %s Key ohne Verwendung %s"
                     % (tag, os.path.basename(path), sorted(defined - used)))
            if not shaped.get("unlock"):
                fail("%s: %s 'unlock' fehlt - Rezept bleibt im Spiel gesperrt"
                     % (tag, os.path.basename(path)))
            crafted.add(shaped["result"]["item"])

            key = {k: v["item"] for k, v in shaped["key"].items()}
            rows = []
            for row in pattern:
                rows.append("".join("_" if ch == " " else LETTER.get(key[ch], "?")
                                    for ch in row))
            recipe_strings.append((os.path.basename(path), " / ".join(rows)))
            for item in key.values():
                if item not in LETTER:
                    fail("Kein Kuerzel fuer '%s' in tools/validate.py" % item)

        shapeless = doc.get("minecraft:recipe_shapeless")
        if shapeless:
            if not shapeless["ingredients"]:
                fail("%s: %s Rezept ohne Zutaten" % (tag, os.path.basename(path)))
            if not shapeless.get("unlock"):
                fail("%s: %s 'unlock' fehlt - Rezept bleibt im Spiel gesperrt"
                     % (tag, os.path.basename(path)))
            crafted.add(shapeless["result"]["item"])
            signature = tuple(sorted(i["item"] for i in shapeless["ingredients"]))
            if signature in signatures:
                fail("%s: mehrdeutiges Rezept, %s und %s nutzen %s"
                     % (tag, os.path.basename(path), signatures[signature],
                        list(signature)))
            signatures[signature] = os.path.basename(path)
            letters = [LETTER.get(i["item"], "?") for i in shapeless["ingredients"]]
            recipe_strings.append((os.path.basename(path), " + ".join(letters)))
            for ingredient in shapeless["ingredients"]:
                if ingredient["item"] not in LETTER:
                    fail("Kein Kuerzel fuer '%s' in tools/validate.py"
                         % ingredient["item"])

    for ident in contents:
        if ident not in crafted:
            fail("%s: %s hat kein Crafting-Rezept" % (tag, ident))

    # --- Rezepthilfe im Skript --------------------------------------------
    if script:
        with open(script, encoding="utf-8") as fh:
            code = fh.read()
        if "world.sendMessage" not in code:
            fail("%s: Skript hat keine Startmeldung - Diagnose im Spiel unmoeglich"
                 % tag)
        for filename, wanted_string in recipe_strings:
            if wanted_string not in code:
                fail("%s: Rezepthilfe im Skript weicht ab, %s erwartet '%s'"
                     % (tag, filename, wanted_string))

    # --- Texturliste -------------------------------------------------------
    listing = os.path.join(RP, "textures", "textures_list.json")
    if not os.path.exists(listing):
        fail("%s: textures/textures_list.json fehlt" % tag)
    else:
        listed = set(docs.get(listing) or load(listing) or [])
        actual = set()
        for base, _, files in os.walk(os.path.join(RP, "textures")):
            for filename in files:
                if filename.endswith(".png"):
                    rel = os.path.relpath(os.path.join(base, filename), RP)
                    actual.add(rel.replace(os.sep, "/")[:-4])
        for missing in sorted(actual - listed):
            fail("%s: textures_list.json fuehrt '%s' nicht auf" % (tag, missing))
        for stale in sorted(listed - actual):
            fail("%s: textures_list.json nennt '%s', die Datei fehlt" % (tag, stale))

    # --- HUD-Ueberlagerung, falls vorhanden --------------------------------
    hud = os.path.join(RP, "ui", "hud_screen.json")
    if os.path.exists(hud):
        for node in (docs.get(hud) or load(hud) or {}).values():
            if isinstance(node, dict) and node.get("type") == "image":
                declared = node.get("size")
                png = os.path.join(RP, node.get("texture", "") + ".png")
                if declared and os.path.exists(png):
                    with open(png, "rb") as fh:
                        head = fh.read(24)
                    width = int.from_bytes(head[16:20], "big")
                    height = int.from_bytes(head[20:24], "big")
                    if declared != [width, height]:
                        fail("%s: hud_screen.json gibt %s an, die Textur ist %dx%d"
                             % (tag, declared, width, height))

    # --- Vorschaubilder fuer die Website -----------------------------------
    preview = addon.get("preview", {})
    if preview:
        pack = preview.get("pack")
        if pack not in addon.get("packs", []):
            fail("%s: preview.pack '%s' steht nicht in 'packs'" % (tag, pack))
        folder = preview.get("folder", "items")
        for texture in preview.get("textures", []):
            png = os.path.join(ROOT, pack or "", "textures", folder, texture + ".png")
            if not os.path.exists(png):
                fail("%s: Vorschaubild fehlt -> %s" % (tag, os.path.relpath(png, ROOT)))

    doc_path = addon.get("docs")
    if doc_path and not os.path.exists(os.path.join(ROOT, doc_path)):
        fail("%s: 'docs' zeigt auf %s - nicht vorhanden" % (tag, doc_path))

    notes.append("  %-16s %2d Inhalte, %2d Rezepte, Version %s"
                 % (addon.get("id"), len(contents), len(recipe_strings), version))


for entry in library.get("addons", []):
    check_addon(entry)

print("%d Add-On(s), %d JSON-Dateien geprueft" % (len(library.get("addons", [])), total_json))
for line in notes:
    print(line)

if errors:
    print("\nFEHLER (%d):" % len(errors))
    for e in errors:
        print("  -", e)
    sys.exit(1)
print("Alles konsistent.")
