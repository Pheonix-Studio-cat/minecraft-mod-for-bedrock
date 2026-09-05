#!/usr/bin/env python3
"""Erzeugt die statische Add-On-Bibliothek fuer GitHub Pages nach site/.

Ausfuehren mit:
    python3 tools/build.py        # erst die .mcaddon-Dateien bauen
    python3 tools/build_site.py   # dann die Website

Alle Pfade in der Seite sind relativ, damit sie unter jedem Unterpfad
funktioniert (GitHub Pages liefert Projektseiten unter /<repo>/ aus).
"""
import datetime
import html
import json
import os
import shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
SITE = os.path.join(ROOT, "site")
MANIFEST = os.path.join(ROOT, "addons.json")

DISCLAIMER = ("NOT AN OFFICIAL MINECRAFT PRODUCT. "
              "NOT APPROVED BY OR ASSOCIATED WITH MOJANG OR MICROSOFT.")

STYLE = """
*, *::before, *::after { box-sizing: border-box; }

:root {
  --bg: #0f1115;
  --surface: #171a21;
  --surface-2: #1e222b;
  --border: #2a2f3a;
  --text: #e6e9ef;
  --muted: #98a1b0;
  --accent: #3fb8c8;
  --shadow: 0 1px 3px rgba(0,0,0,.45), 0 10px 30px rgba(0,0,0,.28);
  --radius: 14px;
}

@media (prefers-color-scheme: light) {
  :root {
    --bg: #f5f6f8;
    --surface: #ffffff;
    --surface-2: #eef0f4;
    --border: #dde1e8;
    --text: #14171d;
    --muted: #5b6472;
    --shadow: 0 1px 2px rgba(0,0,0,.05), 0 10px 30px rgba(20,23,29,.07);
  }
}

html { -webkit-text-size-adjust: 100%; }

body {
  margin: 0;
  background: var(--bg);
  color: var(--text);
  font: 16px/1.6 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
  overflow-x: hidden;
}

a { color: inherit; }

.wrap { max-width: 1040px; margin: 0 auto; padding: 0 20px; }

/* ---------------------------------------------------------- Kopfbereich */

.top {
  border-bottom: 1px solid var(--border);
  background: var(--surface);
  position: sticky;
  top: 0;
  z-index: 10;
}

.top .wrap {
  display: flex;
  align-items: center;
  gap: 14px;
  min-height: 60px;
  flex-wrap: wrap;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 650;
  letter-spacing: .02em;
  text-decoration: none;
}

.brand .mark {
  width: 26px; height: 26px;
  border-radius: 6px;
  background: linear-gradient(135deg, var(--accent), #7d5bd6);
  box-shadow: inset 0 0 0 1px rgba(255,255,255,.16);
  flex: none;
}

.top nav {
  margin-left: auto;
  display: flex;
  gap: 18px;
  font-size: 14px;
  color: var(--muted);
}

.top nav a { text-decoration: none; }
.top nav a:hover { color: var(--text); }

/* ------------------------------------------------------------------ Hero */

.hero { padding: 56px 0 34px; }

.hero h1 {
  margin: 0 0 12px;
  font-size: clamp(30px, 5.5vw, 46px);
  line-height: 1.12;
  letter-spacing: -.02em;
}

.hero p {
  margin: 0;
  max-width: 62ch;
  color: var(--muted);
  font-size: 17px;
}

.count {
  display: inline-block;
  margin-bottom: 16px;
  padding: 4px 11px;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--muted);
  font-size: 13px;
  letter-spacing: .03em;
}

/* ----------------------------------------------------------------- Suche */

.search {
  margin: 30px 0 6px;
  position: relative;
}

.search input {
  width: 100%;
  padding: 12px 16px;
  border-radius: 10px;
  border: 1px solid var(--border);
  background: var(--surface);
  color: var(--text);
  font: inherit;
  font-size: 15px;
}

.search input:focus {
  outline: 2px solid var(--accent);
  outline-offset: 1px;
  border-color: transparent;
}

/* ----------------------------------------------------------------- Karten */

.grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
  gap: 20px;
  padding: 22px 0 10px;
}

.card {
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  overflow: hidden;
  transition: transform .16s ease, border-color .16s ease;
}

.card:hover { transform: translateY(-2px); border-color: var(--card-accent, var(--accent)); }
.card[hidden] { display: none; }

.preview {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  flex-wrap: wrap;
  padding: 22px 16px;
  background:
    linear-gradient(135deg,
      color-mix(in srgb, var(--card-accent, var(--accent)) 22%, transparent),
      transparent 70%),
    var(--surface-2);
  min-height: 104px;
}

.card .preview { border-bottom: 1px solid var(--border); }

.preview.standalone {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  box-shadow: var(--shadow);
  min-height: 128px;
}

.preview img {
  width: 36px; height: 36px;
  image-rendering: pixelated;
  image-rendering: crisp-edges;
  filter: drop-shadow(0 2px 3px rgba(0,0,0,.35));
}

.card .body { padding: 18px; display: flex; flex-direction: column; gap: 10px; flex: 1; }

.card h2 { margin: 0; font-size: 19px; letter-spacing: -.01em; }
.card h2 a { text-decoration: none; }
.card h2 a:hover { color: var(--card-accent, var(--accent)); }

.card .tagline { margin: 0; color: var(--muted); font-size: 14.5px; flex: 1; }

.tags { display: flex; flex-wrap: wrap; gap: 6px; }

.tag {
  font-size: 12px;
  padding: 3px 9px;
  border-radius: 999px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  color: var(--muted);
}

.meta {
  display: flex;
  flex-wrap: wrap;
  gap: 6px 14px;
  font-size: 12.5px;
  color: var(--muted);
  border-top: 1px solid var(--border);
  padding-top: 12px;
}

.actions { display: flex; gap: 10px; flex-wrap: wrap; }

.btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  border-radius: 9px;
  border: 1px solid transparent;
  font-size: 14.5px;
  font-weight: 560;
  text-decoration: none;
  cursor: pointer;
}

.btn.primary {
  background: var(--card-accent, var(--accent));
  color: #0d0f13;
}

.btn.primary:hover { filter: brightness(1.08); }

.btn.ghost {
  border-color: var(--border);
  background: var(--surface-2);
  color: var(--text);
}

.btn.ghost:hover { border-color: var(--card-accent, var(--accent)); }

/* ------------------------------------------------------------- Abschnitte */

section.block { padding: 44px 0; border-top: 1px solid var(--border); margin-top: 40px; }
section.block h2 { margin: 0 0 6px; font-size: 24px; letter-spacing: -.015em; }
section.block > .wrap > p { color: var(--muted); margin-top: 0; }

ol.steps { margin: 22px 0 0; padding: 0; list-style: none; counter-reset: s; }

ol.steps li {
  counter-increment: s;
  position: relative;
  padding: 0 0 20px 46px;
  border-left: 2px solid var(--border);
  margin-left: 15px;
}

ol.steps li:last-child { border-left-color: transparent; padding-bottom: 0; }

ol.steps li::before {
  content: counter(s);
  position: absolute;
  left: -16px; top: -2px;
  width: 30px; height: 30px;
  display: grid; place-items: center;
  border-radius: 50%;
  background: var(--surface-2);
  border: 1px solid var(--border);
  font-size: 13px;
  font-weight: 650;
  color: var(--muted);
}

ol.steps strong { display: block; }
ol.steps span { color: var(--muted); font-size: 14.5px; }

.note {
  margin-top: 22px;
  padding: 14px 16px;
  border-radius: 10px;
  border: 1px solid var(--border);
  border-left: 3px solid var(--accent);
  background: var(--surface);
  font-size: 14.5px;
  color: var(--muted);
}

.note strong { color: var(--text); }

/* --------------------------------------------------------------- Detailseite */

.detail-head { padding: 40px 0 26px; }
.back { font-size: 14px; color: var(--muted); text-decoration: none; }
.back:hover { color: var(--text); }
.detail-head h1 { margin: 14px 0 8px; font-size: clamp(27px, 5vw, 38px); letter-spacing: -.02em; }
.detail-head .tagline { margin: 0 0 18px; color: var(--muted); font-size: 17px; }

.panel {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 22px;
  box-shadow: var(--shadow);
}

.split { display: grid; grid-template-columns: 1fr; gap: 20px; }

@media (min-width: 800px) {
  .split { grid-template-columns: 1.55fr 1fr; align-items: start; }
}

.facts { list-style: none; margin: 0; padding: 0; font-size: 14.5px; }

.facts li {
  display: flex;
  justify-content: space-between;
  gap: 14px;
  padding: 9px 0;
  border-bottom: 1px solid var(--border);
}

.facts li:last-child { border-bottom: 0; }
.facts .k { color: var(--muted); }
.facts .v { text-align: right; }

ul.features { margin: 0; padding-left: 20px; }
ul.features li { margin: 7px 0; }

/* -------------------------------------------------------------- Fusszeile */

footer {
  border-top: 1px solid var(--border);
  margin-top: 50px;
  padding: 30px 0 44px;
  font-size: 13.5px;
  color: var(--muted);
}

footer .disclaimer {
  font-weight: 650;
  letter-spacing: .02em;
  color: var(--text);
  margin: 0 0 10px;
}

footer p { margin: 6px 0; }
footer a { color: var(--accent); }

/* ------------------------------------------------------------- Rezepte */

.recipe-list {
  display: grid;
  gap: 16px;
  grid-template-columns: 1fr;
  align-items: start;   /* Karten wachsen mit ihrem Inhalt, statt auf
                           Zeilenhoehe gestreckt zu werden */
}

@media (min-width: 720px) {
  .recipe-list { grid-template-columns: repeat(2, 1fr); }
}

.recipe {
  display: flex;
  align-items: center;
  gap: 16px;
  /* kein flex-wrap: sonst rutscht das Ergebnis bei dreireihigen Rezepten
     in eine zweite Zeile und damit aus der Karte heraus */
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 16px;
  box-shadow: var(--shadow);
}

.bench {
  display: grid;
  grid-template-columns: repeat(3, 34px);
  grid-auto-rows: 34px;
  gap: 3px;
  padding: 5px;
  background: var(--surface-2);
  border: 1px solid var(--border);
  border-radius: 8px;
  flex: none;
}

/* Formlose Rezepte: eine Reihe nebeneinander, nicht untereinander. */
.bench.shapeless {
  grid-template-columns: none;
  grid-auto-flow: column;
  grid-auto-columns: 34px;
}

.cell {
  /* Feste Groesse: Rasterspuren allein reichten nicht, die Zellen wuchsen
     ueber ihre Spur hinaus und ragten aus dem Raster heraus. */
  width: 34px;
  height: 34px;
  min-width: 0;
  min-height: 0;
  border-radius: 5px;
  border: 1px solid var(--border);
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 700;
  color: #14171d;
  background: var(--bg);
}

.cell.blank { opacity: .35; }
.cell.filled { border-color: rgba(0,0,0,.25); }

.arrow { color: var(--muted); font-size: 20px; flex: none; }

.result {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;        /* erlaubt Umbruch im Namen statt Ueberlauf */
  flex: 1 1 auto;
}

.result .name { overflow-wrap: anywhere; }

.result img {
  width: 34px; height: 34px;
  image-rendering: pixelated;
  image-rendering: crisp-edges;
  flex: none;
}

.result .name { font-weight: 600; font-size: 15px; }

.result .count { color: var(--muted); font-size: 13px; }

.legend {
  display: flex;
  flex-wrap: wrap;
  gap: 8px 18px;
  margin-top: 24px;
  padding-top: 18px;
  border-top: 1px solid var(--border);
  font-size: 14px;
  color: var(--muted);
}

.legend span { display: inline-flex; align-items: center; gap: 7px; }

.swatch {
  width: 18px; height: 18px;
  border-radius: 4px;
  border: 1px solid rgba(0,0,0,.25);
  display: grid;
  place-items: center;
  font-size: 10px;
  font-weight: 700;
  color: #14171d;
}

.empty {
  padding: 44px;
  text-align: center;
  color: var(--muted);
  border: 1px dashed var(--border);
  border-radius: var(--radius);
}
"""

SEARCH_JS = """
(function () {
  var input = document.getElementById('q');
  var cards = Array.prototype.slice.call(document.querySelectorAll('.card'));
  var empty = document.getElementById('noresult');
  if (!input) return;
  input.addEventListener('input', function () {
    var q = input.value.trim().toLowerCase();
    var shown = 0;
    cards.forEach(function (card) {
      var match = !q || card.dataset.search.indexOf(q) !== -1;
      card.hidden = !match;
      if (match) shown++;
    });
    if (empty) empty.hidden = shown !== 0;
  });
})();
"""


# Zutaten: Kuerzel, Anzeigename und Farbe fuer die Rezeptraster.
# Es werden keine Minecraft-Texturen verwendet, nur eigene Farbfelder.
INGREDIENTS = {
    "minecraft:iron_ingot":   ("I", "Eisenbarren", "#d9dde2"),
    "minecraft:stick":        ("S", "Stock", "#b58c56"),
    "minecraft:redstone":     ("R", "Redstone", "#d05646"),
    "minecraft:glass":        ("G", "Glas", "#a9d9e8"),
    "minecraft:gunpowder":    ("P", "Schießpulver", "#9aa0a6"),
    "minecraft:string":       ("T", "Faden", "#e8e8e8"),
    "minecraft:coal":         ("C", "Kohle", "#6b6b6b"),
    "minecraft:glass_bottle": ("F", "Glasflasche", "#b9dccb"),
}


def read_pack_items(behavior_pack, resource_pack):
    """Sammelt id -> {icon, name} aus Item-Definitionen und Sprachdatei."""
    items = {}
    folder = os.path.join(ROOT, behavior_pack, "items")
    for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
        if not name.endswith(".json"):
            continue
        with open(os.path.join(folder, name), encoding="utf-8") as fh:
            doc = json.load(fh)
        block = doc.get("minecraft:item", {})
        ident = block.get("description", {}).get("identifier")
        icon = block.get("components", {}).get("minecraft:icon", {})
        if ident:
            items[ident] = {
                "icon": icon.get("texture") if isinstance(icon, dict) else icon,
                "name": ident,
            }

    lang = os.path.join(ROOT, resource_pack, "texts", "de_DE.lang")
    if os.path.exists(lang):
        with open(lang, encoding="utf-8") as fh:
            for line in fh:
                if "=" not in line:
                    continue
                key, value = line.rstrip("\n").split("=", 1)
                if key.startswith("item.") and key.endswith(".name"):
                    ident = key[len("item."):-len(".name")]
                    if ident in items:
                        items[ident]["name"] = value
    return items


def read_recipes(behavior_pack):
    """Liest alle Rezepte eines Behavior-Packs in einheitlicher Form."""
    folder = os.path.join(ROOT, behavior_pack, "recipes")
    recipes = []
    for name in sorted(os.listdir(folder)) if os.path.isdir(folder) else []:
        if not name.endswith(".json"):
            continue
        with open(os.path.join(folder, name), encoding="utf-8") as fh:
            doc = json.load(fh)

        shaped = doc.get("minecraft:recipe_shaped")
        if shaped:
            key = {k: v["item"] for k, v in shaped["key"].items()}
            grid = [[key.get(ch) for ch in row] for row in shaped["pattern"]]
            width = max(len(row) for row in grid)
            for row in grid:
                row.extend([None] * (width - len(row)))
            recipes.append({
                "kind": "shaped",
                "grid": grid,
                "result": shaped["result"]["item"],
                "count": shaped["result"].get("count", 1),
            })

        shapeless = doc.get("minecraft:recipe_shapeless")
        if shapeless:
            recipes.append({
                "kind": "shapeless",
                "items": [i["item"] for i in shapeless["ingredients"]],
                "result": shapeless["result"]["item"],
                "count": shapeless["result"].get("count", 1),
            })
    return recipes


def cell(item):
    if not item:
        return '<div class="cell blank"></div>'
    letter, label, color = INGREDIENTS.get(item, ("?", item, "#cccccc"))
    return ('<div class="cell filled" style="background:%s" title="%s">%s</div>'
            % (esc(color), esc(label), esc(letter)))


def recipe_block(recipe, items, depth):
    up = "../" * depth
    result = items.get(recipe["result"], {})
    icon = result.get("icon")
    image = ('<img src="%simg/%s/%s.png" alt="" width="34" height="34">'
             % (up, esc(recipe["_addon"]), esc(icon))) if icon else ""
    count = ('<span class="count">&times;%d</span>' % recipe["count"]
             if recipe["count"] > 1 else "")

    if recipe["kind"] == "shaped":
        cells = "".join(cell(i) for row in recipe["grid"] for i in row)
        columns = len(recipe["grid"][0])
        bench = ('<div class="bench" style="grid-template-columns:repeat(%d,34px)">%s</div>'
                 % (columns, cells))
    else:
        bench = ('<div class="bench shapeless">%s</div>'
                 % "".join(cell(i) for i in recipe["items"]))

    return ('<div class="recipe">%s<span class="arrow">&rarr;</span>'
            '<div class="result">%s<span><span class="name">%s</span> %s</span></div></div>'
            % (bench, image, esc(result.get("name", recipe["result"])), count))


def build_recipes_page(manifest, addon, generated):
    behavior = next((p for p in addon["packs"] if p.startswith("behavior_packs")), None)
    resource = next((p for p in addon["packs"] if p.startswith("resource_packs")), None)
    if not behavior or not resource:
        return None

    items = read_pack_items(behavior, resource)
    recipes = read_recipes(behavior)
    if not recipes:
        return None

    for recipe in recipes:
        recipe["_addon"] = addon["id"]

    shaped = [r for r in recipes if r["kind"] == "shaped"]
    shapeless = [r for r in recipes if r["kind"] == "shapeless"]

    used = set()
    for recipe in recipes:
        if recipe["kind"] == "shaped":
            used.update(i for row in recipe["grid"] for i in row if i)
        else:
            used.update(recipe["items"])

    legend = "".join(
        '<span><span class="swatch" style="background:%s">%s</span>%s</span>'
        % (esc(INGREDIENTS[i][2]), esc(INGREDIENTS[i][0]), esc(INGREDIENTS[i][1]))
        for i in sorted(used) if i in INGREDIENTS)

    sections = ""
    if shaped:
        sections += ('<h2 style="font-size:20px;margin:26px 0 4px">Werkbank</h2>'
                     '<p style="color:var(--muted);margin-top:0">'
                     'Die Anordnung muss stimmen. Leere Felder bleiben leer.</p>'
                     '<div class="recipe-list">%s</div>'
                     % "".join(recipe_block(r, items, 1) for r in shaped))
    if shapeless:
        sections += ('<h2 style="font-size:20px;margin:32px 0 4px">Formlos</h2>'
                     '<p style="color:var(--muted);margin-top:0">'
                     'Reihenfolge und Position sind egal.</p>'
                     '<div class="recipe-list">%s</div>'
                     % "".join(recipe_block(r, items, 1) for r in shapeless))

    body = """%s
<main class="wrap">
  <div class="detail-head">
    <a class="back" href="../addon/%s.html">&larr; %s</a>
    <h1>Rezepte</h1>
    <p class="tagline">Alle %d Rezepte von %s. Bewusst günstig gehalten.</p>
  </div>
  %s
  <div class="legend">%s</div>
  <p style="color:var(--muted);font-size:14px;margin-top:26px">
    Im Spiel gibt es dieselbe Liste per Befehl:
    <code>/scriptevent px:recipes</code>
  </p>
</main>
%s""" % (header(manifest, 1), esc(addon["id"]), esc(addon["name"]),
         len(recipes), esc(addon["name"]), sections, legend,
         footer(manifest, generated))

    return page("Rezepte – %s" % addon["name"],
                "Alle Crafting-Rezepte von %s" % addon["name"], body, depth=1)


def esc(value):
    return html.escape(str(value), quote=True)


def page(title, description, body, depth=0):
    up = "../" * depth
    return """<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%s</title>
<meta name="description" content="%s">
<meta name="color-scheme" content="dark light">
<link rel="stylesheet" href="%sstyle.css">
</head>
<body>
%s
</body>
</html>
""" % (esc(title), esc(description), up, body)


def header(manifest, depth):
    up = "../" * depth
    return """<header class="top"><div class="wrap">
  <a class="brand" href="%sindex.html"><span class="mark"></span>%s</a>
  <nav>
    <a href="%sindex.html#addons">Add-Ons</a>
    <a href="%sindex.html#install">Installation</a>
    <a href="%s" rel="noopener">Quellcode</a>
  </nav>
</div></header>""" % (up, esc(manifest["studio"]), up, up,
                      esc(manifest["repository"]))


def footer(manifest, generated):
    return """<footer><div class="wrap">
  <p class="disclaimer">%s</p>
  <p>%s &middot; Code und Assets unter MIT-Lizenz &middot;
     <a href="%s" rel="noopener">Quellcode auf GitHub</a></p>
  <p>Diese Seite sammelt keine Daten, setzt keine Cookies und bindet nichts von
     Dritten ein. Stand: %s</p>
</div></footer>""" % (esc(DISCLAIMER), esc(manifest["studio"]),
                      esc(manifest["repository"]), esc(generated))


def preview_images(addon, depth):
    up = "../" * depth
    textures = addon.get("preview", {}).get("textures", [])
    return "".join(
        '<img src="%simg/%s/%s.png" alt="" loading="lazy" width="40" height="40">'
        % (up, esc(addon["id"]), esc(name)) for name in textures)


def download_name(addon):
    return "%s-%s.mcaddon" % (addon["id"], addon["version"])


def size_kb(path):
    return "%.0f KB" % (os.path.getsize(path) / 1024)


def card(addon, depth, size):
    search = " ".join([addon["name"], addon["tagline"], addon["description"]]
                      + addon.get("tags", [])).lower()
    tags = "".join('<span class="tag">%s</span>' % esc(t)
                   for t in addon.get("tags", []))
    return """<article class="card" style="--card-accent:%s" data-search="%s">
  <div class="preview">%s</div>
  <div class="body">
    <h2><a href="addon/%s.html">%s</a></h2>
    <p class="tagline">%s</p>
    <div class="tags">%s</div>
    <div class="actions">
      <a class="btn primary" href="downloads/%s" download>Herunterladen</a>
      <a class="btn ghost" href="addon/%s.html">Details</a>
    </div>
    <div class="meta">
      <span>Version %s</span><span>Bedrock %s+</span><span>%s</span>
    </div>
  </div>
</article>""" % (esc(addon["accent"]), esc(search), preview_images(addon, depth),
                 esc(addon["id"]), esc(addon["name"]), esc(addon["tagline"]),
                 tags, esc(download_name(addon)), esc(addon["id"]),
                 esc(addon["version"]), esc(addon["minEngineVersion"]), esc(size))


def install_steps():
    steps = [
        ("Add-On herunterladen",
         "Die .mcaddon-Datei von dieser Seite laden."),
        ("Datei öffnen",
         "Doppelklick auf Windows, Antippen auf Android und iOS. "
         "Minecraft importiert Behavior- und Resource-Pack automatisch."),
        ("Packs in der Welt aktivieren",
         "Welt bearbeiten, dann unter Verhaltenspakete und Ressourcenpakete "
         "beide Teile des Add-Ons aktivieren."),
        ("Beta APIs einschalten",
         "In den Welteinstellungen unter Experimente. Add-Ons mit Skript-Logik "
         "laufen sonst nicht."),
    ]
    return "".join("<li><strong>%s</strong><span>%s</span></li>"
                   % (esc(t), esc(d)) for t, d in steps)


def build_index(manifest, sizes, generated):
    addons = manifest["addons"]
    if addons:
        cards = "".join(card(a, 0, sizes[a["id"]]) for a in addons)
        listing = ('<div class="grid">%s</div>'
                   '<div class="empty" id="noresult" hidden>'
                   'Kein Add-On passt zu dieser Suche.</div>' % cards)
        search = ('<div class="search"><input id="q" type="search" '
                  'placeholder="Add-Ons durchsuchen" '
                  'aria-label="Add-Ons durchsuchen"></div>')
    else:
        listing = '<div class="empty">Noch keine Add-Ons veröffentlicht.</div>'
        search = ""

    count = "%d Add-On%s verfügbar" % (len(addons), "" if len(addons) == 1 else "s")

    body = """%s
<main>
  <div class="wrap">
    <div class="hero">
      <span class="count">%s</span>
      <h1>%s</h1>
      <p>%s</p>
    </div>
    <div id="addons">%s%s</div>
  </div>

  <section class="block" id="install">
    <div class="wrap">
      <h2>Installation</h2>
      <p>Vier Schritte, danach sind die Gegenstände im Kreativinventar und craftbar.</p>
      <ol class="steps">%s</ol>
      <div class="note">
        <strong>Nichts zu sehen im Spiel?</strong> Fast immer fehlt eine der beiden
        Aktivierungen: das Ressourcenpaket oder die Beta APIs unter Experimente.
        Beides gilt pro Welt, nicht global.
      </div>
    </div>
  </section>
</main>
%s
<script>%s</script>""" % (header(manifest, 0), esc(count), esc(manifest["title"]),
                          esc(manifest["intro"]), search, listing,
                          install_steps(), footer(manifest, generated), SEARCH_JS)

    return page("%s – %s" % (manifest["title"], manifest["studio"]),
                manifest["tagline"], body, depth=0)


def build_detail(manifest, addon, size, generated):
    features = "".join("<li>%s</li>" % esc(f) for f in addon.get("features", []))
    tags = "".join('<span class="tag">%s</span>' % esc(t)
                   for t in addon.get("tags", []))
    beta = "erforderlich" if addon.get("requiresBetaApi") else "nicht nötig"

    body = """%s
<main class="wrap">
  <div class="detail-head">
    <a class="back" href="../index.html">&larr; Alle Add-Ons</a>
    <h1>%s</h1>
    <p class="tagline">%s</p>
    <div class="tags">%s</div>
  </div>

  <div class="preview standalone" style="--card-accent:%s">%s</div>

  <div class="split" style="--card-accent:%s;margin-top:20px">
    <div class="panel">
      <h2 style="margin-top:0;font-size:20px">Über dieses Add-On</h2>
      <p style="color:var(--muted)">%s</p>
      <h2 style="font-size:18px">Enthalten</h2>
      <ul class="features">%s</ul>
    </div>

    <div class="panel">
      <a class="btn primary" href="../downloads/%s" download
         style="width:100%%;justify-content:center">Herunterladen</a>
      <a class="btn ghost" href="../recipes/%s.html"
         style="width:100%%;justify-content:center;margin-top:10px">Rezepte ansehen</a>
      <ul class="facts" style="margin-top:18px">
        <li><span class="k">Version</span><span class="v">%s</span></li>
        <li><span class="k">Dateigröße</span><span class="v">%s</span></li>
        <li><span class="k">Minecraft</span><span class="v">Bedrock %s+</span></li>
        <li><span class="k">Beta APIs</span><span class="v">%s</span></li>
        <li><span class="k">Lizenz</span><span class="v">MIT</span></li>
        <li><span class="k">Preis</span><span class="v">kostenlos</span></li>
      </ul>
      <p style="font-size:13.5px;color:var(--muted);margin-bottom:0">
        Installationsanleitung auf der <a href="../index.html#install">Startseite</a>.
      </p>
    </div>
  </div>
</main>
%s""" % (header(manifest, 1), esc(addon["name"]), esc(addon["tagline"]), tags,
         esc(addon["accent"]), preview_images(addon, 1), esc(addon["accent"]),
         esc(addon["description"]), features, esc(download_name(addon)),
         esc(addon["id"]),
         esc(addon["version"]), esc(size), esc(addon["minEngineVersion"]),
         esc(beta), footer(manifest, generated))

    return page("%s – %s" % (addon["name"], manifest["studio"]),
                addon["tagline"], body, depth=1)


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(text)


def main():
    with open(MANIFEST, encoding="utf-8") as fh:
        manifest = json.load(fh)

    if os.path.isdir(SITE):
        shutil.rmtree(SITE)
    os.makedirs(SITE)

    # Verhindert, dass GitHub Pages die Seite durch Jekyll schleust.
    write(os.path.join(SITE, ".nojekyll"), "")
    write(os.path.join(SITE, "style.css"), STYLE)

    generated = datetime.date.today().isoformat()
    sizes = {}

    for addon in manifest["addons"]:
        source = os.path.join(DIST, download_name(addon))
        if not os.path.exists(source):
            raise SystemExit(
                "Fehlt: %s - bitte zuerst 'python3 tools/build.py' ausfuehren."
                % os.path.relpath(source, ROOT))
        target = os.path.join(SITE, "downloads", download_name(addon))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        shutil.copy2(source, target)
        sizes[addon["id"]] = size_kb(target)

        preview = addon.get("preview", {})
        pack = preview.get("pack")
        for name in preview.get("textures", []):
            src = os.path.join(ROOT, pack, "textures", "items", name + ".png")
            if not os.path.exists(src):
                raise SystemExit("Vorschaubild fehlt: %s" % src)

        # Alle Item-Texturen des Packs uebernehmen: die Vorschau braucht
        # einige, die Rezeptseite zeigt jedes Ergebnis mit seinem Icon.
        resource = next((x for x in addon["packs"]
                         if x.startswith("resource_packs")), None)
        if resource:
            source_dir = os.path.join(ROOT, resource, "textures", "items")
            target_dir = os.path.join(SITE, "img", addon["id"])
            os.makedirs(target_dir, exist_ok=True)
            for name in sorted(os.listdir(source_dir)):
                if name.endswith(".png"):
                    shutil.copy2(os.path.join(source_dir, name),
                                 os.path.join(target_dir, name))

        write(os.path.join(SITE, "addon", addon["id"] + ".html"),
              build_detail(manifest, addon, sizes[addon["id"]], generated))

        recipes_page = build_recipes_page(manifest, addon, generated)
        if recipes_page:
            write(os.path.join(SITE, "recipes", addon["id"] + ".html"), recipes_page)

    write(os.path.join(SITE, "index.html"),
          build_index(manifest, sizes, generated))

    files = sum(len(f) for _, _, f in os.walk(SITE))
    print("site/ erzeugt: %d Dateien, %d Add-On-Seite(n)"
          % (files, len(manifest["addons"])))


if __name__ == "__main__":
    main()
