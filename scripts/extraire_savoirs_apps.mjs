#!/usr/bin/env node
// Les savoirs des apps, pour DiGiSha (fable, 06.11.2026 — Patrick : « je trouve que DiGiSha n'utilise pas encore assez les
// savoirs croisés de mes app » ; « oui tu construis la marque corrigé et les 5 savoirs »).
//
// Extrait TELS QUELS les six savoirs les plus croisés des dépôts des apps (~/Developer) vers data/savoirs_apps.json :
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
  // 07.11.2026 — Patrick : « j'ai besoin que DiGiSha puisse apprendre le savoir des faces Dodécaèdre qui contient l'app
  // svlbh-pro-1 - la face 5 fenêtre 7h-9h Na Zi Fa Chén 5ème des 12 branches terrestres ». Trois niveaux, GATÉS par stade
  // (DEC Patrick 04.08.2026 : Niveau 1 = ST2 · Niveau 2 = ST3 · Niveau 3 = ST5) : le stade de la version est celui du niveau.
  dodeca: ['svlbh-core', 'Sources/SVLBHCore/Models/SVLBHEarthlyBranches.swift', 'VLBH Chroma 5 Abondance (dodécaèdre)', 2],
  dodecaVue: ['svlbh-pro-1', 'ios-app/SVLBHPro1App/Dodecaedre/PentagonEditorView.swift', 'VLBH Chroma 5 Abondance (dodécaèdre)', 5],
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

// ── Le dodécaèdre : les 12 faces = les 12 branches terrestres ─────────────────────────────────────────────────────
// Le fichier Swift du socle est COMPILÉ tel quel (swiftc) et écrit lui-même ses douze faces : aucune table recopiée.
const GEN_DODECA = `import Foundation
struct Face: Encodable { let face: Int; let branche: String; let rang: String; let fenetre: String; let meridien: String
  let meridien_fr: String; let element: String; let grenier: Bool; let harmonie: String; let opposition: String
  let triangle: String; let linggui: Int }
struct Sortie: Encodable { let faces: [Face]; let pointes: [String]; let contraintes: [String]; let appariement: String
  let formule: String; let diviseur: String; let reste: String; let provenance: String; let confluence: [String]
  let but: String; let valeurs: [[String]]; let niveaux: [[String]] }
let s = Sortie(
  faces: EarthlyBranch.allCases.map { b in Face(face: b.face, branche: b.title, rang: b.rankLabel, fenetre: b.hourLabel,
    meridien: b.meridianCode, meridien_fr: b.meridianLabel, element: b.elementLabel, grenier: b.isEarthGranary,
    harmonie: b.harmony.title, opposition: b.opposition.title, triangle: b.triangleLabel, linggui: b.lingguiValue) },
  pointes: DodecaedreDoctrine.pointes, contraintes: DodecaedreDoctrine.contraintes, appariement: DodecaedreDoctrine.appariement,
  formule: LingguiBafa.formula, diviseur: LingguiBafa.divisor, reste: LingguiBafa.remainderRule,
  provenance: LingguiBafa.provenance, confluence: LingguiBafa.confluentPoints, but: LingguiBafa.purpose,
  valeurs: LingguiBafa.valueGroups.map { ["\\($0.value)", $0.stems, $0.branches] },
  niveaux: SavoirNiveau.allCases.map { [$0.titre, $0.stadeLabel, $0.destinataire] })
let e = JSONEncoder(); e.outputFormatting = [.sortedKeys]
print(String(data: try! e.encode(s), encoding: .utf8)!)
`;

// Les phrases d'un bloc("<titre>", [ … ]) de l'écran de Chroma 5, telles quelles (concaténations Swift jointes).
function blocVue(swift, titre) {
  const debut = swift.indexOf(`bloc("${titre}", [`);
  if (debut < 0) throw new Error(`bloc introuvable dans l'écran du dodécaèdre : ${titre}`);
  let i = swift.indexOf('[', debut) + 1, prof = 1, dans = false, cour = '', elements = [], lit = '';
  for (; i < swift.length && prof > 0; i++) {
    const c = swift[i];
    if (dans) { if (c === '\\' && swift[i + 1] === '"') { lit += '"'; i++; } else if (c === '"') { dans = false; cour += lit; lit = ''; } else lit += c; continue; }
    if (c === '"') dans = true;
    else if (c === '[' || c === '(') prof++;
    else if (c === ']' || c === ')') prof--;
    else if (c === ',' && prof === 1) { elements.push(cour); cour = ''; }
  }
  if (cour) elements.push(cour);
  return elements.map((e) => e.trim()).filter(Boolean);
}

async function dodecaedre() {
  writeFileSync(join(COPIES, 'main.swift'), GEN_DODECA);
  const bin = join(COPIES, 'dodeca');
  execFileSync('swiftc', ['-O', chemin('dodeca'), join(COPIES, 'main.swift'), '-o', bin], { stdio: ['ignore', 'ignore', 'inherit'] });
  const d = JSON.parse(execFileSync(bin, { encoding: 'utf8' }));
  const source = lire('dodeca');
  const doctrine = (source.match(/Doctrine validée par Patrick[\s\S]*?portail du miroir\./) || [''])[0].replace(/\n\/\/\s*/g, ' ');
  const vue = lire('dodecaVue');
  const porte = blocVue(vue, "La branche comme porte d'organe");
  const modes = blocVue(vue, "Les deux modes d'ouverture");
  const pourFace = (t, f) => t.replace(/\\\(branch\.title\)/g, f.branche).replace(/\\\(branch\.meridianCode\)/g, f.meridien)
    .replace(/\\\(branch\.hourLabel\)/g, f.fenetre);
  const cle = (f) => `Face ${f.face} — ${f.branche}`;
  const n1 = (f) => ({ cle: cle(f), face: f.face, branche: f.branche, rang: f.rang, fenetre: `${f.fenetre} (Na Zi Fa)`,
    meridien: `${f.meridien} — ${f.meridien_fr}`, ligne_du_temps: `face ${f.face} du dodécaèdre`,
    la_face: [`5 pointes — ${d.pointes.join(' · ')}`, '5 arêtes — les 5 Wu-Shen'], ce_que_la_geometrie_impose: d.contraintes });
  const n2 = (f) => ({ ...n1(f), element: f.element,
    ...(f.grenier ? { terre: 'Branche de Terre — charnière de saison. Dite « grenier » ou « tombe » : elle absorbe et stocke la '
      + "mémoire de l'élément qui s'achève. Nuance déterminante en décodage." } : {}),
    harmonie_六合: f.harmonie, opposition_六沖: f.opposition, triangle_三合: f.triangle, appariement: d.appariement });
  const n3 = (f) => ({ ...n2(f), porte_d_organe: porte.map((t) => pourFace(t, f)), modes_d_ouverture: modes,
    linggui_bafa: { calcul: [d.formule, d.diviseur, d.reste], valeur_de_la_branche: f.linggui,
      valeurs: d.valeurs.map(([v, troncs, branches]) => `${v} = ${troncs} / ${branches}`), provenance: d.provenance },
    points_de_confluence: d.confluence, but: d.but });
  const doc = { cle: 'Dodécaèdre — les 12 faces', doctrine, niveaux: d.niveaux.map(([t, st, qui]) => `${t} : à partir de ${st} — ${qui}`) };
  const niveau = (nom, stade, faire) => ({ ...version('dodeca', nom, [doc, ...d.faces.map(faire)]), stade });
  return {
    titre: 'Dodécaèdre — les 12 faces, les 12 branches terrestres (地支) et le Linggui Bafa',
    memes_cles: true,      // une face porte la même clé aux trois niveaux : le niveau le plus haut lisible la remplace
    description: 'Les 12 faces pentagonales du dodécaèdre de Chroma 5 = les 12 branches terrestres = les 12 lignes des temps : '
      + 'branche (Zǐ…Hài), rang, fenêtre horaire Na Zi Fa et méridien (face 5 = 辰 Chén, 7 h – 9 h, ST Estomac) ; puis '
      + "élément, branches de Terre, harmonies 六合, oppositions 六沖, triangles 三合 ; puis l'usage opératoire : porte "
      + "d'organe, Na Zi / Na Jia, calcul Linggui Bafa, points de confluence.",
    versions: [
      niveau("Niveau 1 — L'image (face, branche, fenêtre, méridien)", 2, n1),
      niveau('Niveau 2 — La structure (élément, harmonie, opposition, triangle)', 3, n2),
      { ...niveau("Niveau 3 — L'usage opératoire (porte d'organe, Na Zi / Na Jia, Linggui Bafa)", 5, n3),
        source: `${S.dodeca[0]}/${S.dodeca[1]} · ${S.dodecaVue[0]}/${S.dodecaVue[1]}` },
    ],
  };
}

const savoirs = {
  rose_des_vents: await rose(),
  types_de_lmasc: await lmasc(),
  sephiroth_chromatique: await sephiroth(),
  wu_shen_dynapathomu: await wuShen(),
  hdom_phantom: await hdom(),
  dodecaedre_branches: await dodecaedre(),
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
