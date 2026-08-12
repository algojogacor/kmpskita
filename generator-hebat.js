// Generator data tombol tugas — jalan di KONSOLE browser kamu sendiri,
// saat kamu sedang di halaman HE-BAT (hebat.elearning.unair.ac.id) dan login.
// Pakai sesi login kamu; TIDAK ada kredensial yang keluar dari browser.
// Cara pakai: login HE-BAT → F12 → Console → tempel seluruh kode ini → Enter.
// Hasil: file hebat-links-<userid>.json terunduh → seret ke web kampus kita.
(async () => {
  const BASE = 'https://hebat.elearning.unair.ac.id';
  const ui = /^(Collapse|Expand)( all)?$/i;
  const BLOCKS = 'P,DIV,LI,H1,H2,H3,H4,H5,H6,BR,PRE,BLOCKQUOTE,TR'.split(',');
  const parseTitle = t => {
    const p = (t || '').split(' - ');
    return p.length >= 5
      ? { period: p[0], code: p[1], name: p[2], cls: p[p.length - 1] }
      : { period: '', code: '', name: t || '', cls: '' };
  };
  // Ekstrak sections dari dokumen kursus (logika sama dgn scripts/sync-hebat.mjs).
  // Baris baru: sisipkan '\n' di akhir tiap elemen blok — setara dgn innerText,
  // tapi tetap bekerja pada dokumen hasil DOMParser (tanpa layout).
  const extract = d => {
    const out = { sections: [] };
    d.querySelectorAll('li.section.course-section').forEach(s => {
      const item = s.querySelector('.section-item') || s;
      const nm = item.querySelector('h3.sectionname');
      const clone = item.cloneNode(true);
      clone.querySelectorAll('li.activity, .section-modchooser, button, select, .bulkselect').forEach(el => el.remove());
      clone.querySelectorAll(BLOCKS.join(',')).forEach(el => el.appendChild(d.createTextNode('\n')));
      const lines = (clone.textContent || '').split('\n').map(l => l.replace(/\s+/g, ' ').trim()).filter(l => l && !ui.test(l));
      let text = lines.join('\n');
      if (nm) { const nmt = nm.textContent.replace(/\s+/g, ' ').trim(); if (nmt) text = text.split('\n').filter(l => l !== nmt).join('\n'); }
      const acts = [];
      item.querySelectorAll('li.activity').forEach(a => {
        const al = a.querySelector('a[href]');
        if (!al) return;
        acts.push({ mod: (a.className.match(/modtype_(\w+)/) || [])[1] || '', href: al.getAttribute('href') || '', name: (al.innerText || al.textContent || '').split('\n')[0].trim().slice(0, 200) });
      });
      if (text || acts.length) out.sections.push({ name: nm ? nm.textContent.trim() : '', summary: text, activities: acts });
    });
    return out;
  };

  try {
    // 1) userid dari link profil di header
    const prof = document.querySelector('a[href*="user/profile.php?id="]');
    const uid = prof ? ((prof.getAttribute('href') || '').match(/id=(\d+)/) || [])[1] : '';
    if (!uid) throw new Error('userid tidak ditemukan — pastikan kamu sudah LOGIN HE-BAT (klik foto/avatar di pojok kanan atas)');

    // 2) daftar kursus via AJAX yang dipakai halaman HE-BAT itu sendiri
    const skm = (document.querySelector('a[href*="sesskey="]') || { href: '' }).href.match(/sesskey=([A-Za-z0-9]+)/);
    const sk = skm ? skm[1] : '';
    if (!sk) throw new Error('sesskey tidak ditemukan — muat ulang halaman HE-BAT lalu jalankan ulang');
    const body = JSON.stringify([{ index: 0, methodname: 'core_course_get_enrolled_courses_by_timeline_classification', args: { classification: 'all', limit: 0, offset: 0, sort: 'fullname', customfieldname: '', customfieldvalue: '' } }]);
    const r = await fetch('/lib/ajax/service.php?sesskey=' + sk + '&info=core_course_get_enrolled_courses_by_timeline_classification', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body });
    const j = await r.json();
    const x = j[0];
    if (x && x.error) throw new Error('daftar kursus ditolak: ' + (x.exception ? x.exception.message : 'error'));
    const list = (x.data.courses || []).map(c => ({ id: c.id, title: c.fullname }));
    console.log('HEBAT sync: ' + list.length + ' kursus');

    // 3) tiap kursus: ambil halaman + ekstrak sections (isi penugasan, aktivitas)
    const courses = [];
    for (const c of list) {
      const h = await (await fetch('/course/view.php?id=' + c.id)).text();
      const d = new DOMParser().parseFromString(h, 'text/html');
      const raw = extract(d);
      const { period, code, name, cls } = parseTitle(c.title);
      courses.push({
        id: c.id, period, code, name, class: cls,
        url: BASE + '/course/view.php?id=' + c.id,
        sections: (raw.sections || []).filter(s => !(s.name === 'General' && !s.summary && !(s.activities || []).length)),
      });
      const n = raw.sections.filter(s => (s.activities || []).some(a => a.mod === 'assign')).length;
      console.log('  - ' + c.id + ' ' + name + ' (' + raw.sections.length + ' section, ' + n + ' tugas)');
      await new Promise(rs => setTimeout(rs, 300)); // jeda kecil, ramah server
    }

    // 4) index tugas (assign)
    const tasks = [];
    const seen = new Set();
    for (const c of courses) for (const s of c.sections) for (const a of s.activities || []) {
      if (a.mod !== 'assign') continue;
      if (!seen.has(a.href)) { seen.add(a.href); tasks.push({ name: a.name, url: a.href, courseId: c.id }); }
    }
    tasks.sort((a, b) => a.name.localeCompare(b.name, 'id'));

    // 5) unduh file data tombol
    const out = {
      generated: new Date().toISOString().slice(0, 10),
      note: 'Peta kursus + tugas HE-BAT. Course-global (URL & isi sama untuk semua mahasiswa di kelas itu), BUKAN data pribadi — status kumpul/file milik user TIDAK ada di sini. courses[].sections[].summary = isi penugasan/info dari halaman kursus. Dibuat dari browser pengguna via generator-hebat.js.',
      courses, tasks,
    };
    const blob = new Blob([JSON.stringify(out, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(blob);
    a.download = 'hebat-links-' + uid + '.json';
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(a.href);
    alert('Selesai! File ' + a.download + ' terunduh (' + courses.length + ' kursus, ' + tasks.length + ' tugas).\n\nSekarang buka web kampus kita dan seret file itu ke kotak "buat tombolmu".');
  } catch (e) {
    alert('Gagal: ' + e.message + '\n\nPastikan: 1) kamu login HE-BAT, 2) kode dijalankan di halaman hebat.elearning.unair.ac.id (bukan halaman lain), 3) F12 → Console.');
    console.error(e);
  }
})();
