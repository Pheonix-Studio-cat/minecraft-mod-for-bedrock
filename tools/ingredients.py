#!/usr/bin/env python3
"""Zutaten der Crafting-Rezepte: Kuerzel, Anzeigename und Farbe.

Einzige Quelle fuer alle Werkzeuge. Vorher gab es zwei Tabellen - eine im
Validator, eine im Website-Generator - und die liefen auseinander: neue
Zutaten wurden auf der Rezeptseite als "?" dargestellt.

Es werden keine Minecraft-Texturen verwendet, nur eigene Farbfelder.
"""

INGREDIENTS = {
    "minecraft:iron_ingot":   ("I", "Eisenbarren", "#d9dde2"),
    "minecraft:stick":        ("S", "Stock", "#b58c56"),
    "minecraft:redstone":     ("R", "Redstone", "#d05646"),
    "minecraft:glass":        ("G", "Glas", "#a9d9e8"),
    "minecraft:gunpowder":    ("P", "Schießpulver", "#9aa0a6"),
    "minecraft:string":       ("T", "Faden", "#e8e8e8"),
    "minecraft:coal":         ("C", "Kohle", "#6b6b6b"),
    "minecraft:glass_bottle": ("F", "Glasflasche", "#b9dccb"),
    "minecraft:blue_dye":     ("D", "Blauer Farbstoff", "#5a7fd0"),
    "minecraft:sand":         ("A", "Sand", "#e0d6a8"),
    "minecraft:clay_ball":    ("L", "Tonklumpen", "#a8adba"),
}

# Kuerzel je Zutat, fuer den Abgleich der Rezepthilfe im Skript.
LETTER = {item: data[0] for item, data in INGREDIENTS.items()}
