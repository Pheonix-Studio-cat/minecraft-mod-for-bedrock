#!/usr/bin/env python3
"""Erzeugt Item-, Rezept-, Textur- und Sprachdefinitionen des Add-Ons.

Ausfuehren mit:  python3 tools/gen_content.py
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BP = os.path.join(ROOT, "behavior_packs", "px_weapons_bp")
RP = os.path.join(ROOT, "resource_packs", "px_weapons_rp")

ITEM_FORMAT = "1.21.60"
RECIPE_FORMAT = "1.20.10"

# name, kategorie, stapel, nahkampfschaden, haltbarkeit(0 = unzerstoerbar), verzauberbar
ITEMS = [
    ("pistol",           "equipment", 1,  2, 0,   False),
    ("smg",              "equipment", 1,  2, 0,   False),
    ("rifle",            "equipment", 1,  3, 0,   False),
    ("shotgun",          "equipment", 1,  3, 0,   False),
    ("sniper",           "equipment", 1,  3, 0,   False),
    ("minigun",          "equipment", 1,  4, 0,   False),
    ("bazooka",          "equipment", 1,  2, 0,   False),
    ("balisong",         "equipment", 1,  6, 420, True),
    ("karambit",         "equipment", 1,  7, 480, True),
    ("turret",           "equipment", 16, 0, 0,   False),
    ("grenade_frag",     "items",     16, 0, 0,   False),
    ("grenade_smoke",    "items",     16, 0, 0,   False),
    ("grenade_molotov",  "items",     16, 0, 0,   False),
    ("ammo",             "items",     64, 0, 0,   False),
    ("rocket",           "items",     16, 0, 0,   False),
]

NAMES_DE = {
    "pistol": "PX-7 Pistole",
    "smg": "PX-9 Maschinenpistole",
    "rifle": "PX-15 Sturmgewehr",
    "shotgun": "PX-12 Schrotflinte",
    "sniper": "PX-50 Scharfschuetzengewehr",
    "minigun": "PX-6 Minigun",
    "bazooka": "PX-84 Raketenwerfer",
    "balisong": "PX Balisong",
    "karambit": "PX Karambit",
    "turret": "PX Geschuetzturm",
    "grenade_frag": "Splittergranate",
    "grenade_smoke": "Rauchgranate",
    "grenade_molotov": "Brandflasche",
    "ammo": "Munition",
    "rocket": "Rakete",
}

NAMES_EN = {
    "pistol": "PX-7 Pistol",
    "smg": "PX-9 SMG",
    "rifle": "PX-15 Assault Rifle",
    "shotgun": "PX-12 Shotgun",
    "sniper": "PX-50 Sniper Rifle",
    "minigun": "PX-6 Minigun",
    "bazooka": "PX-84 Rocket Launcher",
    "balisong": "PX Balisong",
    "karambit": "PX Karambit",
    "turret": "PX Turret",
    "grenade_frag": "Frag Grenade",
    "grenade_smoke": "Smoke Grenade",
    "grenade_molotov": "Incendiary Bottle",
    "ammo": "Ammo",
    "rocket": "Rocket",
}

IRON = "minecraft:iron_ingot"
STICK = "minecraft:stick"
REDSTONE = "minecraft:redstone"
GLASS = "minecraft:glass"
POWDER = "minecraft:gunpowder"
STRING = "minecraft:string"
COAL = "minecraft:coal"
BOTTLE = "minecraft:glass_bottle"

# Bewusst guenstig gehalten: alles aus Eisen / Redstone / Schiesspulver.
SHAPED = {
    "pistol":   (["II", "S "], {"I": IRON, "S": STICK}, 1),
    "smg":      (["III", "SR "], {"I": IRON, "S": STICK, "R": REDSTONE}, 1),
    "rifle":    (["III", "SRI"], {"I": IRON, "S": STICK, "R": REDSTONE}, 1),
    "shotgun":  (["III", "SS "], {"I": IRON, "S": STICK}, 1),
    "sniper":   ([" G ", "III", "SI "], {"I": IRON, "S": STICK, "G": GLASS}, 1),
    "minigun":  (["III", "IRI", "SI "], {"I": IRON, "S": STICK, "R": REDSTONE}, 1),
    "bazooka":  (["III", "GRI", " S "], {"I": IRON, "S": STICK, "R": REDSTONE, "G": POWDER}, 1),
    "balisong": (["I ", "IS"], {"I": IRON, "S": STICK}, 1),
    "karambit": (["II", "TS"], {"I": IRON, "S": STICK, "T": STRING}, 1),
    "turret":   ([" I ", "IRI", "IGI"], {"I": IRON, "R": REDSTONE, "G": POWDER}, 1),
}

SHAPELESS = {
    "ammo":            ([IRON, POWDER], 8),
    "rocket":          ([IRON, POWDER, REDSTONE], 2),
    "grenade_frag":    ([IRON, POWDER, POWDER], 2),
    "grenade_smoke":   ([COAL, COAL, POWDER], 2),
    "grenade_molotov": ([BOTTLE, COAL, STRING], 2),
}


def dump(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        json.dump(data, fh, indent=2)
        fh.write("\n")


def build_items():
    texture_data = {}
    for name, category, stack, melee, durability, enchantable in ITEMS:
        ident = "px:" + name
        texture = "px_" + name
        components = {
            # Kurzform statt {"texture": ...}: ab 1.20.60 die empfohlene und
            # zuverlaessigere Schreibweise fuer den Atlas-Kurznamen.
            "minecraft:icon": texture,
            "minecraft:display_name": {"value": "item.%s.name" % ident},
            "minecraft:max_stack_size": stack,
        }
        if stack == 1:
            components["minecraft:hand_equipped"] = True
        if melee:
            components["minecraft:damage"] = melee
        if durability:
            components["minecraft:durability"] = {"max_durability": durability}
        if enchantable:
            components["minecraft:enchantable"] = {"value": 12, "slot": "sword"}
        dump(os.path.join(BP, "items", name + ".json"), {
            "format_version": ITEM_FORMAT,
            "minecraft:item": {
                "description": {
                    "identifier": ident,
                    "menu_category": {"category": category},
                },
                "components": components,
            },
        })
        texture_data[texture] = {"textures": "textures/items/" + texture}

    dump(os.path.join(RP, "textures", "item_texture.json"), {
        "resource_pack_name": "px_weapons",
        "texture_name": "atlas.items",
        "texture_data": texture_data,
    })


def build_recipes():
    for name, (pattern, key, count) in SHAPED.items():
        ident = "px:" + name
        dump(os.path.join(BP, "recipes", name + ".json"), {
            "format_version": RECIPE_FORMAT,
            "minecraft:recipe_shaped": {
                "description": {"identifier": ident},
                "tags": ["crafting_table"],
                # Seit 1.20.10 muessen Rezepte freigeschaltet werden,
                # sonst sind sie im Spiel nicht herstellbar.
                "unlock": [{"context": "AlwaysUnlocked"}],
                "pattern": pattern,
                "key": {k: {"item": v} for k, v in key.items()},
                "result": {"item": ident, "count": count},
            },
        })

    for name, (ingredients, count) in SHAPELESS.items():
        ident = "px:" + name
        dump(os.path.join(BP, "recipes", name + ".json"), {
            "format_version": RECIPE_FORMAT,
            "minecraft:recipe_shapeless": {
                "description": {"identifier": ident},
                "tags": ["crafting_table"],
                "unlock": [{"context": "AlwaysUnlocked"}],
                "ingredients": [{"item": i} for i in ingredients],
                "result": {"item": ident, "count": count},
            },
        })


def pack_version():
    """Liest die Version aus dem Behavior-Pack-Manifest.

    Damit steht die Version nur an einer Stelle und kann nicht zwischen
    Manifest und angezeigtem Paketnamen auseinanderlaufen.
    """
    with open(os.path.join(BP, "manifest.json")) as fh:
        return ".".join(str(n) for n in json.load(fh)["header"]["version"])


def build_lang():
    version = pack_version()

    # Der Paketname traegt die Version, damit sich in der Paketliste einer Welt
    # mehrere Fassungen unterscheiden lassen. Die Beschreibung sagt zusaetzlich,
    # welcher der beiden Teile es ist - beide muessen aktiviert werden.
    packs = {
        "de_DE": {
            "name": "PX Waffen %s" % version,
            BP: "Teil 1 von 2: Verhalten, Rezepte und Skripte. "
                "Kein offizielles Minecraft-Produkt.",
            RP: "Teil 2 von 2: Texturen, Fadenkreuz und Namen. "
                "Kein offizielles Minecraft-Produkt.",
        },
        "en_US": {
            "name": "PX Weapons %s" % version,
            BP: "Part 1 of 2: behaviour, recipes and scripts. "
                "Not an official Minecraft product.",
            RP: "Part 2 of 2: textures, crosshair and names. "
                "Not an official Minecraft product.",
        },
    }
    tables = {"de_DE": NAMES_DE, "en_US": NAMES_EN}

    for lang, names in tables.items():
        meta = packs[lang]

        # Behavior-Pack: nur der Paketname. Bewusst ohne Item-Namen, damit ein
        # fehlendes Resource-Pack sofort auffaellt - die Items heissen dann
        # sichtbar "item.px:pistol.name".
        write_lang(os.path.join(BP, "texts", lang + ".lang"),
                   ["pack.name=" + meta["name"],
                    "pack.description=" + meta[BP]])

        # Resource-Pack: Paketname und alle Item-Namen.
        lines = ["pack.name=" + meta["name"],
                 "pack.description=" + meta[RP], ""]
        for name, *_ in ITEMS:
            ident = "px:" + name
            # Beide Schluesselvarianten, damit es versionsunabhaengig greift.
            lines.append("item.%s.name=%s" % (ident, names[name]))
            lines.append("item.%s=%s" % (ident, names[name]))
        write_lang(os.path.join(RP, "texts", lang + ".lang"), lines)

    for pack in (BP, RP):
        dump(os.path.join(pack, "texts", "languages.json"), ["de_DE", "en_US"])

    return version


def write_lang(path, lines):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as fh:
        fh.write("\n".join(lines) + "\n")


def build_turret():
    dump(os.path.join(BP, "entities", "px_turret.json"), {
        "format_version": "1.21.30",
        "minecraft:entity": {
            "description": {
                "identifier": "px:turret",
                "is_spawnable": False,
                "is_summonable": True,
            },
            "components": {
                "minecraft:type_family": {"family": ["px_turret", "inanimate"]},
                "minecraft:health": {"value": 40, "max": 40},
                "minecraft:collision_box": {"width": 0.8, "height": 0.9},
                "minecraft:physics": {},
                "minecraft:pushable": {"is_pushable": False,
                                       "is_pushable_by_piston": False},
                "minecraft:knockback_resistance": {"value": 1.0},
                "minecraft:persistent": {},
                "minecraft:fire_immune": True,
                "minecraft:loot": {"table": "loot_tables/entities/px_turret.json"},
            },
        },
    })

    dump(os.path.join(BP, "loot_tables", "entities", "px_turret.json"), {
        "pools": [{
            "rolls": 1,
            "entries": [{"type": "item", "name": "px:turret", "weight": 1}],
        }],
    })

    dump(os.path.join(RP, "entity", "px_turret.entity.json"), {
        "format_version": "1.10.0",
        "minecraft:client_entity": {
            "description": {
                "identifier": "px:turret",
                "materials": {"default": "entity_alphatest"},
                "textures": {"default": "textures/entity/px_turret"},
                "geometry": {"default": "geometry.px_turret"},
                "render_controllers": ["controller.render.default"],
            },
        },
    })

    dump(os.path.join(RP, "models", "entity", "px_turret.geo.json"), {
        "format_version": "1.12.0",
        "minecraft:geometry": [{
            "description": {
                "identifier": "geometry.px_turret",
                "texture_width": 64,
                "texture_height": 64,
                "visible_bounds_width": 2,
                "visible_bounds_height": 2,
                "visible_bounds_offset": [0, 1, 0],
            },
            "bones": [
                {"name": "base", "pivot": [0, 0, 0], "cubes": [
                    {"origin": [-5, 0, -5], "size": [10, 3, 10], "uv": [0, 0]}]},
                {"name": "body", "parent": "base", "pivot": [0, 3, 0], "cubes": [
                    {"origin": [-4, 3, -4], "size": [8, 6, 8], "uv": [0, 20]}]},
                {"name": "barrel", "parent": "body", "pivot": [0, 7, 0], "cubes": [
                    {"origin": [-1.5, 5.5, -11], "size": [3, 3, 11], "uv": [0, 40]}]},
            ],
        }],
    })


def build_textures_list():
    """Listet alle Texturen des Resource-Packs in textures/textures_list.json."""
    root = os.path.join(RP, "textures")
    paths = []
    for base, _, files in os.walk(root):
        for name in sorted(files):
            if name.endswith(".png"):
                rel = os.path.relpath(os.path.join(base, name), RP)
                paths.append(rel.replace(os.sep, "/")[: -len(".png")])
    dump(os.path.join(root, "textures_list.json"), sorted(paths))
    return len(paths)


def main():
    build_items()
    build_recipes()
    version = build_lang()
    build_turret()
    count = build_textures_list()
    print("Items:", len(ITEMS), "| Rezepte:", len(SHAPED) + len(SHAPELESS),
          "| Texturen gelistet:", count, "| Paketname: PX Waffen", version)


if __name__ == "__main__":
    main()
