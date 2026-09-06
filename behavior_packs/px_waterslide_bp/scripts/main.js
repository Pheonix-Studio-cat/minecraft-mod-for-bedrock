/*
 * PX Waterslide - Rutsch-Logik
 * PHOENIX STUDIO - MIT-Lizenz
 *
 * Kein offizielles Minecraft-Produkt, nicht von Mojang oder Microsoft genehmigt.
 */

import { world, system } from "@minecraft/server";

const VERSION = "1.0.0";
const problems = [];

function problem(where, error) {
  const line = where + ": " + error;
  if (problems.length < 20 && !problems.includes(line)) problems.push(line);
  console.warn("[PX Waterslide] " + line);
}

/* ---------------------------------------------------------------------- *
 * Konfiguration                                                          *
 * ---------------------------------------------------------------------- */
const CONFIG = {
  // Dämpft Sturzschaden, solange man rutscht. Auf false setzen für pur.
  softLanding: true,
  // Spritzer und Rutschgeräusch
  effects: true,
};

/**
 * speed  Schub pro Tick in Blöcken
 * lift   senkrechter Anteil: leicht negativ hält im Kanal, positiv hebt an
 */
const SLIDE_BLOCKS = {
  "px:slide_straight": { speed: 0.55, lift: -0.02 },
  "px:slide_curve":    { speed: 0.50, lift: -0.02 },
  "px:slide_slope":    { speed: 0.85, lift: -0.12 },
  "px:slide_tube":     { speed: 0.62, lift: -0.02 },
  "px:slide_booster":  { speed: 1.25, lift: 0.02 },
  "px:slide_end":      { speed: 0.14, lift: 0.00, brake: true },
};

// Blickrichtung des Blocks -> Richtung, in die geschoben wird.
const FACING = {
  north: { x: 0, z: -1 },
  south: { x: 0, z: 1 },
  east: { x: 1, z: 0 },
  west: { x: -1, z: 0 },
};

/* ---------------------------------------------------------------------- *
 * Helfer                                                                 *
 * ---------------------------------------------------------------------- */

function alive(entity) {
  if (!entity) return false;
  try {
    return typeof entity.isValid === "function" ? entity.isValid() : !!entity.isValid;
  } catch {
    return false;
  }
}

/**
 * Schiebt einen Spieler waagerecht an.
 *
 * applyImpulse wirkt bei Spielern nicht, dafür gibt es applyKnockback - und
 * dessen Signatur hat sich zwischen den API-Versionen geändert. Beide Formen
 * werden versucht, damit das Add-On nicht an der Version scheitert.
 */
function push(player, x, z, lift) {
  try {
    player.applyKnockback({ x, z }, lift);        // API 2.x
    return true;
  } catch {
    try {
      const strength = Math.hypot(x, z) || 1;     // API 1.x
      player.applyKnockback(x / strength, z / strength, strength, lift);
      return true;
    } catch (error) {
      problem("Schub", String(error));
      return false;
    }
  }
}

function blockAt(dimension, location) {
  try {
    return dimension.getBlock({
      x: Math.floor(location.x),
      y: Math.floor(location.y),
      z: Math.floor(location.z),
    });
  } catch {
    return undefined;
  }
}

/**
 * Sucht das Rutschenteil, auf dem der Spieler steht.
 *
 * Geprüft wird knapp unter den Füßen und auf Fußhöhe: die Teile sind flach,
 * bei etwas Geschwindigkeit steht man mal auf, mal knapp über dem Block.
 */
function slideUnder(player) {
  const spot = player.location;
  const candidates = [
    { x: spot.x, y: spot.y - 0.35, z: spot.z },
    { x: spot.x, y: spot.y + 0.1, z: spot.z },
    { x: spot.x, y: spot.y - 1.05, z: spot.z },
  ];
  for (const candidate of candidates) {
    const block = blockAt(player.dimension, candidate);
    if (!block) continue;
    const spec = SLIDE_BLOCKS[block.typeId];
    if (spec) return { block, spec };
  }
  return undefined;
}

function facingOf(block) {
  try {
    return FACING[block.permutation.getState("minecraft:cardinal_direction")];
  } catch (error) {
    problem("Blickrichtung", String(error));
    return undefined;
  }
}

/* ---------------------------------------------------------------------- *
 * Rutschen                                                               *
 * ---------------------------------------------------------------------- */

const sliding = new Set();
let ticks = 0;

function slideTick() {
  ticks++;
  for (const player of world.getPlayers()) {
    const found = slideUnder(player);

    if (!found) {
      sliding.delete(player.id);
      continue;
    }

    const direction = facingOf(found.block);
    if (!direction) continue;

    const { speed, lift } = found.spec;
    push(player, direction.x * speed, direction.z * speed, lift);
    sliding.add(player.id);

    if (CONFIG.softLanding) {
      try {
        player.addEffect("resistance", 60, { amplifier: 2, showParticles: false });
      } catch (error) {
        problem("Landung", String(error));
      }
    }

    if (!CONFIG.effects) continue;

    try {
      const at = player.location;
      player.dimension.spawnParticle("minecraft:water_splash_particle_manual", {
        x: at.x, y: at.y + 0.2, z: at.z,
      });
    } catch {
      /* Chunk nicht geladen oder Partikel unbekannt - nicht kritisch */
    }
    if (ticks % 10 === 0) {
      try {
        player.dimension.playSound("random.splash", player.location,
                                   { volume: 0.3, pitch: 1.4 });
      } catch {
        /* ignorieren */
      }
    }
  }
}

system.runInterval(slideTick, 1);

/* ---------------------------------------------------------------------- *
 * Befehle                                                                *
 * ---------------------------------------------------------------------- */

const RECIPE_HELP = [
  "§bPX Wasserrutsche - Rezepte§r  (Werkbank, G=Glas)",
  "",
  "§eRutsche gerade x6§r   G_G / GGG",
  "§eRutsche Kurve x4§r    G_G / GDG      §7D = blauer Farbstoff§r",
  "§eRutsche Gefälle x4§r  G_G / GAG      §7A = Sand§r",
  "§eRutschen-Röhre x4§r   GGG / G_G / GGG",
  "§eBeschleuniger x2§r    G_G / GRG      §7R = Redstone§r",
  "§eAuslauf x4§r          G_G / GLG      §7L = Tonklumpen§r",
  "",
  "§7Teile zeigen beim Setzen in deine Blickrichtung.",
  "§7Reihenfolge: Gefälle zum Anschieben, dann gerade Teile,",
  "§7Kurven zum Abbiegen, am Ende ein Auslauf zum Abbremsen.§r",
];

function sendDiagnosis(player) {
  for (const line of [
    "§bPX Wasserrutsche " + VERSION + "§r",
    "§7Skripte laufen.§r Wenn du das siehst, ist das Verhaltenspaket aktiv.",
    "Rutschende Spieler gerade: §f" + sliding.size + "§r",
    "Bausteine: §f" + Object.keys(SLIDE_BLOCKS).length + "§r",
    problems.length
      ? "§cFehler (" + problems.length + "):§r " + problems.slice(0, 5).join(" | ")
      : "§aKeine Fehler aufgezeichnet.§r",
    "§7Heißen die Blöcke 'tile.px:...', ist das Ressourcenpaket nicht aktiv.§r",
  ]) {
    player.sendMessage(line);
  }
}

system.afterEvents.scriptEventReceive.subscribe((event) => {
  const player = event.sourceEntity;
  const send = (line) => {
    if (player && typeof player.sendMessage === "function") player.sendMessage(line);
    else world.sendMessage(line);
  };
  if (event.id === "px:slide_recipes") {
    for (const line of RECIPE_HELP) send(line);
  } else if (event.id === "px:slide_diag") {
    if (player && typeof player.sendMessage === "function") sendDiagnosis(player);
    else world.sendMessage("§bPX Wasserrutsche " + VERSION + "§r - Skripte laufen.");
  } else if (event.id === "px:slide_help") {
    send("§bPX Wasserrutsche§r - /scriptevent px:slide_recipes  ·  " +
         "/scriptevent px:slide_diag");
  }
});

// Startmeldung: sichtbarer Beleg, dass die Skripte laufen.
system.run(() => {
  try {
    world.sendMessage(
      "§bPX Wasserrutsche " + VERSION + "§r geladen. " +
      "§7/scriptevent px:slide_recipes§r für Rezepte.");
  } catch (error) {
    console.warn("[PX Waterslide] Startmeldung fehlgeschlagen: " + error);
  }
});
