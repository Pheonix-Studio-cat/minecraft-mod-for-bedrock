/**
 * Testet die Vektor- und Streumathematik aus scripts/main.js.
 *
 * Der Code wird aus der echten Skriptdatei herausgeschnitten und ausgefuehrt,
 * damit der Test nicht auf einer Kopie arbeitet, die veralten kann.
 *
 * Ausfuehren mit:  node tools/test_math.mjs
 */
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";

const root = dirname(dirname(fileURLToPath(import.meta.url)));
const source = readFileSync(
  join(root, "behavior_packs", "px_weapons_bp", "scripts", "main.js"), "utf8");

const START = "const add = (a, b)";
const END = "/* --------------------------- Kleine Helfer";
if (!source.includes(START) || !source.includes(END)) {
  console.error("Mathematik-Block in main.js nicht gefunden - Marker geaendert?");
  process.exit(1);
}
const block = source.slice(source.indexOf(START), source.indexOf(END));
const { normalize, applySpread, dist, add, scale } =
  new Function(block + "\nreturn { normalize, applySpread, dist, add, scale };")();

let failures = 0;

function check(name, ok, info) {
  console.log((ok ? "  ok   " : "  FEHL ") + name + (info ? "  (" + info + ")" : ""));
  if (!ok) failures++;
}

const angle = (a, b) =>
  (Math.acos(Math.max(-1, Math.min(1, a.x * b.x + a.y * b.y + a.z * b.z))) * 180) / Math.PI;

// --- normalize -------------------------------------------------------------
const n = normalize({ x: 3, y: 4, z: 0 });
check("normalize liefert Laenge 1", Math.abs(Math.hypot(n.x, n.y, n.z) - 1) < 1e-12);
const zero = normalize({ x: 0, y: 0, z: 0 });
check("normalize stuerzt bei Nullvektor nicht ab", Number.isFinite(zero.x));

// --- dist ------------------------------------------------------------------
check("dist misst richtig",
      Math.abs(dist({ x: 0, y: 0, z: 0 }, { x: 3, y: 4, z: 0 }) - 5) < 1e-12);

// --- add / scale -----------------------------------------------------------
const moved = add({ x: 1, y: 2, z: 3 }, scale({ x: 1, y: 0, z: 0 }, 4));
check("add und scale rechnen zusammen richtig",
      moved.x === 5 && moved.y === 2 && moved.z === 3);

// --- applySpread -----------------------------------------------------------
// Auch fast senkrechte Blickrichtungen pruefen: dort wechselt die Hilfsachse
// fuer die orthonormale Basis.
const directions = [
  { x: 0, y: 0, z: 1 },
  { x: 1, y: 0, z: 0 },
  { x: 0.6, y: -0.5, z: 0.62 },
  { x: 0, y: 1, z: 0 },
  { x: 0.001, y: 0.9999, z: 0.001 },
  { x: 0, y: -1, z: 0 },
];

const SAMPLES = 8000;
for (const raw of directions) {
  const aim = normalize(raw);
  const label = `[${aim.x.toFixed(2)},${aim.y.toFixed(2)},${aim.z.toFixed(2)}]`;

  // Ohne Streuung muss der Schuss exakt auf das Fadenkreuz gehen.
  check(`Streuung 0 trifft exakt ${label}`, angle(aim, applySpread(aim, 0)) < 1e-5);

  for (const spread of [0.5, 2, 5]) {
    let worst = 0;
    let unit = true;
    for (let i = 0; i < SAMPLES; i++) {
      const shot = applySpread(aim, spread);
      worst = Math.max(worst, angle(aim, shot));
      if (Math.abs(Math.hypot(shot.x, shot.y, shot.z) - 1) > 1e-9) unit = false;
    }
    check(`Streuung ${spread} Grad bleibt im Kegel ${label}`,
          worst <= spread + 1e-6 && unit, `max ${worst.toFixed(3)} Grad`);
  }
}

console.log(failures ? `\n${failures} Test(s) fehlgeschlagen` : "\nAlle Tests bestanden.");
process.exit(failures ? 1 : 0);
