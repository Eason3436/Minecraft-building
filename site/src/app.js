// 方塊建築館：hash 路由（#/、#/b/<slug>[/<版本>[/<模型>]]）、首頁目錄、建築頁。
const app = document.getElementById('app');
const isTouch = matchMedia('(pointer: coarse)').matches;
let catalog = null;
let page = null; // 目前建築頁狀態
const homeState = { q: '', tag: '全部', scroll: 0 };

// ---------------------------------------------------------------- 小工具
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const h = (html) => { const t = document.createElement('template'); t.innerHTML = html.trim(); return t.content.firstElementChild; };
function fmtNum(n) {
  if (n >= 1e8) return (n / 1e8).toFixed(2).replace(/\.?0+$/, '') + ' 億';
  if (n >= 1e4) return (n / 1e4).toFixed(n >= 1e6 ? 0 : 1).replace(/\.0$/, '') + ' 萬';
  return n.toLocaleString('zh-TW');
}
const fmtInt = (n) => n.toLocaleString('zh-TW');
function fmtBytes(b) {
  if (b >= 1048576) return (b / 1048576).toFixed(1) + ' MB';
  return Math.max(1, Math.round(b / 1024)) + ' KB';
}
const dimText = (s) => `${s[0]} × ${s[2]} × ${s[1]}`;
const dimLong = (s) => `寬 ${s[0]} × 深 ${s[2]} × 高 ${s[1]}`;
function toast(msg) {
  const t = document.getElementById('toast');
  t.textContent = msg; t.classList.add('show');
  clearTimeout(toast._t); toast._t = setTimeout(() => t.classList.remove('show'), 1600);
}
async function copyText(text) {
  try { await navigator.clipboard.writeText(text); }
  catch {
    const ta = document.createElement('textarea'); ta.value = text; ta.style.position = 'fixed'; ta.style.opacity = '0';
    document.body.appendChild(ta); ta.select();
    try { document.execCommand('copy'); } catch { /* 無法複製 */ }
    ta.remove();
  }
  toast('已複製');
}
document.addEventListener('click', (e) => {
  const b = e.target.closest('[data-copy]');
  if (b) { e.preventDefault(); copyText(b.dataset.copy); }
});

const ICONS = {
  rotate: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12a9 9 0 1 1-2.64-6.36"/><path d="M21 3v6h-6"/></svg>',
  reset: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3 4 7.5v9L12 21l8-4.5v-9Z"/><path d="m4 7.5 8 4.5 8-4.5M12 12v9"/></svg>',
  fs: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M8 3H3v5M16 3h5v5M8 21H3v-5M16 21h5v-5"/></svg>',
  fsExit: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 8h5V3M21 8h-5V3M3 16h5v5M21 16h-5v5"/></svg>',
  download: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 3v12m0 0-5-5m5 5 5-5M4 19h16"/></svg>',
  doc: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 3H6v18h12V7Z"/><path d="M14 3v4h4M9 12h6M9 16h6"/></svg>',
  img: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="16" rx="2"/><circle cx="9" cy="10" r="2"/><path d="m21 17-5-5-9 8"/></svg>',
  search: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
};

// ---------------------------------------------------------------- 路由
function parseRoute() {
  const p = location.hash.replace(/^#\/?/, '').split('/').filter(Boolean).map(decodeURIComponent);
  if (p[0] === 'b' && p[1]) return { name: 'building', slug: p[1], ver: p[2] || null, model: p[3] || null };
  return { name: 'home' };
}
async function route() {
  if (!catalog) {
    try {
      const r = await fetch('catalog.json', { cache: 'no-cache' });
      if (!r.ok) throw new Error('HTTP ' + r.status);
      catalog = await r.json();
    } catch (e) {
      app.innerHTML = `<p class="notice">無法載入建築目錄（${esc(e.message)}）。請重新整理頁面。</p>`;
      return;
    }
  }
  const r = parseRoute();
  if (r.name === 'building') {
    const b = catalog.buildings.find((x) => x.slug === r.slug);
    if (!b) { leaveBuilding(); renderNotFound(); return; }
    if (page && page.b === b) { page.select(r.ver, r.model); return; }
    leaveBuilding();
    renderBuilding(b, r.ver, r.model);
  } else {
    if (page) leaveBuilding();
    renderHome();
  }
}
window.addEventListener('hashchange', route);

function leaveBuilding() {
  if (!page) return;
  page.dispose();
  page = null;
}
function renderNotFound() {
  document.title = '找不到建築｜方塊建築館';
  app.innerHTML = `<div class="empty"><p>找不到這棟建築。</p><p><a href="#/">回到全部建築</a></p></div>`;
}

// ---------------------------------------------------------------- 首頁
const TAG_ORDER = ['全部', '建築', '鐵道', '載具', '紅石', '橋梁'];
function renderHome() {
  document.title = '方塊建築館｜Minecraft 基岩版建築作品集';
  const bs = catalog.buildings;
  const totalBlocks = bs.reduce((t, b) => t + b.versions.reduce((u, v) => u + v.blocks, 0), 0);
  const nVer = bs.reduce((t, b) => t + b.versions.length, 0);
  const counts = { 全部: bs.length };
  for (const b of bs) for (const t of b.tags) counts[t] = (counts[t] || 0) + 1;
  const tags = TAG_ORDER.filter((t) => counts[t]).concat(Object.keys(counts).filter((t) => !TAG_ORDER.includes(t)));
  app.innerHTML = `
    <section class="hero">
      <h1>Minecraft 基岩版建築作品集</h1>
      <p>用 AI 設計、可直接匯入遊戲的建築與機關。每一件都能在瀏覽器裡 3D 旋轉、剖切看室內，再下載 <b>.mcpack</b> 用 Minecraft 開啟，以結構方塊或指令放進你的世界。</p>
      <div class="hero-stats"><span><b>${bs.length}</b>件作品</span><span><b>${nVer}</b>個版本</span><span><b>${fmtNum(totalBlocks)}</b>個方塊</span></div>
    </section>
    <div class="toolbar">
      <label class="search"><span class="sr-only">搜尋建築</span>${ICONS.search}<input type="search" placeholder="搜尋名稱、類型或結構 ID…" value="${esc(homeState.q)}" autocomplete="off"></label>
      <div class="chips" role="group" aria-label="分類">${tags.map((t) => `<button type="button" class="chip" data-tag="${esc(t)}" aria-pressed="${t === homeState.tag}">${esc(t)}<span class="n">${counts[t]}</span></button>`).join('')}</div>
    </div>
    <div class="grid" id="grid"></div>`;
  const grid = app.querySelector('#grid');
  const input = app.querySelector('.search input');
  const draw = () => {
    const q = homeState.q.trim().toLowerCase();
    const list = bs.filter((b) => (homeState.tag === '全部' || b.tags.includes(homeState.tag)) && (!q || searchText(b).includes(q)));
    grid.innerHTML = list.length ? list.map(cardHtml).join('') : '';
    app.querySelector('.empty')?.remove();
    if (!list.length) grid.insertAdjacentHTML('afterend', `<p class="empty">沒有符合「${esc(homeState.q)}」的建築。</p>`);
  };
  input.addEventListener('input', () => { homeState.q = input.value; draw(); });
  app.querySelectorAll('.chip').forEach((c) => c.addEventListener('click', () => {
    homeState.tag = c.dataset.tag;
    app.querySelectorAll('.chip').forEach((x) => x.setAttribute('aria-pressed', String(x === c)));
    draw();
  }));
  draw();
  requestAnimationFrame(() => window.scrollTo(0, homeState.scroll || 0));
}
function searchText(b) {
  if (!b._s) b._s = [b.name, b.tags.join(' '), ...b.versions.flatMap((v) => [v.label, v.packName, v.description, ...v.structures.map((s) => s.id)])].join(' ').toLowerCase();
  return b._s;
}
function defaultVersion(b) { return b.versions.find((v) => v.id === b.defaultVersion) || b.versions[0]; }
function defaultModel(v) { return v.models.find((m) => m.id === v.defaultModel) || v.models[0]; }
function cardHtml(b) {
  const v = defaultVersion(b);
  const m = defaultModel(v);
  const img = b.cover ? `<img src="${esc(b.cover)}" alt="${esc(b.name)} 渲染圖" loading="lazy" decoding="async">` : '';
  return `<a class="card" href="#/b/${encodeURIComponent(b.slug)}">
    <div class="card-img">${img}${b.versions.length > 1 ? `<span class="badge">${b.versions.length} 個版本</span>` : ''}</div>
    <div class="card-body">
      <h3 class="card-title">${esc(b.name)}</h3>
      <div class="card-meta"><span>${dimText(m.size)}</span><span>${fmtNum(v.blocks)} 方塊</span>${v.models.length > 1 ? `<span>${v.structures.length} 個結構</span>` : ''}</div>
      <div class="tags">${b.tags.map((t, i) => `<span class="tag${i ? ' alt' : ''}">${esc(t)}</span>`).join('')}</div>
    </div></a>`;
}
window.addEventListener('scroll', () => { if (!page && parseRoute().name === 'home') homeState.scroll = window.scrollY; }, { passive: true });

// ---------------------------------------------------------------- 建築頁
function renderBuilding(b, verId, modelId) {
  window.scrollTo(0, 0);
  document.title = `${b.name}｜方塊建築館`;
  app.innerHTML = `
    <nav class="crumbs"><a href="#/">← 全部建築</a></nav>
    <div class="b-head"><div><h1>${esc(b.name)}</h1><div class="b-sub"></div></div></div>
    <div class="versions" role="group" aria-label="版本"></div>
    <section class="viewer" aria-label="3D 模型檢視器">
      <div class="v-top">
        <div class="v-models"><select class="select" aria-label="選擇模型"></select></div>
        <div class="v-btns">
          <button type="button" class="icon-btn" data-act="rotate" aria-pressed="false" title="自動旋轉" aria-label="自動旋轉">${ICONS.rotate}</button>
          <button type="button" class="icon-btn" data-act="reset" title="重設視角" aria-label="重設視角">${ICONS.reset}</button>
          <button type="button" class="icon-btn" data-act="fs" title="全螢幕" aria-label="全螢幕">${ICONS.fs}</button>
        </div>
      </div>
      <div class="v-progress hide"><div class="v-progress-text">準備中…</div><div class="bar"><i></i></div></div>
      <div class="v-hint hide">${isTouch ? '單指旋轉 · 雙指縮放與平移' : '拖曳旋轉 · 滾輪縮放 · 右鍵或 Shift＋拖曳平移'}</div>
      <div class="v-bottom">
        <div class="cutbar"><label for="cut-range">剖切高度</label><input id="cut-range" type="range" min="1" max="1" value="1" step="1"><output>全部顯示</output></div>
        <div class="v-stats"></div>
      </div>
    </section>
    <div class="layout">
      <div class="main-col">
        <section class="panel" id="p-images"><h2>渲染圖 <span class="sub"></span></h2><div class="gallery"></div></section>
        <section class="panel" id="p-guide"><h2>使用說明 <span class="guide-actions"></span></h2><div class="guide">載入中…</div></section>
      </div>
      <aside class="side">
        <section class="panel" id="p-info"></section>
        <section class="panel" id="p-ids"><h2>結構 ID 與載入指令</h2><div class="ids-body"></div></section>
      </aside>
    </div>`;
  if (window.matchMedia('(max-width: 979px)').matches) {
    // 手機：資訊與下載放在說明前面
    const side = app.querySelector('.side'), main = app.querySelector('.main-col');
    side.after(main);
  }
  const viewerEl = app.querySelector('.viewer');
  const sel = app.querySelector('.v-models select');
  const prog = app.querySelector('.v-progress');
  const progText = prog.querySelector('.v-progress-text');
  const progBar = prog.querySelector('.bar i');
  const cut = app.querySelector('#cut-range');
  const cutOut = app.querySelector('.cutbar output');
  const statsEl = app.querySelector('.v-stats');
  const hint = app.querySelector('.v-hint');

  const st = { b, v: null, m: null, viewer: null, disposed: false, guideFor: null };
  page = st;
  let viewerP = null;

  async function ensureViewer() {
    if (st.viewer) return st.viewer;
    if (!viewerP) {
      viewerP = import('./viewer.js?v=__BUILD__').then((mod) => {
        if (st.disposed) return null;
        if (!mod.webglSupported()) {
          viewerEl.insertAdjacentHTML('beforeend', `<div class="v-msg"><div><b>這個瀏覽器不支援 WebGL 2</b><p>無法顯示 3D 模型。請改用新版 Chrome、Edge、Firefox 或 Safari，或直接看下方的渲染圖與下載檔案。</p></div></div>`);
          app.querySelector('.v-bottom').style.display = 'none';
          return null;
        }
        try {
          st.viewer = new mod.Viewer(viewerEl, {
            onProgress: showProgress,
            onLoaded: (s) => {
              prog.classList.add('hide');
              const secs = (s.wall / 1000).toFixed(1);
              statsEl.textContent = `${fmtNum(s.vertices)} 頂點 · ${fmtNum(Math.round(s.triangles))} 三角形 · ${secs} 秒`;
              st.loadStats = s;
              window.__mcLastLoad = { model: st.m.id, ...s };
              window.__mcViewer = st.viewer; // 方便除錯／自動測試
            },
            onError: (msg) => { progText.textContent = msg; prog.classList.remove('hide', 'mini'); progBar.style.width = '0'; },
            onCut: (c) => { window.__mcLastCut = c; },
          });
        } catch (e) {
          viewerEl.insertAdjacentHTML('beforeend', `<div class="v-msg"><div><b>無法啟動 3D 檢視器</b><p>${esc(e.message)}</p></div></div>`);
          return null;
        }
        return st.viewer;
      });
    }
    return viewerP;
  }

  function showProgress(p) {
    prog.classList.remove('hide');
    if (p.stage === 'download') {
      prog.classList.remove('mini');
      progText.textContent = p.total > 1 ? `下載方塊資料 ${p.done}/${p.total}${p.bytes ? '（' + fmtBytes(p.bytes) + '）' : ''}` : '下載方塊資料…';
      progBar.style.width = `${(p.done / p.total) * 30}%`;
    } else if (p.stage === 'assemble') {
      progText.textContent = st.m.parts.length > 1 ? `組裝 ${st.m.parts.length} 個分件…` : '整理方塊…';
      progBar.style.width = '34%';
    } else if (p.stage === 'mesh') {
      prog.classList.add('mini');
      progText.textContent = `產生 3D 網格 ${Math.round((p.done / p.total) * 100)}%`;
      progBar.style.width = `${34 + (p.done / p.total) * 66}%`;
    }
  }

  // ---- 版本 chips
  const vWrap = app.querySelector('.versions');
  if (b.versions.length > 1) {
    vWrap.innerHTML = b.versions.map((v) => `<button type="button" class="chip" data-v="${esc(v.id)}"><b>${esc(v.label)}</b><small>${v.version ? 'v' + esc(v.version) + ' · ' : ''}${fmtNum(v.blocks)} 方塊</small></button>`).join('');
    vWrap.addEventListener('click', (e) => {
      const c = e.target.closest('[data-v]');
      if (c) setHash(c.dataset.v, null);
    });
  } else vWrap.remove();

  sel.addEventListener('change', () => setHash(st.v.id, sel.value));
  function setHash(vid, mid) {
    const v = b.versions.find((x) => x.id === vid) || defaultVersion(b);
    const m = v.models.find((x) => x.id === mid) || defaultModel(v);
    const hash = `#/b/${encodeURIComponent(b.slug)}/${encodeURIComponent(v.id)}/${encodeURIComponent(m.id)}`;
    if (location.hash !== hash) history.replaceState(null, '', hash);
    st.select(v.id, m.id);
  }

  // ---- 視角按鈕
  viewerEl.querySelector('.v-btns').addEventListener('click', (e) => {
    const btn = e.target.closest('[data-act]');
    if (!btn || !st.viewer) { if (btn?.dataset.act === 'fs') toggleFs(); return; }
    const act = btn.dataset.act;
    if (act === 'rotate') {
      const on = btn.getAttribute('aria-pressed') !== 'true';
      btn.setAttribute('aria-pressed', String(on));
      st.viewer.setAutoRotate(on);
    } else if (act === 'reset') st.viewer.resetView();
    else if (act === 'fs') toggleFs();
  });
  const fsBtn = viewerEl.querySelector('[data-act="fs"]');
  function inFs() { return document.fullscreenElement === viewerEl || document.webkitFullscreenElement === viewerEl || viewerEl.classList.contains('fs'); }
  function toggleFs() {
    if (inFs()) {
      if (document.fullscreenElement || document.webkitFullscreenElement) (document.exitFullscreen || document.webkitExitFullscreen).call(document);
      viewerEl.classList.remove('fs'); document.body.classList.remove('noscroll');
    } else if (viewerEl.requestFullscreen || viewerEl.webkitRequestFullscreen) {
      const p = (viewerEl.requestFullscreen || viewerEl.webkitRequestFullscreen).call(viewerEl);
      if (p && p.catch) p.catch(() => { viewerEl.classList.add('fs'); document.body.classList.add('noscroll'); updFs(); });
    } else { viewerEl.classList.add('fs'); document.body.classList.add('noscroll'); }
    updFs();
  }
  const updFs = () => { fsBtn.innerHTML = inFs() ? ICONS.fsExit : ICONS.fs; fsBtn.title = inFs() ? '離開全螢幕' : '全螢幕'; };
  const onFsChange = () => updFs();
  document.addEventListener('fullscreenchange', onFsChange);
  document.addEventListener('webkitfullscreenchange', onFsChange);
  const onKey = (e) => { if (e.key === 'Escape' && viewerEl.classList.contains('fs')) toggleFs(); };
  document.addEventListener('keydown', onKey);

  // ---- 剖切
  let cutRaf = 0;
  cut.addEventListener('input', () => {
    const Y = st.m.size[1], val = +cut.value;
    cutOut.textContent = val >= Y ? '全部顯示' : `Y ≤ ${val - 1}`;
    cancelAnimationFrame(cutRaf);
    cutRaf = requestAnimationFrame(() => st.viewer && st.viewer.setCut(val));
  });

  st.select = (vid, mid) => {
    const v = b.versions.find((x) => x.id === vid) || defaultVersion(b);
    const m = v.models.find((x) => x.id === mid) || defaultModel(v);
    const vChanged = st.v !== v;
    st.v = v;
    if (vChanged) {
      vWrap.querySelectorAll?.('[data-v]').forEach((c) => c.setAttribute('aria-pressed', String(c.dataset.v === v.id)));
      const act = vWrap.querySelector?.('[aria-pressed="true"]');
      if (act && vWrap.scrollWidth > vWrap.clientWidth) vWrap.scrollLeft = act.offsetLeft - 16;
      renderVersionInfo(st, v);
      // 模型選單
      const asm = v.models.filter((x) => x.kind === 'assembly');
      const rest = v.models.filter((x) => x.kind !== 'assembly');
      const narrow = matchMedia('(max-width: 679px)').matches;
      const opt = (x) => `<option value="${esc(x.id)}">${esc(x.kind === 'assembly' ? `${x.label}（${x.parts.length} 件）` : x.label)}${narrow ? '' : '　' + dimText(x.size)}</option>`;
      sel.innerHTML = asm.length && rest.length
        ? `<optgroup label="組裝">${asm.map(opt).join('')}</optgroup><optgroup label="${rest.some((x) => x.kind === 'module') ? '模組' : '分件'}">${rest.map(opt).join('')}</optgroup>`
        : v.models.map(opt).join('');
      sel.parentElement.style.display = v.models.length > 1 ? '' : 'none';
    }
    if (st.m === m && !vChanged) return;
    st.m = m;
    sel.value = m.id;
    app.querySelector('.b-sub').innerHTML = [
      ...b.tags.map((t, i) => `<span class="tag${i ? ' alt' : ''}">${esc(t)}</span>`),
      `<span>${dimLong(m.size)}</span>`,
      `<span>${fmtInt(m.blocks)} 方塊</span>`,
      b.versions.length > 1 ? `<span>目前：${esc(v.label)}</span>` : '',
    ].join('');
    const factSize = app.querySelector('#fact-size');
    if (factSize) factSize.textContent = dimLong(m.size);
    renderIds(st, v, m);
    cut.max = String(m.size[1]); cut.value = String(m.size[1]); cutOut.textContent = '全部顯示';
    statsEl.textContent = '';
    ensureViewer().then((viewer) => {
      if (!viewer || st.disposed || st.m !== m) return;
      progText.textContent = '準備中…'; progBar.style.width = '0'; prog.classList.remove('hide', 'mini');
      if (isTouch && m.blocks > 1500000) progText.textContent = '大型模型，手機載入需要幾秒…';
      viewer.load(m);
      if (!st.hinted) {
        st.hinted = true;
        hint.classList.remove('hide');
        setTimeout(() => hint.classList.add('hide'), 4500);
      }
    });
  };

  st.dispose = () => {
    st.disposed = true;
    document.removeEventListener('fullscreenchange', onFsChange);
    document.removeEventListener('webkitfullscreenchange', onFsChange);
    document.removeEventListener('keydown', onKey);
    document.body.classList.remove('noscroll');
    if (st.viewer) st.viewer.dispose();
    st.viewer = null;
  };
  st.select(verId, modelId);
}

function renderVersionInfo(st, v) {
  const b = st.b;
  const info = app.querySelector('#p-info');
  const f = v.files;
  const imgs = v.images;
  const render = imgs.find((i) => i.kind === 'render'), cutaway = imgs.find((i) => i.kind === 'cutaway');
  const gallery = imgs.filter((i) => i.kind === 'gallery');
  const dl = (file, label, icon) => file ? `<a class="btn" href="${esc(file.url || file.full)}" download="${esc(file.name)}">${icon}<span>${label}</span></a>` : '';
  info.innerHTML = `
    <h2>${esc(v.packName || b.name)} <span class="sub">${v.version ? 'v' + esc(v.version) : ''}</span></h2>
    ${v.description ? `<p class="desc clamp">${esc(v.description)}</p>${v.description.length > 90 ? '<button type="button" class="more">展開全文</button>' : ''}` : ''}
    <dl class="facts">
      <div><dt>尺寸（寬×深×高）</dt><dd id="fact-size">${dimLong(defaultModel(v).size)}</dd></div>
      <div><dt>方塊數</dt><dd>${fmtInt(v.blocks)}</dd></div>
      <div><dt>結構數</dt><dd>${v.structures.length} 個</dd></div>
      <div><dt>行為包大小</dt><dd>${fmtBytes(f.mcpack.bytes)}</dd></div>
    </dl>
    <div style="margin-top:14px">
      <a class="btn primary" href="${esc(f.mcpack.url)}" download="${esc(f.mcpack.name)}">${ICONS.download}<span>下載 .mcpack</span><small>${fmtBytes(f.mcpack.bytes)}</small></a>
      <div class="dl-list">
        ${dl(f.txt, '使用說明 .txt', ICONS.doc)}
        ${render ? `<a class="btn" href="${esc(render.full)}" download="${esc(render.name)}">${ICONS.img}<span>整體渲染圖</span></a>` : ''}
        ${cutaway ? `<a class="btn" href="${esc(cutaway.full)}" download="${esc(cutaway.name)}">${ICONS.img}<span>內部剖視圖</span></a>` : ''}
        ${gallery.length ? `<a class="btn" href="#p-images" data-scroll="p-images">${ICONS.img}<span>預覽圖 ${gallery.length} 張</span></a>` : ''}
      </div>
      <p class="hint">${isTouch
        ? '<b>手機安裝：</b>下載完成後點開 .mcpack 檔，選擇用 <b>Minecraft</b> 開啟即會自動匯入（iPhone 請在「檔案」App 點檔案 → 分享 → Minecraft）。'
        : '<b>安裝：</b>下載後雙擊 .mcpack 匯入 Minecraft，在世界設定的「行為包」啟用，開啟作弊後用結構方塊或下方指令放置。'}</p>
    </div>`;
  info.querySelector('.more')?.addEventListener('click', (e) => {
    const d = info.querySelector('.desc'); const open = d.classList.toggle('clamp');
    e.target.textContent = open ? '展開全文' : '收合';
  });
  info.querySelector('[data-scroll]')?.addEventListener('click', (e) => { e.preventDefault(); document.getElementById('p-images').scrollIntoView({ behavior: 'smooth' }); });

  // 圖片
  const pImg = app.querySelector('#p-images');
  if (!imgs.length) pImg.style.display = 'none';
  else {
    pImg.style.display = '';
    pImg.querySelector('.sub').textContent = `${imgs.length} 張 · 點圖放大`;
    pImg.querySelector('.gallery').innerHTML = imgs.map((im, i) => `<button type="button" data-i="${i}"><img src="${esc(im.thumb)}" alt="${esc(im.title)}" loading="lazy" decoding="async"><span>${esc(im.kind === 'render' ? '整體渲染' : im.kind === 'cutaway' ? '內部剖視' : im.title)}</span></button>`).join('');
    pImg.querySelector('.gallery').onclick = (e) => { const t = e.target.closest('[data-i]'); if (t) openLightbox(imgs, +t.dataset.i); };
  }

  // 使用說明
  const guide = app.querySelector('#p-guide .guide');
  const actions = app.querySelector('#p-guide .guide-actions');
  actions.innerHTML = '';
  if (!f.txt) { guide.textContent = '這個版本沒有附使用說明。'; return; }
  guide.textContent = '載入中…';
  const want = v;
  fetch(f.txt.url).then((r) => r.arrayBuffer()).then((ab) => {
    if (st.v !== want || st.disposed) return;
    const text = new TextDecoder('utf-8').decode(ab).replace(/^﻿/, '').replace(/\r\n?/g, '\n');
    guide.innerHTML = guideHtml(text);
    actions.innerHTML = `<button type="button" class="copy" data-copy="${esc(text)}">複製全文</button><a class="copy" style="display:inline-flex;align-items:center" href="${esc(f.txt.url)}" download="${esc(f.txt.name)}">下載 .txt</a>`;
  }).catch(() => { guide.textContent = '無法載入使用說明。'; });
}

// 行內指令：遇到中文字或全形標點就結束
const CMD_RE = /\/(?:function|structure|execute|give|tp|teleport|tickingarea|gamerule|fill|clone|setblock|scoreboard|kill|summon|time|weather|gamemode|effect|setworldspawn|spawnpoint|difficulty|tellraw|title|clear|playsound|particle)\b[^\u3000-\u303f\uff00-\uffef\u4e00-\u9fff\n]*/g;
function guideHtml(text) {
  return text.split('\n').map((line) => {
    const t = line.trim();
    if (t.startsWith('/') && /^\/[a-z]/.test(t)) {
      return `<div class="gl-cmd"><code>${esc(t)}</code><button type="button" class="copy" data-copy="${esc(t)}">複製</button></div>`;
    }
    const isH = /^([一二三四五六七八九十]+、|【.+】|#{1,4}\s|\d+[.)、]\s*\S.{0,24}$|[■◆●▍].+)/.test(t) && t.length < 60 && !/[。]$/.test(t) && /^([一二三四五六七八九十]+、|【|#|[■◆●▍])/.test(t);
    let html = '';
    let last = 0;
    line.replace(CMD_RE, (m, off) => {
      const cmd = m.replace(/\s+$/, '');
      html += esc(line.slice(last, off)) + `<code class="inline" data-copy="${esc(cmd)}" title="點一下複製">${esc(cmd)}</code>`;
      last = off + cmd.length;
      return m;
    });
    html += esc(line.slice(last));
    return `<p${isH ? ' class="h"' : ''}>${html || ''}</p>`;
  }).join('');
}

function renderIds(st, v, m) {
  const body = app.querySelector('#p-ids .ids-body');
  const asm = m.kind === 'assembly' ? m : v.models.find((x) => x.kind === 'assembly');
  const offsets = new Map((asm ? asm.parts : []).map((p) => [p.id, p.offset]));
  const ids = m.kind === 'assembly' ? m.parts.map((p) => p.id) : v.structures.map((s) => s.id);
  const sById = new Map(v.structures.map((s) => [s.id, s]));
  const cmdFor = (id) => {
    const o = m.kind === 'assembly' ? offsets.get(id) : (m.parts[0].id === id ? [0, 0, 0] : offsets.get(id) || [0, 0, 0]);
    return `/structure load ${id} ~${o[0] || ''} ~${o[1] || ''} ~${o[2] || ''}`;
  };
  const all = ids.map(cmdFor).join('\n');
  body.innerHTML = `
    <p class="hint" style="margin:0 0 10px">拿結構方塊：<code class="inline" data-copy="/give @s structure_block">/give @s structure_block</code>，切到「載入」輸入 ID（旋轉 0°、不鏡像）。或直接在原點執行指令，<b>~</b> 表示相對於你目前的位置${m.kind === 'assembly' ? '，分件依偏移拼成整體' : ''}。</p>
    ${ids.length > 1 ? `<div style="display:flex;justify-content:flex-end;margin-bottom:8px"><button type="button" class="copy" data-copy="${esc(all)}">複製全部 ${ids.length} 行指令</button></div>` : ''}
    <ul class="ids">${ids.map((id) => {
      const s = sById.get(id);
      const o = offsets.get(id);
      const cmd = cmdFor(id);
      return `<li${(m.kind !== 'assembly' && m.parts[0].id === id) ? ' style="border-color:var(--accent)"' : ''}>
        <div class="id-row"><code>${esc(id)}</code><button type="button" class="copy" data-copy="${esc(id)}">複製 ID</button></div>
        <div class="meta">${s ? dimText(s.size) + ' · ' + fmtNum(s.blocks) + ' 方塊' : ''}${o && (m.kind === 'assembly') ? ` · 偏移 (${o.join(', ')})` : ''}</div>
        <div class="cmd"><code>${esc(cmd)}</code><button type="button" class="copy" data-copy="${esc(cmd)}">複製</button></div>
      </li>`;
    }).join('')}</ul>`;
}

// ---------------------------------------------------------------- 大圖
function openLightbox(list, index) {
  let i = index;
  const lb = h(`<div class="lightbox" role="dialog" aria-modal="true" aria-label="圖片檢視">
    <button type="button" class="lb-close" aria-label="關閉">×</button>
    ${list.length > 1 ? '<button type="button" class="lb-nav lb-prev" aria-label="上一張">‹</button><button type="button" class="lb-nav lb-next" aria-label="下一張">›</button>' : ''}
    <img alt="">
    <div class="lb-bar"><span class="lb-title"></span><a class="lb-dl" download>下載原圖</a></div>
  </div>`);
  const img = lb.querySelector('img');
  const show = () => {
    const im = list[i];
    img.src = im.large; img.alt = im.title;
    lb.querySelector('.lb-title').textContent = `${im.kind === 'render' ? '整體渲染' : im.kind === 'cutaway' ? '內部剖視' : im.title}${list.length > 1 ? `（${i + 1}/${list.length}）` : ''}`;
    const a = lb.querySelector('.lb-dl'); a.href = im.full; a.setAttribute('download', im.name);
    a.textContent = `下載原圖${im.bytes ? '（' + fmtBytes(im.bytes) + '）' : ''}`;
  };
  const close = () => { lb.remove(); document.body.classList.remove('noscroll'); document.removeEventListener('keydown', key); };
  const go = (d) => { i = (i + d + list.length) % list.length; show(); };
  const key = (e) => { if (e.key === 'Escape') close(); else if (e.key === 'ArrowLeft') go(-1); else if (e.key === 'ArrowRight') go(1); };
  lb.addEventListener('click', (e) => {
    if (e.target === lb || e.target.classList.contains('lb-close')) close();
    else if (e.target.classList.contains('lb-prev')) go(-1);
    else if (e.target.classList.contains('lb-next')) go(1);
  });
  let sx = null;
  lb.addEventListener('touchstart', (e) => { sx = e.touches[0].clientX; }, { passive: true });
  lb.addEventListener('touchend', (e) => { if (sx == null) return; const dx = e.changedTouches[0].clientX - sx; if (Math.abs(dx) > 50) go(dx < 0 ? 1 : -1); sx = null; });
  document.addEventListener('keydown', key);
  document.body.appendChild(lb);
  document.body.classList.add('noscroll');
  show();
  lb.querySelector('.lb-close').focus();
}

route();
