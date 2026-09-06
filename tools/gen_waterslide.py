#!/usr/bin/env python3
"""Erzeugt das Wasserrutschen-Add-On: Bloecke, Modelle, Texturen, Rezepte.

Ausfuehren mit:  python3 tools/gen_waterslide.py
"""
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from gen_textures import write_png  # noqa: E402  eigener PNG-Encoder

BP = os.path.join(ROOT, "behavior_packs", "px_waterslide_bp")
RP = os.path.join(ROOT, "resource_packs", "px_waterslide_rp")

BLOCK_FORMAT = "1.21.60"
RECIPE_FORMAT = "1.20.10"

# name, geometrie, textur, deutsch, englisch
BLOCKS = [
    ("slide_straight", "straight", "px_slide",       "Rutsche gerade",   "Slide Straight"),
    ("slide_curve",    "curve",    "px_slide",       "Rutsche Kurve",    "Slide Curve"),
    ("slide_slope",    "slope",    "px_slide",       "Rutsche Gefälle",  "Slide Slope"),
    ("slide_tube",     "tube",     "px_slide",       "Rutschen-Röhre",   "Slide Tube"),
    ("slide_booster",  "straight", "px_slide_boost", "Beschleuniger",    "Booster"),
    ("slide_end",      "straight", "px_slide_end",   "Auslauf",          "Slide End"),
]

GLASS = "minecraft:glass"
RECIPES = {
    # Muster, Zutaten je Buchstabe, Stueckzahl
    "slide_straight": (["G G", "GGG"], {"G": GLASS}, 6),
    "slide_curve":    (["G G", "GDG"], {"G": GLASS, "D": "minecraft:blue_dye"}, 4),
    "slide_slope":    (["G G", "GAG"], {"G": GLASS, "A": "minecraft:sand"}, 4),
    "slide_tube":     (["GGG", "G G", "GGG"], {"G": GLASS}, 4),
    "slide_booster":  (["G G", "GRG"], {"G": GLASS, "R": "minecraft:redstone"}, 2),
    "slide_end":      (["G G", "GLG"], {"G": GLASS, "L": "minecraft:clay_ball"}, 4),
}

DIRECTIONS = [("north", 0), ("east", 90), ("south", 180), ("west", 270)]


def dump(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, indent=2, ensure_ascii=False)
        fh.write("\n")


def pack_version():
    with open(os.path.join(BP, "manifest.json")) as fh:
        return ".".join(str(n) for n in json.load(fh)["header"]["version"])


# --------------------------------------------------------------- Texturen

def slide_texture(accent=None):
    """Wasserblaue Rinne mit helleren Streifen; optional ein Akzentmuster.

    accent "boost" zeichnet gelbe Pfeilspitzen in Fliessrichtung,
    accent "end" rot-weisse Warnstreifen.
    """
    size = 16
    rows = []
    for y in range(size):
        row = []
        for x in range(size):
            # Grundton: nach unten hin etwas dunkler, mit Laengsstreifen
            base = 190 - y * 3
            streak = 18 if x % 5 == 2 else 0
            r, g, b = 60 + streak // 2, base - 40 + streak, base + 20 + streak

            if accent == "boost" and (y + x // 2) % 8 in (0, 1):
                r, g, b = 232, 197, 71          # gelbe Pfeilspitze
            elif accent == "end" and (x + y) % 8 < 4 and y % 4 < 2:
                r, g, b = 192, 57, 43           # rote Warnstreifen
            elif accent == "end" and y % 4 >= 2:
                r, g, b = 226, 228, 232

            row.append((max(0, min(255, r)), max(0, min(255, g)),
                        max(0, min(255, b)), 255))
        rows.append(row)
    return size, rows


def build_textures():
    variants = {"px_slide": None, "px_slide_boost": "boost", "px_slide_end": "end"}
    for name, accent in variants.items():
        size, rows = slide_texture(accent)
        write_png(os.path.join(RP, "textures", "blocks", name + ".png"), size, size, rows)

    dump(os.path.join(RP, "textures", "terrain_texture.json"), {
        "resource_pack_name": "px_waterslide",
        "texture_name": "atlas.terrain",
        "padding": 8,
        "num_mip_levels": 4,
        "texture_data": {
            name: {"textures": "textures/blocks/" + name} for name in variants
        },
    })

    # Pack-Icons im Stil des Add-Ons
    size, rows = slide_texture()
    icon = [[rows[y * size // 64][x * size // 64] for x in range(64)] for y in range(64)]
    for pack in (BP, RP):
        write_png(os.path.join(pack, "pack_icon.png"), 64, 64, icon)

    paths = []
    for base, _, files in os.walk(os.path.join(RP, "textures")):
        for name in sorted(files):
            if name.endswith(".png"):
                rel = os.path.relpath(os.path.join(base, name), RP)
                paths.append(rel.replace(os.sep, "/")[:-4])
    dump(os.path.join(RP, "textures", "textures_list.json"), sorted(paths))
    return len(variants)


# --------------------------------------------------------------- Modelle

def cube(origin, size, uv=(0, 0)):
    return {"origin": list(origin), "size": list(size), "uv": list(uv)}


# Eine Rinne: Boden plus zwei Seitenwaende. Offen nach oben und in
# Laufrichtung (Nord-Sued), damit sich Teile aneinanderreihen lassen.
FLOOR = cube((-8, 0, -8), (16, 2, 16))
WALL_WEST = cube((-8, 2, -8), (2, 7, 16), (0, 4))
WALL_EAST = cube((6, 2, -8), (2, 7, 16), (0, 4))

GEOMETRIES = {
    # gerade Rinne
    "straight": [{"name": "slide", "pivot": [0, 0, 0],
                  "cubes": [FLOOR, WALL_WEST, WALL_EAST]}],

    # Kurve: Waende an zwei aneinandergrenzenden Aussenseiten
    "curve": [{"name": "slide", "pivot": [0, 0, 0], "cubes": [
        FLOOR,
        cube((-8, 2, -8), (16, 7, 2), (0, 4)),   # Nordseite
        cube((6, 2, -8), (2, 7, 16), (0, 4)),    # Ostseite
    ]}],

    # Gefaelle: dieselbe Rinne, um die X-Achse gekippt
    "slope": [{"name": "slide", "pivot": [0, 4, 0], "rotation": [-22.5, 0, 0],
               "cubes": [FLOOR, WALL_WEST, WALL_EAST]}],

    # Roehre: rundum geschlossen, nur in Laufrichtung offen
    "tube": [{"name": "slide", "pivot": [0, 0, 0], "cubes": [
        FLOOR,
        cube((-8, 2, -8), (2, 12, 16), (0, 4)),
        cube((6, 2, -8), (2, 12, 16), (0, 4)),
        cube((-8, 14, -8), (16, 2, 16)),
    ]}],
}


def build_models():
    for name, bones in GEOMETRIES.items():
        dump(os.path.join(RP, "models", "blocks", "px_%s.geo.json" % name), {
            "format_version": "1.12.0",
            "minecraft:geometry": [{
                "description": {
                    "identifier": "geometry.px_" + name,
                    "texture_width": 16,
                    "texture_height": 16,
                    "visible_bounds_width": 2,
                    "visible_bounds_height": 2,
                    "visible_bounds_offset": [0, 1, 0],
                },
                "bones": bones,
            }],
        })
    return len(GEOMETRIES)


# --------------------------------------------------------------- Bloecke

def build_blocks():
    for name, geometry, texture, *_ in BLOCKS:
        ident = "px:" + name
        # Die Roehre ist rundum geschlossen und daher hoeher begehbar.
        height = 16 if geometry == "tube" else 9
        dump(os.path.join(BP, "blocks", name + ".json"), {
            "format_version": BLOCK_FORMAT,
            "minecraft:block": {
                "description": {
                    "identifier": ident,
                    "menu_category": {"category": "construction"},
                    "traits": {
                        # Der Block richtet sich beim Setzen nach dem Spieler.
                        "minecraft:placement_direction": {
                            "enabled_states": ["minecraft:cardinal_direction"],
                            "y_rotation_offset": 180,
                        }
                    },
                },
                "components": {
                    "minecraft:geometry": "geometry.px_" + geometry,
                    "minecraft:material_instances": {
                        "*": {
                            "texture": texture,
                            "render_method": "alpha_test",
                            "ambient_occlusion": False,
                        }
                    },
                    "minecraft:collision_box": {
                        "origin": [-8, 0, -8], "size": [16, 2, 16]
                    },
                    "minecraft:selection_box": {
                        "origin": [-8, 0, -8], "size": [16, height, 16]
                    },
                    "minecraft:destructible_by_mining": {"seconds_to_destroy": 0.4},
                    "minecraft:destructible_by_explosion": {"explosion_resistance": 1},
                    "minecraft:light_dampening": 0,
                    "minecraft:loot": "loot_tables/blocks/%s.json" % name,
                },
                "permutations": [
                    {
                        "condition": "query.block_state('minecraft:cardinal_direction') == '%s'" % facing,
                        "components": {
                            "minecraft:transformation": {"rotation": [0, angle, 0]}
                        },
                    }
                    for facing, angle in DIRECTIONS
                ],
            },
        })

        dump(os.path.join(BP, "loot_tables", "blocks", name + ".json"), {
            "pools": [{"rolls": 1, "entries": [
                {"type": "item", "name": ident, "weight": 1}]}],
        })
    return len(BLOCKS)


# --------------------------------------------------------------- Rezepte

def build_recipes():
    for name, (pattern, key, count) in RECIPES.items():
        ident = "px:" + name
        dump(os.path.join(BP, "recipes", name + ".json"), {
            "format_version": RECIPE_FORMAT,
            "minecraft:recipe_shaped": {
                "description": {"identifier": ident},
                "tags": ["crafting_table"],
                # Ohne unlock bleibt das Rezept im Spiel gesperrt.
                "unlock": [{"context": "AlwaysUnlocked"}],
                "pattern": pattern,
                "key": {k: {"item": v} for k, v in key.items()},
                "result": {"item": ident, "count": count},
            },
        })
    return len(RECIPES)


# --------------------------------------------------------------- Sprache

def build_lang():
    version = pack_version()
    meta = {
        "de_DE": {
            "name": "PX Wasserrutsche %s" % version,
            BP: "Teil 1 von 2: Bausteine, Rezepte und Rutsch-Logik. "
                "Kein offizielles Minecraft-Produkt.",
            RP: "Teil 2 von 2: Modelle, Texturen und Namen. "
                "Kein offizielles Minecraft-Produkt.",
            "names": {b[0]: b[3] for b in BLOCKS},
        },
        "en_US": {
            "name": "PX Waterslide %s" % version,
            BP: "Part 1 of 2: blocks, recipes and sliding logic. "
                "Not an official Minecraft product.",
            RP: "Part 2 of 2: models, textures and names. "
                "Not an official Minecraft product.",
            "names": {b[0]: b[4] for b in BLOCKS},
        },
    }

    for lang, info in meta.items():
        write_lang(os.path.join(BP, "texts", lang + ".lang"),
                   ["pack.name=" + info["name"], "pack.description=" + info[BP]])

        lines = ["pack.name=" + info["name"], "pack.description=" + info[RP], ""]
        for name, *_ in BLOCKS:
            ident = "px:" + name
            lines.append("tile.%s.name=%s" % (ident, info["names"][name]))
            lines.append("item.%s.name=%s" % (ident, info["names"][name]))
        write_lang(os.path.join(RP, "texts", lang + ".lang"), lines)

    for pack in (BP, RP):
        dump(os.path.join(pack, "texts", "languages.json"), ["de_DE", "en_US"])
    return version


def write_lang(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")


def main():
    textures = build_textures()
    models = build_models()
    blocks = build_blocks()
    recipes = build_recipes()
    version = build_lang()
    print("Bloecke: %d | Modelle: %d | Texturen: %d | Rezepte: %d | Version: %s"
          % (blocks, models, textures, recipes, version))


if __name__ == "__main__":
    main()
