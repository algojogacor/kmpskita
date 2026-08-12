// Sync hebat-links.json — crawler kursus HE-BAT via Kimi WebBridge
// (butuh: daemon jalan + Chrome sudah login HE-BAT).
// 1) /my/courses.php -> daftar kursus (id + nama)
// 2) tiap halaman kursus -> section (nama + summary = isi penugasan/info) + aktivitas
// 3) tulis hebat-links.json (courses + index tasks). Jalankan: node scripts/sync-hebat.mjs
import { readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const DAEMON = 'http://127.0.0.1:10086/command';
const SESSION = 'hebat-sync';
const here = dirname(fileURLToPath(import.meta.url));
const linksFile = resolve(here, '../hebat-links.json');
const BASE = 'https://hebat.elearning.unair.ac.id';

async function cmd(action, args = {}) {
  const r = await fetch(DAEMON, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ action, args, session: SESSION }),
  });
  const j = await r.json();
  if (!j.ok) throw new Error(JSON.stringify(j.error || j));
  return j.data;
}
const sleep = ms => new Promise(r => setTimeout(r, ms));

// Extract halaman kursus: per section -> {name, summary, activities:[{mod,href,name}]}.
// (Hindari regex dengan \/ di kode yang dievaluasi — daemon menolaknya.)
// innerText section berisi baris tombol UI ("Collapse"/"Expand"/"Collapse all")
// di awal & akhir. Solusi: klon section, buang elemen aktivitas + tombol,
// sisanya = nama section + baris summary asli (paragraf dosen dipertahankan).
const EXTRACT = `(() => {
  const ui = /^(Collapse|Expand)( all)?$/i;
  const out = {sections: []};
  document.querySelectorAll('li.section.course-section').forEach(s => {
    const item = s.querySelector('.section-item') || s;
    const nm = item.querySelector('h3.sectionname');
    const clone = item.cloneNode(true);
    clone.querySelectorAll('li.activity, .section-modchooser, button, select, .bulkselect').forEach(el => el.remove());
    const lines = (clone.innerText || '').split('\\n').map(l => l.replace(/\\s+/g, ' ').trim()).filter(l => l && !ui.test(l));
    let text = lines.join('\\n');
    if (nm) { const nmt = nm.innerText.replace(/\\s+/g, ' ').trim(); if (nmt) text = text.split('\\n').filter(l => l !== nmt).join('\\n'); }
    const acts = [];
    item.querySelectorAll('li.activity').forEach(a => {
      const al = a.querySelector('a[href]');
      if (!al) return;
      acts.push({ mod: (a.className.match(/modtype_(\\w+)/) || [])[1] || '', href: al.getAttribute('href') || '', name: (al.innerText || '').split('\\n')[0].trim().slice(0, 200) });
    });
    if (text || acts.length) out.sections.push({ name: nm ? nm.innerText.trim() : '', summary: text, activities: acts });
  });
  return JSON.stringify(out);
})()`;

// Daftar kursus via AJAX Moodle (lib/ajax/service.php) — lebih andal daripada
// scrape DOM: /my/courses.php me-render kartu secara lazy (terhambat di tab
// background), tapi API ini balik langsung: [{id, title=fullname}].
// Method dipakai halaman itu sendiri (terbukti dari performance entries).
const LIST_CODE = `(async () => {
  const m = (document.querySelector('a[href*="sesskey="]') || {href: ''}).href.match(/sesskey=([A-Za-z0-9]+)/);
  const sk = m ? m[1] : '';
  const url = '/lib/ajax/service.php?sesskey=' + sk + '&info=core_course_get_enrolled_courses_by_timeline_classification';
  const body = JSON.stringify([{index: 0, methodname: 'core_course_get_enrolled_courses_by_timeline_classification', args: {classification: 'all', limit: 0, offset: 0, sort: 'fullname', customfieldname: '', customfieldvalue: ''}}]);
  const r = await fetch(url, {method: 'POST', headers: {'Content-Type': 'application/json'}, body});
  const j = await r.json();
  const x = j[0];
  if (x && x.error) return JSON.stringify({error: x.exception ? x.exception.message : 'error'});
  return JSON.stringify((x.data.courses || []).map(c => ({id: c.id, title: c.fullname})));
})()`;

// "2026Ganjil - FHK25601032 - Hak Asasi Manusia - S1 - Ilmu Hukum - 2025 - A-2"
const parseTitle = t => {
  const p = (t || '').split(' - ');
  return p.length >= 5
    ? { period: p[0], code: p[1], name: p[2], class: p[p.length - 1] }
    : { period: '', code: '', name: t || '', class: '' };
};

async function evalJson(code) {
  return JSON.parse((await cmd('evaluate', { code })).value);
}
// sesskey ada di header (server-rendered) — halaman apa pun di HEBAT cukup.
async function waitCourseList() {
  for (let i = 0; i < 10; i++) {
    const list = await evalJson(LIST_CODE);
    if (Array.isArray(list) && list.length) return list;
    if (Array.isArray(list) && list.length === 0 && i >= 5) return [];
    await sleep(1000);
  }
  return [];
}

await cmd('navigate', { url: BASE + '/my/', newTab: true, group_title: 'Sync HE-BAT' });
const list = await waitCourseList();
if (!Array.isArray(list)) throw new Error('gagal ambil daftar kursus: ' + JSON.stringify(list));
console.log(`kursus terdaftar (AJAX): ${list.length}`);

const courses = [];
for (const c of list) {
  await cmd('navigate', { url: `${BASE}/course/view.php?id=${c.id}` });
  let raw = { sections: [] };
  for (let i = 0; i < 15; i++) {
    raw = await evalJson(EXTRACT);
    if (raw.sections.length) break; // halaman kursus sudah ter-render
    await sleep(1000);
  }
  const { period, code, name, class: cls } = parseTitle(c.title);
  courses.push({
    id: c.id, period, code, name, class: cls,
    url: `${BASE}/course/view.php?id=${c.id}`,
    sections: (raw.sections || []).filter(s => !(s.name === 'General' && !s.summary && !(s.activities || []).length)),
  });
  const acts = (raw.sections || []).flatMap(s => s.activities || []).filter(a => a.mod === 'assign');
  console.log(`- ${c.id} ${code} ${name}: ${acts.length} tugas, ${(raw.sections || []).length} section`);
}

// index tugas (assign) + merge dengan data lama (jangan sampai hilang kalau crawl terlewat)
const cur = JSON.parse(readFileSync(linksFile, 'utf8'));
const seenUrl = new Set(cur.tasks.map(t => t.url));
const tasks = [];
const byUrl = new Map();
for (const c of courses) {
  for (const s of c.sections) {
    for (const a of s.activities || []) {
      if (a.mod !== 'assign') continue;
      if (!byUrl.has(a.href)) byUrl.set(a.href, { name: a.name, url: a.href, courseId: c.id });
    }
  }
}
let added = 0;
for (const t of cur.tasks) {
  if (byUrl.has(t.url)) continue;
  byUrl.set(t.url, t); // tugas lama yang tak ada di crawl: pertahankan
}
for (const t of byUrl.values()) {
  tasks.push(t);
  if (!seenUrl.has(t.url)) added++;
}
tasks.sort((a, b) => a.name.localeCompare(b.name, 'id'));

const out = { generated: new Date().toISOString().slice(0, 10), note: cur.note, courses, tasks };
writeFileSync(linksFile, JSON.stringify(out, null, 2) + '\n');
console.log(`hebat-links.json: ${courses.length} kursus, ${tasks.length} tugas (baru: ${added})`);
for (const t of tasks) console.log('-', t.name, '->', t.url);
await cmd('close_tab', {});
