#!/usr/bin/env node
// Les savoirs des apps, pour DiGiSha (fable, 06.11.2026 — Patrick : « je trouve que DiGiSha n'utilise pas encore assez les
// savoirs croisés de mes app » ; « oui tu construis la marque corrigé et les 5 savoirs »).
//
// Extrait TELS QUELS les cinq savoirs les plus croisés des dépôts des apps (~/Developer) vers data/savoirs_apps.json :
// rien n'est recopié à la main, rien n'est réécrit. Chaque version porte le STADE à partir duquel elle se lit — Patrick,
// 06.11 : « les 3 savoirs ne se contredisent pas - ils sont le savoir au stade ST2, ST3 et ST4 ». Le stade d'une version
// est celui du canal de l'app qui la porte (table canal_app, relevée le 06.11 : Priv 1 à 5 et Priv Core en z2 → ST2 ;
// Ancrage Classique, Chroma 1, 2, 3 et 5 en z3 → ST3 ; Ancrage duale et Pro Core en z4 → ST4).
//
//   node scripts/extraire_savoirs_apps.mjs            # réécrit data/savoirs_apps.json
//   node scripts/extraire_savoirs_apps.mjs --verifier # dit seulement si le fichier diffère des sources
import { execFileSync } from 'node:child_process';
import { copyFileSync, mkdtempSync, readFileSync, writeFileSync } from 'node:fs';
import { tmpdir, homedir } from 'node:os';
import { basename, dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const DEV = join(homedir(), 'Developer');
const SORTIE = join(dirname(fileURLToPath(import.meta.url)), '..', 'data', 'savoirs_apps.json');

// ── Les sources : dépôt, chemin, app qui la montre, stade ─────────────────────────────────────────────────────────
const S = {
  roseVifa: ['SVLBH-VIFA-essentielles', 'SVLBH VIFA essentielles/Data/roseDesVentsDirs.js', 'SVLBH Priv 4 VIFA', 2],
  roseApres: ['svlbh-cercle-lumiere-mac', 'Sources/SVLBHCercleLumiere/Panel/Views/EtApresTab.swift',
              'Ancrage Conscience Classique · Chroma 5 (page « Et après »)', 3],
  lmascVifa: ['SVLBH-VIFA-essentielles', 'SVLBH VIFA essentielles/Data/typesDE_Lmasc.js', 'SVLBH Priv 4 VIFA', 2],
  lmascChroma2: ['vlbh-chroma2-thyro', 'App/Data/typesDE_Lmasc.json', 'VLBH Chroma 2 Thyro', 3],
  sephArbre: ['svlbh-core-android', 'src/palette-chromatique/sephirothModel.ts', 'Palette Chromatique (Priv 3 Palette et socle)', 2],
  sephNoms: ['svlbh-core-android', 'src/components/HotlineSidebar.tsx', 'Hotline (socle)', 2],
  tores: ['svlbh-demandes', 'Sources/SVLBHPriv1/Models/SephiraModel.swift', 'SVLBH Priv-1 (Tores de Lumière)', 2],
  wuShen: ['svlbh-vifa-android', 'src/data/wuShen.ts', 'SVLBH Priv 4 VIFA', 2],
  dpmVifa: ['svlbh-vifa-android', 'src/data/dpm.ts', 'SVLBH Priv 4 VIFA', 2],
  dpmPro: ['svlbh-pro-core-android', 'src/dpmPattern.ts', 'SVLBH Pro Core', 4],
  dimAncrage: ['svlbh-cercle-android', 'src/data/dimensions.ts', 'Ancrage Conscience Classique', 3],
  dimModeles: ['svlbh-pro-core-android', 'src/dimensionModels.ts', 'SVLBH Pro Core', 4],
  chakrasPro: ['svlbh-pro-core-android', 'src/chakraCatalog.ts', 'SVLBH Pro Core', 4],
  portes: ['svlbh-core', 'Sources/SVLBHCore/Models/SVLBHPorteEnergetique.swift', 'Portes énergétiques (socle)', 2],
};

const chemin = (k) => join(DEV, S[k][0], S[k][1]);
const lire = (k) => readFileSync(chemin(k), 'utf8');
function commit(k) {
  try {
    return execFileSync('git', ['-C', join(DEV, S[k][0]), 'log', '-1', '--format=%h %cs', '--', S[k][1]], { encoding: 'utf8' }).trim();
  } catch { return ''; }
}
const version = (k, nom, entrees) => ({
  stade: S[k][3], app: S[k][2], nom, source: `${S[k][0]}/${S[k][1]}`, commit: commit(k), entrees,
});

// Un module JS/TS se lit par Node depuis une copie (les types TypeScript sont retirés par Node lui-même).
const COPIES = mkdtempSync(join(tmpdir(), 'savoirs-'));
async function module_(...cles) {
  for (const k of cles) copyFileSync(chemin(k), join(COPIES, basename(S[k][1])));
  return import(join(COPIES, basename(S[cles[0]][1])));
}

// ── Swift : les appels Type(clé: valeur, …) d'un tableau, valeurs littérales seulement ────────────────────────────
function chaineSwift(s) {
  return s.replace(/\\u\{([0-9a-fA-F]+)\}/g, (_, h) => String.fromCodePoint(parseInt(h, 16)))
          .replace(/\\"/g, '"').replace(/\\n/g, '\n').replace(/\\\\/g, '\\');
}
function appelsSwift(texte, type, debut = 0, fin = texte.length) {
  const zone = texte.slice(debut, fin), sortie = [];
  const re = new RegExp(`(?:\\b${type}|\\.init)\\(`, 'g');
  let m;
  while ((m = re.exec(zone))) {
    let i = m.index + m[0].length, prof = 1, dans = false;
    const d = i;
    for (; i < zone.length && prof > 0; i++) {
      const c = zone[i];
      if (dans) { if (c === '\\') i++; else if (c === '"') dans = false; continue; }
      if (c === '"') dans = true; else if (c === '(') prof++; else if (c === ')') prof--;
    }
    const args = zone.slice(d, i - 1), obj = {};
    const reArg = /(\w+)\s*:\s*("(?:[^"\\]|\\.)*"|-?\d+(?:\.\d+)?|true|false|nil)/g;
    let a;
    // seulement les arguments de premier niveau : on retire les appels imbriqués (Color(hex: …)) avant de lire
    const plat = args.replace(/\w+\((?:[^()"]|"(?:[^"\\]|\\.)*")*\)/g, 'X');
    while ((a = reArg.exec(plat))) {
      const v = a[2];
      obj[a[1]] = v.startsWith('"') ? chaineSwift(v.slice(1, -1)) : v === 'true' ? true : v === 'false' ? false
        : v === 'nil' ? null : Number(v);
    }
    // les hex de Color(hex: "…") sont gardés sous le nom de l'argument
    const reCouleur = /(\w+)\s*:\s*Color\(hex:\s*"([^"]+)"\)/g;
    let c2;
    while ((c2 = reCouleur.exec(args))) if (!(c2[1] in obj)) obj[c2[1]] = c2[2];
    if (Object.keys(obj).length) sortie.push(obj);
    re.lastIndex = i;
  }
  return sortie;
}
function tableauSwift(texte, nom, type) {
  const d = texte.search(new RegExp(`\\b(?:let|var)\\s+${nom}\\s*:`));
  if (d < 0) throw new Error(`tableau Swift introuvable : ${nom}`);
  const ouvre = texte.indexOf('[', texte.indexOf('=', d));
  let i = ouvre + 1, prof = 1, dans = false;
  for (; i < texte.length && prof > 0; i++) {
    const c = texte[i];
    if (dans) { if (c === '\\') i++; else if (c === '"') dans = false; continue; }
    if (c === '"') dans = true; else if (c === '[') prof++; else if (c === ']') prof--;
  }
  return appelsSwift(texte, type, ouvre, i);
}

// ── Les cinq savoirs ──────────────────────────────────────────────────────────────────────────────────────────────
async function rose() {
  const { DIRS } = await module_('roseVifa');
  const apres = tableauSwift(lire('roseApres'), 'roseDirections', 'RoseDirection');
  return {
    titre: 'Rose des Vents du Hara',
    description: 'Directions de la Rose des Vents : azimut, plan anatomique, associations (karmique, transgénérationnel, '
      + 'multiverses, famille, monde extérieur…) et points d\'acupression ; puis élément, saison, organe et thème de chaque direction.',
    versions: [
      version('roseVifa', '16 directions · plan transverse, associations et points', DIRS.map((d) => ({ cle: d.label, ...d }))),
      version('roseApres', '12 directions · élément, saison, organe, thème', apres.map(({ id, colorId, ...d }) => ({ cle: d.abbr, ...d }))),
    ],
  };
}

async function lmasc() {
  const { ALL_TYPES_DE_LMASC } = await module_('lmascVifa');
  const vide = (t) => !t.nom_fr || /à compléter|placeholder/i.test(String(t.nom_fr));
  const vifa = ALL_TYPES_DE_LMASC.filter((t) => !vide(t));
  const chroma2 = JSON.parse(lire('lmascChroma2')).filter((t) => !vide(t));
  return {
    titre: 'Types de Décodage Énergétique de la Lignée masculine (Lmasc)',
    memes_cles: true,      // un type porte la même clé dans VIFA et dans Chroma 2 : le stade le plus haut remplace
    description: 'Les types DE Lmasc organe par organe (Reins KI, Foie LR, Rate SP) : conflits Hamer, Sabbah, Séphiroth et '
      + 'Lmasc, émotion MTC, élément, méridiens, points clés, heure, dimension et porte Phantom, chakras, Gu, gel couleur, '
      + 'direction et points de la Rose des Vents.',
    versions: [
      version('lmascVifa', `${vifa.length} types renseignés`, vifa.map((t) => ({ cle: t.typeId, ...t }))),
      version('lmascChroma2', `${chroma2.length} types renseignés`, chroma2.map((t) => ({ cle: t.typeId, ...t }))),
    ],
  };
}

async function sephiroth() {
  const arbre = await module_('sephArbre');
  const tsx = lire('sephNoms');
  const bloc = tsx.slice(tsx.indexOf('const SEPH_NAMES'));
  const objet = bloc.slice(bloc.indexOf('= {') + 2, bloc.indexOf('\n};') + 2);
  const noms = Function(`"use strict"; return (${objet});`)();
  const swift = lire('tores');
  const parId = Object.fromEntries(arbre.SEPHIROTH.map((s) => [s.id, s.name]));
  const attributions = Object.entries(arbre.DEFAULT_ATTRIBUTIONS)
    .map(([hex, ids]) => ({ cle: hex, teinte: hex, sephiroth: ids.map((i) => parId[i] ?? i),
                            concept: arbre.CONCEPT_TAGS[hex] ?? null }));
  const concepts = Object.entries(arbre.CONCEPT_TAGS).filter(([hex]) => !(hex in arbre.DEFAULT_ATTRIBUTIONS))
    .map(([hex, c]) => ({ cle: hex, teinte: hex, sephiroth: [], concept: c }));
  return {
    titre: 'Arbre des Séphiroth chromatique et Tores de Lumière',
    description: 'Les dix séphirah : nom, Monde, thème de transgression, chemins ; les teintes de la Palette attribuées à '
      + 'chaque séphirah et leurs concepts ; les Tores de Lumière (élément, côté, Monde kabbalistique, planète, métal), les '
      + 'sept Rayons (qualité, couleur) et les émotions EM (organe, méridien, couleur).',
    versions: [
      version('sephNoms', 'Séphiroth : nom, Monde, thème', Object.entries(noms).map(([id, v]) => ({ cle: v.name, numero: Number(id), ...v }))),
      version('sephArbre', 'Arbre chromatique : teintes attribuées et concepts', [...attributions, ...concepts,
        ...arbre.SEPHIROTH_PATHS.map(([a, b]) => ({ cle: `chemin ${parId[a]}–${parId[b]}`, chemin: [parId[a], parId[b]] }))]),
      version('tores', 'Tores de Lumière : séphirah, Rayons, émotions EM', [
        ...tableauSwift(swift, 'SEPHIROTH', 'Sephira').map(({ x, y, color, stroke, ...s }) => ({ cle: s.nom, genre: 'séphirah', ...s })),
        ...tableauSwift(swift, 'RAYONS', 'Rayon').map(({ color, ...r }) => ({ cle: `Rayon ${r.num}`, genre: 'rayon', ...r })),
        ...tableauSwift(swift, 'EMOTIONS_EM', 'EmotionEM').map(({ color, editable, ...e }) => ({ cle: e.meridien, genre: 'émotion EM', ...e })),
      ]),
    ],
  };
}

async function wuShen() {
  const w = await module_('wuShen');
  const vifa = await module_('dpmVifa');
  const pro = await module_('dpmPro');
  const dpm = (p) => ({ cle: p.id, ...p });
  return {
    titre: 'Wu Shen et DynaPathoMu',
    description: 'Les cinq esprits Wu Shen (organe, élément, émotion, vertu, sens, tissu, saison, psyché, pathologie, Gu '
      + 'associé, risque de fragmentation), les vingt paires d\'esprits (cycle Sheng/Ke, dynamique d\'organe, cascade '
      + 'émotionnelle, pathologie croisée, pierre, axe méridien) et les cascades pathologiques DynaPathoMu (signature, '
      + 'transmission, impact, libération, restauration).',
    versions: [
      version('wuShen', 'Les 5 esprits et leurs 20 paires', [
        ...w.wuShen.map((e) => ({ cle: e.id, genre: 'esprit', ...e })),
        ...Object.entries(w.PAIR_DATA).map(([paire, p]) => ({ cle: paire, genre: 'paire', ...p })),
      ]),
      version('dpmVifa', `DynaPathoMu · ${vifa.dpmPatterns.length} cascades`, vifa.dpmPatterns.map(dpm)),
      version('dpmPro', `DynaPathoMu · ${pro.DPMPattern.all.length} cascades`, pro.DPMPattern.all.map(dpm)),
    ],
  };
}

async function hdom() {
  const anc = await module_('dimAncrage');
  const pro = await module_('chakrasPro', 'dimModeles');
  const portesSwift = lire('portes');
  const dims = (liste) => liste.flatMap((d) => [
    { cle: d.label, genre: 'dimension', num: d.num, label: d.label, description: d.description },
    ...(d.chakras ?? []).map((c) => ({ cle: `${d.label.split(' ')[0]} #${c.num ?? '–'} ${c.nom}`, genre: 'chakra',
      dimension: d.label, num: c.num, nom: c.nom, issues: c.issues?.length ? c.issues : undefined,
      cim: c.cimCodes?.length ? c.cimCodes : undefined })),
  ]);
  return {
    titre: 'Chakras hDOM par dimension et portes Phantom',
    description: 'Les dimensions (D1 à D9, D22, D99) et leurs chakras numérotés avec leurs enjeux et codes CIM ; les '
      + 'programmes de protection Gui ; les portes énergétiques d\'entrée, temporaires et permanentes (point, condition, statut).',
    versions: [
      version('portes', 'Portes énergétiques d\'entrée', [
        ...appelsSwift(portesSwift, 'PorteEnergetique').filter((p) => p.point !== undefined)
          .map((p) => ({ cle: p.point || p.nom, genre: p.isPermanent ? 'porte permanente' : 'porte temporaire', ...p })),
        ...appelsSwift(portesSwift, 'PorteChakraInfo').map((c) => ({ cle: c.sanskrit, genre: 'chakra des portes', ...c })),
      ]),
      version('dimAncrage', `Dimensions d'Ancrage · ${anc.DIMENSIONS.length}`, [
        ...dims(anc.DIMENSIONS),
        ...anc.PROGRAMMES_PROTECTION_GUI.map((p) => ({ cle: p.label, genre: 'programme de protection Gui', ...p })),
      ]),
      version('chakrasPro', `Catalogue Pro Core · ${pro.DimensionCatalog.all.length} dimensions`, dims(pro.DimensionCatalog.all)),
    ],
  };
}

const savoirs = {
  rose_des_vents: await rose(),
  types_de_lmasc: await lmasc(),
  sephiroth_chromatique: await sephiroth(),
  wu_shen_dynapathomu: await wuShen(),
  hdom_phantom: await hdom(),
};
const texte = JSON.stringify({ genere_par: 'scripts/extraire_savoirs_apps.mjs', savoirs }, null, 1) + '\n';
if (process.argv.includes('--verifier')) {
  let avant = '';
  try { avant = readFileSync(SORTIE, 'utf8'); } catch {}
  console.log(avant === texte ? 'à jour' : 'DIFFÈRE des sources — relancer sans --verifier');
  process.exit(avant === texte ? 0 : 1);
}
writeFileSync(SORTIE, texte);
for (const [id, s] of Object.entries(savoirs))
  console.log(id.padEnd(22), s.versions.map((v) => `ST${v.stade} ${v.entrees.length}`).join(' · '));
console.log(`→ ${SORTIE} (${texte.length} car.)`);
