# PX Weapons — Waffen-Add-On für Minecraft Bedrock

> **NOT AN OFFICIAL MINECRAFT PRODUCT.**
> **NOT APPROVED BY OR ASSOCIATED WITH MOJANG OR MICROSOFT.**

Ein Bedrock-Add-On von PHÖNIX STUDIO mit Nahkampfwaffen, Schusswaffen, Granaten
und einem Geschützturm. Alle Waffen sind **frei erfunden** — keine realen
Markennamen, keine Designs aus anderen Spielen, alle Grafiken selbst erzeugt.

## Installation

1. `python3 tools/build.py` ausführen → erzeugt `dist/PX_Weapons.mcaddon`
2. Die `.mcaddon`-Datei doppelklicken (Windows/Android/iOS) — Minecraft
   importiert Behavior- und Resource-Pack automatisch
3. In den Welteinstellungen **beide** Packs aktivieren
4. Unter *Experimente* → **Beta APIs** einschalten (nötig für die Skript-Logik)

Alternativ: die beiden Ordner direkt nach
`com.mojang/development_behavior_packs/` bzw. `development_resource_packs/`
kopieren.

**Voraussetzung:** Minecraft Bedrock **1.21.80 oder neuer** (das Add-On nutzt
`@minecraft/server` 2.0.0).

## Inhalt

### Schusswaffen

Rechtsklick / langes Tippen = schießen. Verbrauchen **Munition** aus dem Inventar.

| Waffe | Schaden | Nachladezeit | Reichweite | Besonderheit |
|---|---|---|---|---|
| PX-7 Pistole | 5 | 0,4 s | 40 | Einzelschuss, wenig Streuung |
| PX-9 Maschinenpistole | 4 | 0,6 s | 32 | 3-Schuss-Salve |
| PX-15 Sturmgewehr | 7 | 0,7 s | 56 | 2-Schuss-Salve |
| PX-12 Schrotflinte | 3 × 8 | 1,0 s | 16 | 8 Schrotkugeln, breite Streuung |
| PX-50 Scharfschützengewehr | 22 | 1,7 s | 120 | keine Streuung |
| PX-6 Minigun | 3 | 2,25 s | 40 | 14-Schuss-Salve |
| PX-84 Raketenwerfer | Explosion | 2,75 s | — | verbraucht **Raketen** |

### Nahkampf

| Waffe | Schaden | Rechtsklick |
|---|---|---|
| PX Balisong | 6 | Flip-Animation (kosmetisch) |
| PX Karambit | 7 | Ausfallschritt — 5 Extraschaden auf 3 Blöcke |

### Granaten & Gerät

| Gegenstand | Wirkung |
|---|---|
| Splittergranate | 2,5 s Zünder, Explosion Radius 2,6 |
| Rauchgranate | 10 s Rauchwolke, Blindheit im Radius 5 |
| Brandflasche | zerbricht beim Aufprall, entzündet Boden und Gegner |
| PX Geschützturm | zielt automatisch auf Monster im Radius 16, 40 LP |

## Crafting-Rezepte

Bewusst günstig gehalten — alles aus Eisen, Stöcken, Redstone und Schießpulver.
`I` Eisenbarren · `S` Stock · `R` Redstone · `G` Glas · `P` Schießpulver ·
`T` Faden

```
Pistole        Sturmgewehr    Schrotflinte   Scharfschütze  Minigun
I I            I I I          I I I           .  G  .       I I I
S .            S R I          S S .           I  I  I       I R I
                                              S  I  .       S I .

Bazooka        Balisong       Karambit        Geschützturm
I I I          I .            I I             .  I  .
P R I          I S            T S             I  R  I
. S .                                         I  P  I
```

Formlos (Werkbank, Reihenfolge egal):

| Ergebnis | Zutaten |
|---|---|
| 8 × Munition | 1 Eisenbarren + 1 Schießpulver |
| 2 × Rakete | 1 Eisenbarren + 1 Schießpulver + 1 Redstone |
| 2 × Splittergranate | 1 Eisenbarren + 2 Schießpulver |
| 2 × Rauchgranate | 2 Kohle + 1 Schießpulver |
| 2 × Brandflasche | 1 Glasflasche + 1 Kohle + 1 Faden |

## Anpassen

Alle Stellschrauben stehen ganz oben in
`behavior_packs/px_weapons_bp/scripts/main.js`:

```js
const CONFIG = {
  explosionsBreakBlocks: true,  // auf false = kein Griefing durch Explosionen
  molotovSetsFire: true,        // auf false = Brandflasche setzt keine Feuerblöcke
  turretRange: 16,
  turretDamage: 4,
  turretFireRate: 10,
  smokeDurationTicks: 200,
  smokeRadius: 5,
};
```

Waffenwerte stehen direkt darunter in der `GUNS`-Tabelle (Schaden, Abklingzeit,
Streuung, Reichweite, Salvenlänge).

## Entwicklung

| Befehl | Zweck |
|---|---|
| `python3 tools/gen_textures.py` | erzeugt alle PNGs neu aus ASCII-Pixelart |
| `python3 tools/gen_content.py` | erzeugt Items, Rezepte, Sprachdateien, Entity |
| `python3 tools/validate.py` | prüft JSON, Texturverweise, Rezepte, Sprachschlüssel |
| `python3 tools/build.py` | packt `dist/PX_Weapons.mcaddon` |
| `node --check behavior_packs/px_weapons_bp/scripts/main.js` | Syntaxprüfung |

Wer Item- oder Rezeptwerte ändert, ändert sie in `tools/gen_content.py` und
generiert neu — die JSON-Dateien sind erzeugte Artefakte.

## Rechtliches

- **Eigenständige Namen.** Alle Waffen heißen `PX-…`. Keine realen
  Herstellermarken (AK-47, Glock, Barrett …), keine Bezeichnungen oder
  Skin-Muster aus anderen Spielen.
- **Eigene Assets.** Sämtliche Texturen werden von `tools/gen_textures.py`
  prozedural erzeugt. Es sind keine Minecraft-Assets und keine fremden Bilddaten
  im Repository. Siehe `ATTRIBUTION.md`.
- **Sounds.** Es werden ausschließlich Vanilla-Sound-IDs *referenziert*
  (`random.bow`, `random.explode`, …). Es werden keine Audiodateien mitgeliefert.
- **Keine Netzwerkfunktionen.** Das Add-On nutzt weder `@minecraft/server-net`
  noch `@minecraft/server-admin`. Es sammelt und überträgt keinerlei Daten —
  damit sind DSGVO/revDSG hier kein Thema.
- **Verteilung.** Gedacht als kostenloses Community-Add-On. Für den
  **Minecraft Marketplace** ist dieses Add-On nicht geeignet — realistische
  Schusswaffen sind dort nicht zulässig. Auch auf kommerziell betriebenen
  Servern gelten Mojangs Commercial Usage Guidelines; vor einer Monetarisierung
  bitte selbst prüfen.
- **Lizenz.** MIT (siehe `LICENSE`) — gilt für den Code und die hier erzeugten
  Assets, nicht für Minecraft selbst.
