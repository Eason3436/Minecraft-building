// three.js 3D 檢視器：載入（worker 網格化）、OrbitControls、剖切、陰影、全螢幕。
import * as THREE from './vendor/three.module.js';
import { OrbitControls } from './vendor/OrbitControls.js';

THREE.ColorManagement.enabled = false; // 方塊顏色直接用 sRGB 數值，不做色彩空間轉換

export function webglSupported() {
  try {
    const c = document.createElement('canvas');
    return !!(window.WebGL2RenderingContext && c.getContext('webgl2'));
  } catch { return false; }
}

const isTouch = matchMedia('(pointer: coarse)').matches;

function freeArray() { this.array = null; }

// 在 Lambert 材質加上「每格微小明暗差」與「方塊格線」，讓大面積合併面仍看得出方塊感
function patchMaterial(mat, { grid = true } = {}) {
  mat.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vBlockPos;\nvarying vec3 vObjNormal;')
      .replace('#include <begin_vertex>', '#include <begin_vertex>\nvBlockPos = position / 16.0;\nvObjNormal = normal;');
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vBlockPos;\nvarying vec3 vObjNormal;')
      .replace('#include <color_fragment>', `#include <color_fragment>
      {
        vec3 an = abs(vObjNormal);
        vec3 cellP = floor(vBlockPos - vObjNormal * 0.02);
        float h = fract(sin(dot(cellP, vec3(12.9898, 78.233, 37.719))) * 43758.5453);
        diffuseColor.rgb *= 0.955 + 0.075 * h;
        #ifdef OPAQUE
        if (vColor.a < 0.995) {
          // 樹葉：每格切成 8×8 小格，隨機加深（模擬葉隙）
          vec3 q = floor(vBlockPos * 8.0 - vObjNormal * 0.01);
          float r = fract(sin(dot(q, vec3(27.17, 91.31, 53.77))) * 24634.6345);
          diffuseColor.rgb *= r < 0.16 ? 0.58 : 0.8 + 0.28 * r;
        }
        #endif
        ${grid ? `vec3 f = abs(fract(vBlockPos) - 0.5);
        float e = an.x > 0.5 ? max(f.y, f.z) : (an.y > 0.5 ? max(f.x, f.z) : max(f.x, f.y));
        float fw = fwidth(e);
        float line = smoothstep(0.5 - fw * 1.5, 0.5, e) * clamp(1.0 - fw * 6.0, 0.0, 1.0);
        diffuseColor.rgb *= 1.0 - 0.13 * line;` : ''}
      }`);
  };
  mat.customProgramCacheKey = () => 'mcblock' + (grid ? 1 : 0);
  return mat;
}

export class Viewer {
  constructor(host, { onProgress = () => {}, onLoaded = () => {}, onError = () => {}, onCut = () => {} } = {}) {
    this.host = host;
    this.cb = { onProgress, onLoaded, onError, onCut };
    const big = !isTouch;
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance', preserveDrawingBuffer: false });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, isTouch ? 2 : 2));
    renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
    renderer.setClearColor(0x000000, 0);
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFShadowMap;
    renderer.shadowMap.autoUpdate = false;
    renderer.shadowMap.needsUpdate = true; // 第一張畫面先產生陰影貼圖，避免取樣到空貼圖
    renderer.domElement.className = 'viewer-canvas';
    host.prepend(renderer.domElement);
    this.renderer = renderer;
    this.maxShadow = Math.min(renderer.capabilities.maxTextureSize, big ? 4096 : 2048);

    const scene = new THREE.Scene();
    this.scene = scene;
    this.camera = new THREE.PerspectiveCamera(38, 1, 0.1, 5000);
    const controls = new OrbitControls(this.camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.09;
    controls.screenSpacePanning = true;
    controls.zoomToCursor = true;
    controls.autoRotateSpeed = 0.9;
    controls.maxPolarAngle = Math.PI * 0.94;
    this.controls = controls;
    controls.addEventListener('start', () => { this.userActive = true; });

    this.hemi = new THREE.HemisphereLight(0xffffff, 0x8d939c, 1.95);
    scene.add(this.hemi);
    this.sun = new THREE.DirectionalLight(0xfff6e8, 1.75);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(this.maxShadow, this.maxShadow);
    this.sun.shadow.bias = -0.0004;
    scene.add(this.sun, this.sun.target);

    this.materials = [
      patchMaterial(new THREE.MeshLambertMaterial({ vertexColors: true })),
      patchMaterial(new THREE.MeshLambertMaterial({ vertexColors: true, transparent: true, depthWrite: false }), { grid: false }),
      new THREE.MeshBasicMaterial({ vertexColors: true }),
    ];

    // 地面：淡色圓盤（邊緣漸隱）＋陰影
    const g = document.createElement('canvas'); g.width = g.height = 256;
    const cx = g.getContext('2d');
    const grad = cx.createRadialGradient(128, 128, 0, 128, 128, 128);
    // alphaMap 讀的是綠色通道，所以用灰階漸層
    grad.addColorStop(0, 'rgb(255,255,255)'); grad.addColorStop(0.35, 'rgb(220,220,220)'); grad.addColorStop(0.7, 'rgb(80,80,80)'); grad.addColorStop(1, 'rgb(0,0,0)');
    cx.fillStyle = grad; cx.fillRect(0, 0, 256, 256);
    const tex = new THREE.CanvasTexture(g);
    // 模型下方的淡色光暈（不打光、邊緣漸隱，看不到地平線）＋只顯示陰影的透明地面
    this.groundMat = new THREE.MeshBasicMaterial({ color: 0xc6cdd0, alphaMap: tex, transparent: true, opacity: 0.55, depthWrite: false });
    this.ground = new THREE.Mesh(new THREE.CircleGeometry(1, 72), this.groundMat);
    this.ground.rotation.x = -Math.PI / 2;
    this.ground.renderOrder = -2;
    scene.add(this.ground);
    this.shadowMat = new THREE.ShadowMaterial({ color: 0x14202a, opacity: 0.24, depthWrite: false });
    this.shadowPlane = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), this.shadowMat);
    this.shadowPlane.rotation.x = -Math.PI / 2;
    this.shadowPlane.receiveShadow = true;
    this.shadowPlane.renderOrder = -1;
    scene.add(this.shadowPlane);

    this.root = new THREE.Group();
    this.root.scale.setScalar(1 / 16);
    scene.add(this.root);
    this.chunks = new Map();
    this.cutState = { busy: false, pending: null, gen: 0, current: null, incoming: [] };
    this.dirty = true;

    this.applyTheme();
    this.mq = matchMedia('(prefers-color-scheme: dark)');
    this.mqHandler = () => { this.applyTheme(); this.dirty = true; };
    this.mq.addEventListener?.('change', this.mqHandler);

    this.ro = new ResizeObserver(() => this.resize());
    this.ro.observe(host);
    this.resize();
    this.running = true;
    const loop = () => {
      if (!this.running) return;
      requestAnimationFrame(loop);
      const moved = this.controls.update();
      if (moved || this.dirty) {
        this.dirty = false;
        this.renderer.render(this.scene, this.camera);
      }
    };
    requestAnimationFrame(loop);
    renderer.domElement.addEventListener('webglcontextlost', (e) => { e.preventDefault(); this.cb.onError('WebGL 內容遺失（顯示卡記憶體不足？），請重新整理頁面。'); });
  }

  applyTheme() {
    const dark = document.documentElement.dataset.theme === 'dark' || (document.documentElement.dataset.theme !== 'light' && matchMedia('(prefers-color-scheme: dark)').matches);
    this.groundMat.color.set(dark ? 0x0b0d10 : 0xc6cdd0);
    this.groundMat.opacity = dark ? 0.45 : 0.55;
    if (this.shadowMat) this.shadowMat.opacity = dark ? 0.4 : 0.24;
    this.hemi.groundColor.set(dark ? 0x6f7680 : 0x8d939c);
  }

  resize() {
    const w = this.host.clientWidth, h = this.host.clientHeight;
    if (!w || !h) return;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.dirty = true;
  }

  clearModel() {
    if (this.worker) { this.worker.terminate(); this.worker = null; }
    for (const c of this.chunks.values()) {
      for (const m of [...c.base, ...c.cut]) { this.root.remove(m); m.geometry.dispose(); }
    }
    this.chunks.clear();
    this.cutState = { busy: false, pending: null, gen: this.cutState.gen + 1, current: null, incoming: [] };
    this.stats = null;
    this.dirty = true;
  }

  /** model: catalog 的模型物件 */
  load(model, base = '') {
    this.clearModel();
    this.model = model;
    const [X, Y, Z] = model.size;
    this.root.position.set(-X / 2, 0, -Z / 2);
    this.root.updateMatrixWorld(true);
    this.fitCamera(true);
    // 手機上的大模型降低解析度，保持流暢
    const dpr = window.devicePixelRatio || 1;
    this.renderer.setPixelRatio(Math.min(dpr, isTouch && model.blocks > 800000 ? 1.5 : 2));
    this.resize();
    this.loadStart = performance.now();
    this.firstChunkAt = null;
    const w = new Worker(new URL('./worker.js?v=__BUILD__', import.meta.url), { type: 'module' });
    this.worker = w;
    w.onmessage = (e) => this.onWorker(e.data, w);
    w.onerror = (e) => { this.cb.onError('網格化程式發生錯誤：' + (e.message || '未知錯誤')); };
    const parts = model.parts.map((p) => ({ url: p.url, offset: p.offset, size: p.size }));
    w.postMessage({ type: 'load', parts, size: model.size, colorsUrl: 'data/colors.json', base: new URL(base || '.', location.href).href });
  }

  onWorker(m, w) {
    if (w !== this.worker) return;
    if (m.type === 'progress') this.cb.onProgress(m);
    else if (m.type === 'chunk') {
      if (!this.firstChunkAt) this.firstChunkAt = performance.now();
      const c = { cy: m.cy, base: this.makeMeshes(m.layers), cut: [] };
      this.chunks.set(m.key, c);
      // 剖切中載入的分塊：先依目前剖切狀態決定顯示
      this.applyCutTo(c, m.key);
      this.shadowDirty();
      this.dirty = true;
    } else if (m.type === 'done') {
      this.stats = { ...m, wall: performance.now() - this.loadStart, firstPaint: (this.firstChunkAt || performance.now()) - this.loadStart };
      this.chunkH = m.chunkH;
      this.shadowDirty(true);
      this.cb.onLoaded(this.stats);
    } else if (m.type === 'cutChunk') {
      if (m.gen === this.cutState.gen) this.cutState.incoming.push([m.key, this.makeMeshes(m.layers)]);
      else for (const mesh of this.makeMeshes(m.layers)) mesh.geometry.dispose();
    } else if (m.type === 'cutDone') this.finishCut(m);
    else if (m.type === 'error') this.cb.onError(m.message);
  }

  makeMeshes(layers) {
    const out = [];
    layers.forEach((L, i) => {
      if (!L) return;
      const g = new THREE.BufferGeometry();
      const pos = new THREE.BufferAttribute(L.pos, 3);
      const nor = new THREE.BufferAttribute(L.nor, 3, true);
      const col = new THREE.BufferAttribute(L.col, 4, true);
      const idx = new THREE.BufferAttribute(L.idx, 1);
      g.setAttribute('position', pos); g.setAttribute('normal', nor); g.setAttribute('color', col); g.setIndex(idx);
      g.computeBoundingSphere();
      for (const a of [pos, nor, col, idx]) a.onUpload(freeArray);
      const mesh = new THREE.Mesh(g, this.materials[i]);
      mesh.castShadow = i !== 1;
      mesh.receiveShadow = i !== 2;
      mesh.matrixAutoUpdate = false;
      mesh.renderOrder = i === 1 ? 2 : 0;
      this.root.add(mesh);
      mesh.updateMatrixWorld(true);
      out.push(mesh);
    });
    return out;
  }

  shadowDirty(now = false) {
    // 陰影貼圖只在幾何改變時重算（光源相對模型固定）
    clearTimeout(this._shT);
    const go = () => { this.renderer.shadowMap.needsUpdate = true; this.dirty = true; };
    if (now) go(); else this._shT = setTimeout(go, 250);
  }

  fitCamera(reset = false) {
    if (!this.model) return;
    const [X, Y, Z] = this.model.size;
    const R = 0.5 * Math.hypot(X, Y, Z);
    this.R = R;
    const target = new THREE.Vector3(0, Y * 0.46, 0);
    const vfov = THREE.MathUtils.degToRad(this.camera.fov);
    const aspect = this.camera.aspect || 1;
    const tanV = Math.tan(vfov / 2), tanH = tanV * aspect;
    // 細長的模型（例如鐵道、戰艦）把長軸轉到畫面橫向
    const az = THREE.MathUtils.degToRad(X >= Z ? 32 : 58), el = THREE.MathUtils.degToRad(27);
    const dir = new THREE.Vector3(Math.sin(az) * Math.cos(el), Math.sin(el), Math.cos(az) * Math.cos(el));
    const up = new THREE.Vector3(0, 1, 0);
    const right = new THREE.Vector3().crossVectors(up, dir).normalize();
    const camUp = new THREE.Vector3().crossVectors(dir, right).normalize();
    // 讓包圍盒 8 個角都落在視野內（留 8% 邊界）
    let dist = 0;
    const c = new THREE.Vector3();
    for (const sx of [-X / 2, X / 2]) for (const sy of [0, Y]) for (const sz of [-Z / 2, Z / 2]) {
      c.set(sx, sy, sz).sub(target);
      const zc = c.dot(dir), xc = Math.abs(c.dot(right)), yc = Math.abs(c.dot(camUp));
      dist = Math.max(dist, zc + xc / (tanH * 0.92), zc + yc / (tanV * 0.9));
    }
    this.camera.near = Math.max(0.05, R / 400);
    this.camera.far = R * 30 + dist;
    this.camera.position.copy(target).addScaledVector(dir, dist);
    this.camera.updateProjectionMatrix();
    this.controls.target.copy(target);
    this.controls.minDistance = Math.max(1.5, R * 0.02);
    this.controls.maxDistance = R * 8;
    this.controls.update();
    if (reset) {
      // 地面與陰影範圍
      const gr = Math.max(X, Z) * 0.85 + 12;
      this.ground.scale.setScalar(gr);
      this.ground.position.y = -0.04;
      this.shadowPlane.scale.setScalar(Math.max(X, Z) * 6 + 80);
      this.shadowPlane.position.y = -0.02;
      const s = this.sun;
      const sd = new THREE.Vector3(-0.55, 1.0, 0.42).normalize();
      s.position.copy(sd.multiplyScalar(R * 2.2)).add(new THREE.Vector3(0, Y * 0.3, 0));
      s.target.position.set(0, Y * 0.3, 0);
      s.target.updateMatrixWorld();
      const sc = s.shadow.camera;
      sc.left = -R * 1.05; sc.right = R * 1.05; sc.top = R * 1.05; sc.bottom = -R * 1.05;
      sc.near = R * 0.2; sc.far = R * 4.4;
      sc.updateProjectionMatrix();
      s.shadow.normalBias = Math.max(0.02, (2 * R / this.maxShadow) * 1.2);
    }
    this.dirty = true;
  }

  resetView() { this.fitCamera(false); }
  setAutoRotate(on) { this.controls.autoRotate = on; this.dirty = true; }

  // ---------------------------------------------------------------- 剖切
  /** 只顯示 y < layers 的方塊（layers = 顯示層數；>= 高度表示不剖切） */
  setCut(layers) {
    const cs = this.cutState;
    cs.pending = layers;
    if (!cs.busy) this.sendCut();
  }

  sendCut() {
    const cs = this.cutState;
    if (cs.pending == null || !this.worker) return;
    const layers = cs.pending; cs.pending = null;
    const Y = this.model.size[1];
    if (layers >= Y) {
      cs.gen++;
      this.removeCutMeshes();
      cs.current = null;
      for (const [k, c] of this.chunks) this.applyCutTo(c, k);
      this.shadowDirty(true);
      this.cb.onCut(null);
      return;
    }
    cs.busy = true;
    cs.gen++;
    cs.incoming = [];
    this.worker.postMessage({ type: 'cut', yMax: layers - 1, gen: cs.gen });
  }

  removeCutMeshes() {
    for (const c of this.chunks.values()) {
      for (const m of c.cut) { this.root.remove(m); m.geometry.dispose(); }
      c.cut = [];
    }
  }

  finishCut(m) {
    const cs = this.cutState;
    cs.busy = false;
    if (m.gen === cs.gen) {
      this.removeCutMeshes();
      cs.current = { yMax: m.yMax, cy: m.cy };
      for (const [key, meshes] of cs.incoming) {
        const c = this.chunks.get(key);
        if (c) c.cut = meshes; else for (const x of meshes) { this.root.remove(x); x.geometry.dispose(); }
      }
      cs.incoming = [];
      for (const [k, c] of this.chunks) this.applyCutTo(c, k);
      this.shadowDirty(true);
      this.cb.onCut({ yMax: m.yMax, ms: m.ms });
    }
    if (cs.pending != null) this.sendCut();
  }

  applyCutTo(c) {
    const cur = this.cutState.current;
    let showBase = true, showCut = false;
    if (cur) {
      if (cur.yMax < 0 || c.cy > cur.cy) showBase = false;
      else if (c.cy === cur.cy) { showBase = false; showCut = true; }
    }
    for (const m of c.base) m.visible = showBase;
    for (const m of c.cut) m.visible = showCut;
    this.dirty = true;
  }

  // ---------------------------------------------------------------- 其他
  vertexCount() { return this.stats ? this.stats.vertices : 0; }

  dispose() {
    this.running = false;
    this.clearModel();
    this.ro.disconnect();
    this.mq.removeEventListener?.('change', this.mqHandler);
    this.controls.dispose();
    for (const m of this.materials) m.dispose();
    this.groundMat.dispose();
    this.shadowMat.dispose();
    this.renderer.dispose();
    this.renderer.forceContextLoss?.();
    this.renderer.domElement.remove();
  }
}
