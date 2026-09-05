# Herkunft der Assets

Dieses Verzeichnis dokumentiert die Herkunft jedes Assets im Add-On. Zweck:
jederzeit belegen zu können, dass keine fremden oder Vanilla-Inhalte enthalten
sind.

## Grafiken

| Datei(en) | Herkunft | Lizenz |
|---|---|---|
| `resource_packs/px_weapons_rp/textures/items/*.png` | prozedural erzeugt von `tools/gen_textures.py` aus ASCII-Pixelart in derselben Datei | MIT (PHÖNIX STUDIO) |
| `resource_packs/px_weapons_rp/textures/entity/px_turret.png` | prozedural erzeugt von `tools/gen_textures.py` | MIT (PHÖNIX STUDIO) |
| `*/pack_icon.png` | prozedural erzeugt von `tools/gen_textures.py` | MIT (PHÖNIX STUDIO) |

Es sind **keine** Bilddaten aus Minecraft, aus anderen Spielen oder aus
Fremdquellen enthalten. Der PNG-Encoder in `tools/gen_textures.py` ist selbst
geschrieben (nur `zlib` und `struct` aus der Standardbibliothek).

## Modelle

| Datei | Herkunft | Lizenz |
|---|---|---|
| `resource_packs/px_weapons_rp/models/entity/px_turret.geo.json` | von Hand erstellt (`tools/gen_content.py`) | MIT (PHÖNIX STUDIO) |

## Sounds

Es werden **keine** Audiodateien mitgeliefert. Das Skript ruft ausschließlich
vorhandene Vanilla-Sound-IDs über `dimension.playSound()` auf:

`random.bow` · `random.explode` · `random.click` · `random.pop` · `random.fizz` ·
`random.glass` · `random.anvil_land` · `fire.ignite` · `mob.ghast.fireball` ·
`mob.player.attack.sweep`

Das Referenzieren einer ID ist keine Vervielfältigung der Audiodatei.

## Render-Controller

`controller.render.default` ist ein von Minecraft bereitgestellter
Render-Controller und wird nur per ID referenziert, nicht mitgeliefert.

## Namen

Sämtliche Waffennamen (`PX-7`, `PX-15`, `PX-84`, …) sind frei erfunden. Es
werden keine eingetragenen Marken von Waffenherstellern und keine
Bezeichnungen, Skin-Muster oder Designs aus anderen Videospielen verwendet.

## Falls du eigene Assets ergänzt

Trag sie hier mit Quelle und Lizenz ein, **bevor** du sie committest. Für
Fremdmaterial gilt: nur CC0 oder eine ausdrücklich kompatible Lizenz, und den
Fundort mit Datum notieren.
