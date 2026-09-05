/*
 * PX Weapons - Skript-Logik
 * PHOENIX STUDIO - MIT-Lizenz
 *
 * Alle Waffen sind frei erfunden. Keine realen Marken, keine fremden Designs.
 * Kein offizielles Minecraft-Produkt, nicht von Mojang oder Microsoft genehmigt.
 */

import { world, system } from "@minecraft/server";

/* ---------------------------------------------------------------------- *
 * Diagnose                                                               *
 *                                                                        *
 * Fehler wurden frueher stillschweigend verschluckt. Jetzt landet jeder   *
 * in dieser Liste und im Inhaltsprotokoll, abrufbar im Spiel mit          *
 *   /scriptevent px:diag                                                  *
 * ---------------------------------------------------------------------- */
const VERSION = "1.2.0";
const problems = [];

function problem(where, error) {
  const line = where + ": " + error;
  if (problems.length < 20 && !problems.includes(line)) problems.push(line);
  console.warn("[PX Weapons] " + line);
}

/* ------------------------------------------------------------------ *
 * Konfiguration - hier kannst du alles ohne Code-Kenntnisse anpassen. *
 * ------------------------------------------------------------------ */
const CONFIG = {
  // Auf false setzen, damit Raketen und Splittergranaten keine Bloecke zerstoeren.
  explosionsBreakBlocks: true,
  // Auf false setzen, damit die Brandflasche keine Feuerbloecke setzt.
  molotovSetsFire: true,
  // Geschuetzturm
  turretRange: 16,
  turretDamage: 4,
  turretFireRate: 10, // Ticks zwischen zwei Schuessen
  // Rauchgranate
  smokeDurationTicks: 200,
  smokeRadius: 5,
};

const AMMO = "px:ammo";
const ROCKET = "px:rocket";

/**
 * dmg      Schaden pro Kugel
 * cd       Abklingzeit in Ticks (20 Ticks = 1 Sekunde)
 * pellets  Kugeln pro Schuss (Schrotflinte)
 * spread   Streuung in Grad
 * range    Reichweite in Bloecken
 * burst    Schuesse pro Ausloesen, gap = Ticks dazwischen
 */
const GUNS = {
  "px:pistol":  { dmg: 5,  cd: 8,  pellets: 1, spread: 0.0, range: 40,  sound: "random.bow" },
  "px:smg":     { dmg: 4,  cd: 12, pellets: 1, spread: 1.2, range: 32,  burst: 3,  gap: 2, sound: "random.bow" },
  "px:rifle":   { dmg: 7,  cd: 14, pellets: 1, spread: 0.5, range: 56,  burst: 2,  gap: 3, sound: "random.bow" },
  "px:shotgun": { dmg: 3,  cd: 20, pellets: 8, spread: 5.0, range: 16,  sound: "random.explode" },
  "px:sniper":  { dmg: 22, cd: 34, pellets: 1, spread: 0.0, range: 120, sound: "random.explode" },
  "px:minigun": { dmg: 3,  cd: 45, pellets: 1, spread: 2.0, range: 40,  burst: 14, gap: 2, sound: "random.bow" },
};

const GRENADES = {
  "px:grenade_frag":    { fuse: 50, speed: 1.15, kind: "frag" },
  "px:grenade_smoke":   { fuse: 40, speed: 1.15, kind: "smoke" },
  "px:grenade_molotov": { fuse: 0,  speed: 1.25, kind: "molotov" }, // zerbricht beim Aufprall
};

/* ------------------------------- Vektoren ------------------------------- */

const add = (a, b) => ({ x: a.x + b.x, y: a.y + b.y, z: a.z + b.z });
const scale = (v, s) => ({ x: v.x * s, y: v.y * s, z: v.z * s });
const dist = (a, b) => Math.hypot(a.x - b.x, a.y - b.y, a.z - b.z);

function normalize(v) {
  const m = Math.hypot(v.x, v.y, v.z) || 1;
  return { x: v.x / m, y: v.y / m, z: v.z / m };
}

function cross(a, b) {
  return {
    x: a.y * b.z - a.z * b.y,
    y: a.z * b.x - a.x * b.z,
    z: a.x * b.y - a.y * b.x,
  };
}

/**
 * Streut den Schuss in einem echten Kegel um die Blickrichtung.
 *
 * Vorher wurde auf jede Achse unabhaengig ein Zufallswert addiert, auch auf
 * die Blickachse selbst. Dadurch lag der Treffer systematisch neben dem Ziel.
 * Jetzt wird senkrecht zur Blickrichtung ausgelenkt, gleichmaessig ueber die
 * Kreisflaeche, und bei 0 Grad trifft der Schuss exakt das Fadenkreuz.
 */
function applySpread(dir, degrees) {
  const forward = normalize(dir);
  if (!degrees) return forward;

  const helper = Math.abs(forward.y) > 0.999 ? { x: 1, y: 0, z: 0 } : { x: 0, y: 1, z: 0 };
  const right = normalize(cross(forward, helper));
  const up = cross(right, forward);

  const maxRadius = Math.tan((degrees * Math.PI) / 180);
  const radius = Math.sqrt(Math.random()) * maxRadius;
  const angle = Math.random() * Math.PI * 2;
  const dx = Math.cos(angle) * radius;
  const dy = Math.sin(angle) * radius;

  return normalize({
    x: forward.x + right.x * dx + up.x * dy,
    y: forward.y + right.y * dx + up.y * dy,
    z: forward.z + right.z * dx + up.z * dy,
  });
}

/* --------------------------- Kleine Helfer ------------------------------ */

// isValid ist je nach API-Version Property oder Methode.
function alive(entity) {
  if (!entity) return false;
  try {
    return typeof entity.isValid === "function" ? entity.isValid() : !!entity.isValid;
  } catch {
    return false;
  }
}

function isCreative(player) {
  try {
    // Der Enum-Wert ist je nach API-Version "Creative" oder "creative".
    return String(player.getGameMode()).toLowerCase() === "creative";
  } catch {
    return false;
  }
}

function solid(block) {
  if (!block) return false;
  try {
    return !block.isAir && !block.isLiquid;
  } catch {
    return false;
  }
}

function particle(dimension, id, location) {
  try {
    dimension.spawnParticle(id, location);
  } catch {
    /* Chunk nicht geladen - egal */
  }
}

function sound(dimension, id, location, volume = 1, pitch = 1) {
  try {
    dimension.playSound(id, location, { volume, pitch });
  } catch {
    /* ignorieren */
  }
}

/**
 * Fuegt Schaden zu und faellt auf einfachere Aufrufformen zurueck, falls die
 * API-Version die Optionen nicht kennt. Frueher schlug der Aufruf in dem Fall
 * stumm fehl - die Waffe traf, richtete aber nichts aus.
 */
function dealDamage(target, amount, cause, source) {
  const attempts = [
    () => target.applyDamage(amount, { cause, damagingEntity: source }),
    () => target.applyDamage(amount, { cause }),
    () => target.applyDamage(amount),
  ];
  for (let i = 0; i < attempts.length; i++) {
    try {
      attempts[i]();
      return true;
    } catch (error) {
      if (i === attempts.length - 1) problem("Schaden", String(error));
    }
  }
  return false;
}

function tell(player, message) {
  try {
    player.onScreenDisplay.setActionBar(message);
  } catch {
    /* ignorieren */
  }
}

/* ------------------------------ Munition -------------------------------- */

function container(player) {
  try {
    return player.getComponent("minecraft:inventory")?.container;
  } catch {
    return undefined;
  }
}

function countItem(player, typeId) {
  const inv = container(player);
  if (!inv) return 0;
  let total = 0;
  for (let i = 0; i < inv.size; i++) {
    const stack = inv.getItem(i);
    if (stack && stack.typeId === typeId) total += stack.amount;
  }
  return total;
}

function consumeItem(player, typeId, amount) {
  if (isCreative(player)) return true;
  if (countItem(player, typeId) < amount) return false;
  const inv = container(player);
  if (!inv) return false;
  let remaining = amount;
  for (let i = 0; i < inv.size && remaining > 0; i++) {
    const stack = inv.getItem(i);
    if (!stack || stack.typeId !== typeId) continue;
    const take = Math.min(stack.amount, remaining);
    remaining -= take;
    if (stack.amount - take <= 0) {
      inv.setItem(i, undefined);
    } else {
      stack.amount -= take;
      inv.setItem(i, stack);
    }
  }
  return remaining === 0;
}

/* ----------------------------- Abklingzeit ------------------------------ */

const cooldowns = new Map();

function ready(player, id, ticks) {
  const key = player.id + "|" + id;
  const last = cooldowns.get(key) ?? -100000;
  if (last + ticks > system.currentTick) return false;
  cooldowns.set(key, system.currentTick);
  return true;
}

/* ------------------------- Schusswaffen (Hitscan) ----------------------- */

function tracer(dimension, origin, direction, length) {
  for (let d = 0.8; d < length; d += 1.4) {
    particle(dimension, "minecraft:basic_smoke_particle", add(origin, scale(direction, d)));
  }
}

function fireOnce(player, gun) {
  const dimension = player.dimension;
  const origin = player.getHeadLocation();
  const aim = player.getViewDirection();

  particle(dimension, "minecraft:basic_flame_particle", add(origin, scale(aim, 0.8)));
  sound(dimension, gun.sound, player.location, 1, 1.6);

  for (let pellet = 0; pellet < (gun.pellets ?? 1); pellet++) {
    const direction = applySpread(aim, gun.spread);
    let reach = gun.range;

    try {
      const blockHit = dimension.getBlockFromRay(origin, direction, {
        maxDistance: gun.range,
        includePassableBlocks: false,
        includeLiquidBlocks: false,
      });
      if (blockHit?.block) reach = Math.min(reach, dist(origin, blockHit.block.location));
    } catch {
      /* ignorieren */
    }

    let victim;
    try {
      const hits = dimension.getEntitiesFromRay(origin, direction, { maxDistance: gun.range });
      victim = hits
        .filter((h) => h.entity && h.entity.id !== player.id && h.distance <= reach)
        .sort((a, b) => a.distance - b.distance)[0];
    } catch {
      /* ignorieren */
    }

    if (victim) {
      reach = victim.distance;
      dealDamage(victim.entity, gun.dmg, "projectile", player);
      particle(dimension, "minecraft:critical_hit_emitter", victim.entity.location);
    }

    tracer(dimension, origin, direction, reach);
    particle(dimension, "minecraft:basic_smoke_particle", add(origin, scale(direction, reach)));
  }
}

function shoot(player, itemId) {
  const gun = GUNS[itemId];
  if (!ready(player, itemId, gun.cd)) return;

  if (countItem(player, AMMO) < 1 && !isCreative(player)) {
    sound(player.dimension, "random.click", player.location, 1, 0.6);
    tell(player, "§cKeine Munition");
    return;
  }

  const shots = gun.burst ?? 1;
  const gap = gun.gap ?? 2;
  for (let i = 0; i < shots; i++) {
    system.runTimeout(() => {
      if (!alive(player)) return;
      if (!consumeItem(player, AMMO, 1)) return;
      fireOnce(player, gun);
      showAmmo(player, itemId);
    }, i * gap);
  }
}

/* ------------------------------- Raketen -------------------------------- */

const rockets = [];

function launchRocket(player) {
  if (!ready(player, "px:bazooka", 55)) return;
  if (!consumeItem(player, ROCKET, 1)) {
    sound(player.dimension, "random.click", player.location, 1, 0.6);
    tell(player, "§cKeine Rakete");
    return;
  }
  const direction = player.getViewDirection();
  rockets.push({
    dimension: player.dimension,
    position: add(player.getHeadLocation(), scale(direction, 1.0)),
    direction,
    owner: player,
    age: 0,
  });
  sound(player.dimension, "mob.ghast.fireball", player.location, 1.2, 1);
  showAmmo(player, "px:bazooka");
}

function detonate(dimension, position, radius, causesFire, source) {
  try {
    dimension.createExplosion(position, radius, {
      breaksBlocks: CONFIG.explosionsBreakBlocks,
      causesFire,
      source,
    });
  } catch {
    sound(dimension, "random.explode", position, 1.4, 1);
  }
}

function stepRockets() {
  for (let i = rockets.length - 1; i >= 0; i--) {
    const rocket = rockets[i];
    rocket.age++;
    if (rocket.age > 120) {
      rockets.splice(i, 1);
      continue;
    }

    const speed = 1.7;
    let hit = null;

    try {
      const blockHit = rocket.dimension.getBlockFromRay(rocket.position, rocket.direction, {
        maxDistance: speed,
        includePassableBlocks: false,
        includeLiquidBlocks: false,
      });
      if (blockHit?.block) hit = rocket.position;
    } catch {
      /* ignorieren */
    }

    const next = add(rocket.position, scale(rocket.direction, speed));

    if (!hit && rocket.age > 2) {
      try {
        const nearby = rocket.dimension.getEntities({
          location: next,
          maxDistance: 1.4,
          excludeTypes: ["minecraft:item", "minecraft:xp_orb"],
        });
        if (nearby.some((e) => e.id !== rocket.owner?.id)) hit = next;
      } catch {
        /* ignorieren */
      }
    }

    particle(rocket.dimension, "minecraft:basic_flame_particle", rocket.position);
    particle(rocket.dimension, "minecraft:basic_smoke_particle", rocket.position);

    if (hit) {
      detonate(rocket.dimension, hit, 3.2, false, rocket.owner);
      rockets.splice(i, 1);
      continue;
    }
    rocket.position = next;
  }
}

/* ------------------------------ Granaten -------------------------------- */

const grenades = [];
const smokeClouds = [];

function throwGrenade(player, itemId) {
  const spec = GRENADES[itemId];
  if (!ready(player, itemId, 12)) return;
  if (!consumeItem(player, itemId, 1)) return;

  const direction = player.getViewDirection();
  grenades.push({
    dimension: player.dimension,
    position: add(player.getHeadLocation(), scale(direction, 0.6)),
    velocity: scale(direction, spec.speed),
    fuse: spec.fuse,
    kind: spec.kind,
    owner: player,
    age: 0,
  });
  sound(player.dimension, "random.bow", player.location, 0.7, 1.3);
}

function ignite(dimension, position, radius) {
  if (!CONFIG.molotovSetsFire) return;
  const r = Math.ceil(radius);
  for (let dx = -r; dx <= r; dx++) {
    for (let dz = -r; dz <= r; dz++) {
      if (dx * dx + dz * dz > radius * radius) continue;
      for (let dy = 2; dy >= -2; dy--) {
        const location = {
          x: Math.floor(position.x) + dx,
          y: Math.floor(position.y) + dy,
          z: Math.floor(position.z) + dz,
        };
        try {
          const here = dimension.getBlock(location);
          const below = dimension.getBlock({ x: location.x, y: location.y - 1, z: location.z });
          if (here?.isAir && solid(below)) {
            here.setType("minecraft:fire");
            break;
          }
        } catch {
          /* ignorieren */
        }
      }
    }
  }
}

function burst(grenade) {
  const { dimension, position, kind, owner } = grenade;

  if (kind === "frag") {
    detonate(dimension, position, 2.6, false, owner);
    return;
  }

  if (kind === "molotov") {
    sound(dimension, "random.glass", position, 1, 1);
    sound(dimension, "fire.ignite", position, 1.2, 1);
    ignite(dimension, position, 2.5);
    try {
      for (const entity of dimension.getEntities({ location: position, maxDistance: 3 })) {
        entity.setOnFire(6, true);
      }
    } catch {
      /* ignorieren */
    }
    return;
  }

  // Rauch
  sound(dimension, "random.fizz", position, 1.2, 0.8);
  smokeClouds.push({
    dimension,
    position,
    until: system.currentTick + CONFIG.smokeDurationTicks,
    nextEffect: 0,
  });
}

function stepGrenades() {
  for (let i = grenades.length - 1; i >= 0; i--) {
    const grenade = grenades[i];
    grenade.age++;

    grenade.velocity = {
      x: grenade.velocity.x * 0.99,
      y: grenade.velocity.y * 0.99 - 0.045,
      z: grenade.velocity.z * 0.99,
    };
    const next = add(grenade.position, grenade.velocity);

    let blocked = false;
    try {
      blocked = solid(grenade.dimension.getBlock({
        x: Math.floor(next.x),
        y: Math.floor(next.y),
        z: Math.floor(next.z),
      }));
    } catch {
      /* ignorieren */
    }

    if (blocked) {
      if (grenade.kind === "molotov") {
        burst(grenade);
        grenades.splice(i, 1);
        continue;
      }
      // Abprallen
      grenade.velocity = scale(grenade.velocity, -0.35);
      sound(grenade.dimension, "random.pop", grenade.position, 0.5, 1.2);
    } else {
      grenade.position = next;
    }

    particle(grenade.dimension, "minecraft:basic_smoke_particle", grenade.position);

    if (grenade.fuse > 0) grenade.fuse--;
    if ((grenade.fuse <= 0 && grenade.kind !== "molotov") || grenade.age > 200) {
      burst(grenade);
      grenades.splice(i, 1);
    }
  }
}

function stepSmoke() {
  const now = system.currentTick;
  for (let i = smokeClouds.length - 1; i >= 0; i--) {
    const cloud = smokeClouds[i];
    if (now > cloud.until) {
      smokeClouds.splice(i, 1);
      continue;
    }
    for (let n = 0; n < 6; n++) {
      particle(cloud.dimension, "minecraft:basic_smoke_particle", {
        x: cloud.position.x + (Math.random() * 2 - 1) * CONFIG.smokeRadius,
        y: cloud.position.y + Math.random() * 2.5,
        z: cloud.position.z + (Math.random() * 2 - 1) * CONFIG.smokeRadius,
      });
    }
    if (now >= cloud.nextEffect) {
      cloud.nextEffect = now + 20;
      try {
        const inside = cloud.dimension.getEntities({
          location: cloud.position,
          maxDistance: CONFIG.smokeRadius,
          excludeFamilies: ["px_turret"],
        });
        for (const entity of inside) {
          entity.addEffect("blindness", 60, { amplifier: 0, showParticles: false });
        }
      } catch {
        /* ignorieren */
      }
    }
  }
}

/* --------------------------- Geschuetztuerme ---------------------------- */

const DIMENSION_IDS = ["overworld", "nether", "the_end"];
const turretCooldowns = new Map();

function placeTurret(player) {
  if (!ready(player, "px:turret", 10)) return;
  const origin = player.getHeadLocation();
  const direction = player.getViewDirection();

  let spot = null;
  try {
    const blockHit = player.dimension.getBlockFromRay(origin, direction, {
      maxDistance: 6,
      includePassableBlocks: false,
      includeLiquidBlocks: false,
    });
    if (blockHit?.block) {
      spot = {
        x: blockHit.block.location.x + 0.5,
        y: blockHit.block.location.y + 1,
        z: blockHit.block.location.z + 0.5,
      };
    }
  } catch {
    /* ignorieren */
  }

  if (!spot) {
    tell(player, "§cZiele auf einen Block, um den Turm zu setzen");
    return;
  }
  if (!consumeItem(player, "px:turret", 1)) return;

  try {
    player.dimension.spawnEntity("px:turret", spot);
    sound(player.dimension, "random.anvil_land", spot, 0.8, 1.4);
    tell(player, "§aGeschuetzturm aufgestellt");
  } catch {
    tell(player, "§cAufstellen fehlgeschlagen");
  }
}

function tickTurrets() {
  const now = system.currentTick;
  for (const id of DIMENSION_IDS) {
    let turrets;
    try {
      turrets = world.getDimension(id).getEntities({ type: "px:turret" });
    } catch {
      continue;
    }
    for (const turret of turrets) {
      const key = turret.id;
      if ((turretCooldowns.get(key) ?? -100000) + CONFIG.turretFireRate > now) continue;

      let target;
      try {
        target = turret.dimension
          .getEntities({
            location: turret.location,
            maxDistance: CONFIG.turretRange,
            families: ["monster"],
          })
          .sort((a, b) => dist(turret.location, a.location) - dist(turret.location, b.location))[0];
      } catch {
        continue;
      }
      if (!target) continue;

      turretCooldowns.set(key, now);

      const muzzle = { x: turret.location.x, y: turret.location.y + 0.7, z: turret.location.z };
      const aim = { x: target.location.x, y: target.location.y + 0.8, z: target.location.z };
      const direction = normalize({ x: aim.x - muzzle.x, y: aim.y - muzzle.y, z: aim.z - muzzle.z });

      try {
        turret.setRotation({
          x: -Math.asin(direction.y) * (180 / Math.PI),
          y: (Math.atan2(-direction.x, direction.z) * 180) / Math.PI,
        });
      } catch {
        /* ignorieren */
      }

      tracer(turret.dimension, muzzle, direction, dist(muzzle, aim));
      particle(turret.dimension, "minecraft:basic_flame_particle", add(muzzle, scale(direction, 0.9)));
      sound(turret.dimension, "random.bow", turret.location, 0.8, 1.8);

      dealDamage(target, CONFIG.turretDamage, "projectile", turret);
    }
  }
}

/* ------------------------------- Messer --------------------------------- */

function balisongFlip(player) {
  if (!ready(player, "px:balisong", 16)) return;
  const location = player.getHeadLocation();
  sound(player.dimension, "random.click", player.location, 1, 1.9);
  system.runTimeout(() => {
    if (alive(player)) sound(player.dimension, "random.click", player.location, 1, 1.4);
  }, 4);
  particle(player.dimension, "minecraft:critical_hit_emitter", location);
  tell(player, "§7Flip");
}

function karambitLunge(player) {
  if (!ready(player, "px:karambit", 24)) return;
  const origin = player.getHeadLocation();
  const direction = player.getViewDirection();
  sound(player.dimension, "mob.player.attack.sweep", player.location, 1, 1.2);

  for (let d = 0.5; d <= 3; d += 0.5) {
    particle(player.dimension, "minecraft:critical_hit_emitter", add(origin, scale(direction, d)));
  }

  try {
    const hits = player.dimension
      .getEntitiesFromRay(origin, direction, { maxDistance: 3.2 })
      .filter((h) => h.entity && h.entity.id !== player.id);
    for (const hit of hits.slice(0, 2)) {
      dealDamage(hit.entity, 5, "entityAttack", player);
    }
  } catch {
    /* ignorieren */
  }
}

/* ------------------------------ Anzeige --------------------------------- */

function showAmmo(player, itemId) {
  if (GUNS[itemId]) {
    tell(player, "§7Munition: §f" + countItem(player, AMMO));
  } else if (itemId === "px:bazooka") {
    tell(player, "§7Raketen: §f" + countItem(player, ROCKET));
  }
}

/* ------------------------------ Ereignisse ------------------------------ */

world.afterEvents.itemUse.subscribe((event) => {
  const player = event.source;
  const itemId = event.itemStack?.typeId;
  if (!player || !itemId) return;

  if (GUNS[itemId]) return shoot(player, itemId);
  if (GRENADES[itemId]) return throwGrenade(player, itemId);

  switch (itemId) {
    case "px:bazooka":
      return launchRocket(player);
    case "px:turret":
      return placeTurret(player);
    case "px:balisong":
      return balisongFlip(player);
    case "px:karambit":
      return karambitLunge(player);
  }
});

system.runInterval(() => {
  stepRockets();
  stepGrenades();
  stepSmoke();
}, 1);

system.runInterval(tickTurrets, 5);

/* ---------------------------------------------------------------------- *
 * Fadenkreuz                                                             *
 *                                                                        *
 * Bedrock erlaubt es nicht, aus einem Skript direkt etwas ins HUD zu      *
 * zeichnen. Der Umweg: das Skript setzt den Titeltext auf ein einzelnes   *
 * Leerzeichen (unsichtbar), und ui/hud_screen.json blendet das Fadenkreuz *
 * genau dann ein, wenn der Titeltext diesem Signal entspricht.            *
 * ---------------------------------------------------------------------- */
const CROSSHAIR_MARKER = " ";
const crosshairOn = new Set();

function heldItem(player) {
  try {
    return player.getComponent("minecraft:equippable")?.getEquipment("Mainhand");
  } catch (error) {
    problem("Handslot", String(error));
    return undefined;
  }
}

function isRanged(itemId) {
  return Boolean(GUNS[itemId]) || itemId === "px:bazooka";
}

function setCrosshair(player, wanted) {
  const active = crosshairOn.has(player.id);
  try {
    if (wanted) {
      // Regelmaessig auffrischen, damit der Titel nicht auslaeuft.
      player.onScreenDisplay.setTitle(CROSSHAIR_MARKER, {
        fadeInDuration: 0,
        stayDuration: 40,
        fadeOutDuration: 0,
      });
      crosshairOn.add(player.id);
    } else if (active) {
      player.onScreenDisplay.clearTitle();
      crosshairOn.delete(player.id);
    }
  } catch (error) {
    problem("Fadenkreuz", String(error));
  }
}

// Fadenkreuz und Munitionsanzeige, solange eine Schusswaffe in der Hand ist.
system.runInterval(() => {
  for (const player of world.getPlayers()) {
    const held = heldItem(player);
    const ranged = held ? isRanged(held.typeId) : false;
    setCrosshair(player, ranged);
    if (ranged) showAmmo(player, held.typeId);
  }
}, 10);

/* ---------------------------------------------------------------------- *
 * Befehle                                                                *
 * ---------------------------------------------------------------------- */

const RECIPE_HELP = [
  "§6PX Weapons - Rezepte§r  (Werkbank, I=Eisen S=Stock R=Redstone",
  "§7G=Glas P=Schiesspulver T=Faden C=Kohle F=Glasflasche)",
  "",
  "§ePistole§r      II / S_",
  "§eMP§r           III / SR_",
  "§eSturmgewehr§r  III / SRI",
  "§eSchrotflinte§r III / SS_",
  "§eScharfschuetze§r _G_ / III / SI_",
  "§eMinigun§r      III / IRI / SI_",
  "§eBazooka§r      III / PRI / _S_",
  "§eBalisong§r     I_ / IS",
  "§eKarambit§r     II / TS",
  "§eGeschuetzturm§r _I_ / IRI / IPI",
  "",
  "§7Formlos (Reihenfolge egal):§r",
  "§eMunition x8§r        I + P",
  "§eRakete x2§r          I + P + R",
  "§eSplittergranate x2§r I + P + P",
  "§eRauchgranate x2§r    C + C + P",
  "§eBrandflasche x2§r    F + C + T",
];

function sendDiagnosis(player) {
  const lines = [
    "§6PX Weapons " + VERSION + "§r",
    "§7Skripte laufen.§r Wenn du das siehst, ist das Behavior-Pack aktiv.",
    "Schusswaffen: §f" + Object.keys(GUNS).length + "§r",
    "Munition im Inventar: §f" + countItem(player, AMMO) + "§r",
    "Raketen im Inventar: §f" + countItem(player, ROCKET) + "§r",
    "Aktive Raketen: §f" + rockets.length + "§r, Granaten: §f" + grenades.length + "§r",
    problems.length
      ? "§cFehler (" + problems.length + "):§r " + problems.slice(0, 5).join(" | ")
      : "§aKeine Fehler aufgezeichnet.§r",
    "§7Fehlen die Texturen und heissen die Items 'item.px:...', dann ist das",
    "§7Resource-Pack nicht aktiv.§r",
  ];
  for (const line of lines) player.sendMessage(line);
}

system.afterEvents.scriptEventReceive.subscribe((event) => {
  const player = event.sourceEntity;
  const send = (line) => {
    if (player && typeof player.sendMessage === "function") player.sendMessage(line);
    else world.sendMessage(line);
  };
  if (event.id === "px:diag") {
    if (player && typeof player.sendMessage === "function") sendDiagnosis(player);
    else world.sendMessage("§6PX Weapons " + VERSION + "§r - Skripte laufen.");
  } else if (event.id === "px:recipes") {
    for (const line of RECIPE_HELP) send(line);
  } else if (event.id === "px:help") {
    send("§6PX Weapons§r - /scriptevent px:recipes  ·  /scriptevent px:diag");
  }
});

// Startmeldung: sichtbarer Beleg dafuer, dass die Skripte ueberhaupt laufen.
// Bleibt aus, wenn das Behavior-Pack oder die Skript-API fehlt.
system.run(() => {
  try {
    world.sendMessage(
      "§6PX Weapons " + VERSION + "§r geladen. §7/scriptevent px:recipes§r für Rezepte, " +
      "§7/scriptevent px:diag§r für Diagnose.");
  } catch (error) {
    console.warn("[PX Weapons] Startmeldung fehlgeschlagen: " + error);
  }
  console.warn("[PX Weapons] " + VERSION + " geladen, " +
               Object.keys(GUNS).length + " Schusswaffen aktiv");
});
