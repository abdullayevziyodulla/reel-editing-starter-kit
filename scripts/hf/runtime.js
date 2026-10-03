// HyperFrames seeks the registered GSAP timeline. No custom browser capture loop.
// Persistent media clips are managed by HyperFrames; holes only describe their animated geometry.
const DARK = PLAN.theme === "dark";
document.documentElement.dataset.theme = DARK ? "dark" : "light";
const W = 1080, H = 1920, TOP_CY = 465;
const clamp = (x, a = 0, b = 1) => Math.max(a, Math.min(b, x));
const lerp = (a, b, p) => a + (b - a) * p;
const easeOut = p => 1 - Math.pow(1 - clamp(p), 3);
function spring(p) { p = clamp(p); return 1 - Math.exp(-6 * p) * Math.cos(9 * p); }  // overshoot ~5%, settles
function pop(t, t0, from = 0.85) {
  if (t < t0) return { s: from, o: 0, on: false };
  const p = (t - t0) / 0.38;
  return { s: from + (1 - from) * spring(p), o: clamp((t - t0) / 0.07), on: true };
}
function outFade(t, end) { return clamp((end - t) / 0.12); }
const esc = s => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;");
const tf = (p, extra = "") => `opacity:${p.o};transform:${extra} scale(${p.s});`;

// ---------- scenes ----------
const SCENES = {
  counter(sc, t) {
    const p = pop(t, sc.start + 0.03), o = outFade(t, sc.end);
    const k = clamp((t - sc.count_at) / 0.35);
    const n = Math.round(lerp(0, sc.number, easeOut(k)));
    return `<div class="card" style="left:${W / 2 - 400}px;top:${TOP_CY - 190}px;width:800px;height:380px;${tf(p)}opacity:${p.o * o}">
      <img src="${sc.logo}" style="position:absolute;left:70px;top:90px;height:200px">
      <div style="position:absolute;left:300px;top:40px;font:italic 700 230px/1 'Playfair Display';color:#111">${n}</div>
      <div style="position:absolute;left:470px;top:150px;font:italic 500 110px/1 'Playfair Display';color:#777">${esc(sc.unit)}</div>
      <div style="position:absolute;left:300px;top:285px;font:800 44px/1 Inter;color:#111">${esc(sc.title)}</div></div>`;
  },

  window(sc, t) {
    const p = pop(t, sc.start + 0.02), o = outFade(t, sc.end);
    const w = sc.w || 960, mh = Math.round(w / (sc.aspect || 16 / 9)), bar = 58;
    const x = W / 2 - w / 2, y = (sc.cy || TOP_CY) - (mh + bar) / 2;
    let cursor = "";
    for (const c of sc.cursor || []) {
      if (t < c.t - 0.6 || t > sc.end) continue;
      const m = easeOut((t - (c.t - 0.6)) / 0.5);
      const cx = lerp(c.from[0], c.x, m), cy = lerp(c.from[1], c.y, m);
      const ring = t > c.t ? clamp((t - c.t) / 0.35) : 0;
      cursor = `${ring > 0 && ring < 1 ? `<div style="position:absolute;left:${x + cx - 40 * ring}px;top:${y + bar + cy - 40 * ring}px;width:${80 * ring}px;height:${80 * ring}px;border-radius:50%;border:5px solid rgba(255,255,255,${1 - ring})"></div>` : ""}
        <svg style="position:absolute;left:${x + cx}px;top:${y + bar + cy}px;transform:scale(${t > c.t && t < c.t + 0.12 ? 0.85 : 1})" width="54" height="64" viewBox="0 0 18 22"><path d="M1 1 L1 17 L5.5 13 L8.5 20 L11 19 L8 12 L14 12 Z" fill="#111" stroke="#fff" stroke-width="1.6"/></svg>`;
    }
    return `<div class="win" style="left:${x}px;top:${y}px;width:${w}px;${tf(p)}opacity:${p.o * o}">
        <div class="bar"><i style="background:#ff5f57"></i><i style="background:#febc2e"></i><i style="background:#28c840"></i><span>${esc(sc.title || "")}</span></div>
        <div data-hole="${sc.media}" data-media-id="${sc.media_id}" data-r="22" data-from="${sc.from || 0}" data-start="${sc.start}" data-op="${p.o * o}" style="height:${mh}px"></div>
      </div>${cursor}`;
  },

  tiles(sc, t) {
    const o = outFade(t, sc.end), cols = 4, tw = 236, ih = 178, gap = 18, th = ih + 56;
    const rows = Math.ceil(sc.items.length / cols), gh = rows * th + (rows - 1) * gap;
    let html = "";
    sc.items.forEach((it, i) => {
      const r = Math.floor(i / cols), inRow = Math.min(cols, sc.items.length - r * cols), c = i % cols;
      const x = W / 2 - (inRow * tw + (inRow - 1) * gap) / 2 + c * (tw + gap), y = TOP_CY - gh / 2 + r * (th + gap) + 20;
      const p = pop(t, it.t, 0.6);
      if (!p.on) return;
      const hot = t - it.t < 0.6 && (i === sc.items.length - 1 || t < sc.items[i + 1].t);
      html += `<div class="card" style="left:${x}px;top:${y}px;width:${tw}px;height:${th}px;padding:12px;box-sizing:border-box;${tf(p)}opacity:${p.o * o};${hot ? "box-shadow:0 0 0 6px #ff6a3d,0 16px 34px rgba(0,0,0,.14);" : ""}">
        <img src="${it.img}" style="width:100%;height:${ih - 24}px;object-fit:cover;border-radius:14px;object-position:${it.pos || "50% 50%"}">
        <div style="font:800 25px/1 Inter;color:#111;text-align:center;margin-top:14px;white-space:nowrap">${it.icon || ""} ${esc(it.label)}</div></div>`;
    });
    return html;
  },

  chat(sc, t) {
    const p = pop(t, sc.start + 0.02), o = outFade(t, sc.end);
    const qn = Math.floor(sc.q.length * clamp((t - sc.q_t0) / (sc.q_t1 - sc.q_t0)));
    const words = sc.a.split(" "), an = Math.floor(words.length * clamp((t - sc.a_t0) / (sc.a_t1 - sc.a_t0)));
    const dots = t > sc.q_t1 + 0.1 && an === 0;
    const dot = i => `<b style="opacity:${0.3 + 0.7 * Math.abs(Math.sin(t * 6 + i))}">•</b>`;
    return `<div class="card" style="left:${W / 2 - 450}px;top:${TOP_CY - 300}px;width:900px;height:600px;${tf(p)}opacity:${p.o * o}">
      <div style="position:absolute;left:40px;top:34px;font:800 36px Inter;color:#111"><span style="display:inline-block;width:18px;height:18px;border-radius:50%;background:#28c840;margin-right:14px"></span>${esc(sc.title)}</div>
      <div style="position:absolute;left:0;right:0;top:100px;height:2px;background:#eee"></div>
      ${qn > 0 ? `<div class="bubble me" style="top:140px">${esc(sc.q.slice(0, qn))}</div>` : ""}
      ${dots ? `<div class="bubble ai" style="top:300px;font-size:60px;line-height:30px;padding:22px 30px">${dot(0)}${dot(1)}${dot(2)}</div>` : ""}
      ${an > 0 ? `<div class="bubble ai" style="top:300px">${esc(words.slice(0, an).join(" "))}</div>` : ""}</div>`;
  },

  stack(sc, t) {
    const o = outFade(t, sc.end);
    let y = TOP_CY - (sc.cards.length * 230 + (sc.cards.length - 1) * 40) / 2, html = "";
    for (const c of sc.cards) {
      const p = pop(t, c.t);
      if (p.on) {
        const inner = c.kind === "github"
          ? `<svg width="110" height="110" viewBox="0 0 16 16" style="position:absolute;left:50px;top:60px"><path fill="#111" d="M8 0C3.58 0 0 3.58 0 8c0 3.54 2.29 6.53 5.47 7.59.4.07.55-.17.55-.38 0-.19-.01-.82-.01-1.49-2.01.37-2.53-.49-2.69-.94-.09-.23-.48-.94-.82-1.13-.28-.15-.68-.52-.01-.53.63-.01 1.08.58 1.23.82.72 1.21 1.87.87 2.33.66.07-.52.28-.87.51-1.07-1.78-.2-3.64-.89-3.64-3.95 0-.87.31-1.59.82-2.15-.08-.2-.36-1.02.08-2.12 0 0 .67-.21 2.2.82.64-.18 1.32-.27 2-.27.68 0 1.36.09 2 .27 1.53-1.04 2.2-.82 2.2-.82.44 1.1.16 1.92.08 2.12.51.56.82 1.27.82 2.15 0 3.07-1.87 3.75-3.65 3.95.29.25.54.73.54 1.48 0 1.07-.01 1.93-.01 2.2 0 .21.15.46.55.38A8.013 8.013 0 0016 8c0-4.42-3.58-8-8-8z"/></svg>
             <div style="position:absolute;left:190px;top:56px;font:500 34px Inter;color:#777">${esc(c.owner)} /</div>
             <div style="position:absolute;left:190px;top:100px;font:800 50px Inter;color:#111">${esc(c.repo)}</div>
             <div style="position:absolute;left:190px;top:168px;display:flex;gap:14px">${c.chips.map(x => `<span class="chip">${esc(x)}</span>`).join("")}</div>`
          : `<img src="${c.img}" style="position:absolute;left:50%;top:50%;transform:translate(-50%,-50%);height:${c.h || 110}px">
             ${c.tag ? `<span class="chip" style="position:absolute;right:30px;top:24px;background:#1b8734;color:#fff">${esc(c.tag)}</span>` : ""}`;
        html += `<div class="card" style="left:${W / 2 - 420}px;top:${y}px;width:840px;height:230px;${tf(p)}opacity:${p.o * o}">${inner}</div>`;
      }
      y += 270;
    }
    return html;
  },

  strike(sc, t) {
    const p = pop(t, sc.start + 0.02), o = outFade(t, sc.end);
    const k = easeOut((t - sc.strike_at) / 0.22), shake = t > sc.strike_at && t < sc.strike_at + 0.2 ? Math.sin(t * 90) * 8 : 0;
    return `<div class="card" style="left:${W / 2 - 380}px;top:${TOP_CY - 230}px;width:760px;height:460px;${tf(p, `translateX(${shake}px)`)}opacity:${p.o * o}">
      <div style="position:absolute;left:290px;top:60px;width:180px;height:200px">
        ${[0, 1, 2].map(i => `<div style="position:absolute;left:0;top:${30 + i * 52}px;width:180px;height:62px;background:#d9d9de;border-radius:0 0 90px 90px / 0 0 26px 26px"></div>`).join("")}
        <div style="position:absolute;left:0;top:10px;width:180px;height:52px;border-radius:50%;background:#bdbdc4"></div>
        <div style="position:absolute;left:62px;top:96px;width:56px;height:46px;background:#111;border-radius:8px"></div>
        <div style="position:absolute;left:72px;top:70px;width:36px;height:40px;border:8px solid #111;border-bottom:none;border-radius:20px 20px 0 0"></div></div>
      <div style="position:absolute;left:0;right:0;top:300px;text-align:center;font:800 64px Inter;color:#111">${esc(sc.title)}</div>
      <div style="position:absolute;left:0;right:0;top:385px;text-align:center;font:italic 500 40px 'Playfair Display';color:#888">${esc(sc.sub || "")}</div>
      ${k > 0 ? `<svg style="position:absolute;left:-40px;top:-30px" width="840" height="520"><line x1="40" y1="500" x2="${40 + 760 * k}" y2="${500 - 480 * k}" stroke="#e53935" stroke-width="22" stroke-linecap="round"/></svg>` : ""}</div>`;
  },

  checklist(sc, t) {
    const p = pop(t, sc.start + 0.02), o = outFade(t, sc.end), rh = 104;
    const h = 130 + sc.rows.length * rh + 30;
    let rows = "";
    sc.rows.forEach((r, i) => {
      const q = pop(t, r.t, 0.7);
      if (!q.on) return;
      const c = pop(t, r.t + 0.12, 0.2);
      rows += `<div style="position:absolute;left:40px;right:40px;top:${130 + i * rh}px;height:84px;display:flex;align-items:center;${tf(q)}transform-origin:left center">
        <span style="font-size:52px;width:80px;color:#111">${r.icon}</span>
        <span style="font:800 40px Inter;color:#111">${esc(r.name)}</span>
        <span style="font:italic 500 36px 'Playfair Display';color:#888;margin-left:16px">${esc(r.desc)}</span>
        <span style="margin-left:auto;width:60px;height:60px;border-radius:50%;background:#28c840;display:flex;align-items:center;justify-content:center;${tf(c)}">
          <svg width="34" height="34" viewBox="0 0 24 24"><path d="M4 12.5l5 5L20 6.5" fill="none" stroke="#fff" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round"/></svg></span></div>`;
    });
    return `<div class="card" style="left:${W / 2 - 460}px;top:${TOP_CY - h / 2}px;width:920px;height:${h}px;${tf(p)}opacity:${p.o * o}">
      <div style="position:absolute;left:40px;top:40px;font:800 46px Inter;color:#111">${esc(sc.title)}</div>${rows}</div>`;
  },

  converge(sc, t) {
    let html = SCENES.window({ ...sc, type: "window" }, t);
    const w = sc.w || 960, cx = W / 2, cy = sc.cy || TOP_CY;
    sc.chips.forEach((c, i) => {
      const a = clamp((t - (sc.chips_at + i * 0.08)) / 0.25);
      if (a <= 0) return;
      const m = easeOut((t - sc.merge_at) / 0.45);
      const x = lerp(c.x, cx, m), y = lerp(c.y, cy, m), s = lerp(1, 0.2, m), op = a * (1 - clamp((t - sc.merge_at - 0.3) / 0.15));
      html += `<span class="chip big" data-layout-allow-overlap="true" style="position:absolute;left:${x}px;top:${y}px;transform:translate(-50%,-50%) scale(${s});opacity:${op}">${c.label}</span>`;
    });
    return html;
  },

  comment(sc, t) {
    const p = pop(t, sc.start + 0.02), o = outFade(t, sc.end);
    const n = t < sc.type_at ? 0 : Math.min(sc.text.length, Math.floor((t - sc.type_at) / sc.per_char) + 1);
    const sent = t > sc.send_at;
    const caret = (Math.floor(t * 2.4) % 2 === 0 || (n > 0 && n < sc.text.length)) && !sent;
    return `<div class="card" style="left:${W / 2 - 450}px;top:${TOP_CY - 230}px;width:900px;height:460px;${tf(p)}opacity:${p.o * o}">
      <div style="position:absolute;left:40px;top:36px;font:800 42px Inter;color:#111">${esc(sc.title)}</div>
      ${sent ? `<div style="position:absolute;left:40px;top:120px;display:flex;align-items:center;gap:22px;${tf(pop(t, sc.send_at, 0.7))}">
          <div style="width:76px;height:76px;border-radius:50%;background:conic-gradient(#feda75,#fa7e1e,#d62976,#962fbf,#4f5bd5,#feda75)"></div>
          <div><div style="font:800 32px Inter;color:#111">siz <span style="font:500 28px Inter;color:#777">hozirgina</span></div>
          <div style="font:500 40px Inter;color:#111">${esc(sc.text)}</div></div></div>` : ""}
      <div style="position:absolute;left:30px;right:30px;bottom:34px;height:110px;border-radius:55px;background:#f2f2f4;display:flex;align-items:center;padding:0 22px 0 36px">
        <span style="font:500 44px Inter;color:${n ? "#111" : "#aaa"}">${n ? esc(sent ? "" : sc.text.slice(0, n)) : esc(sc.placeholder)}</span>
        ${caret ? `<span style="width:4px;height:52px;background:#0a84ff;margin-left:4px"></span>` : ""}
        <span style="margin-left:auto;width:76px;height:76px;border-radius:50%;background:${n === sc.text.length && !sent ? "#0a84ff" : "#cfcfd4"};display:flex;align-items:center;justify-content:center">
          <svg width="36" height="36" viewBox="0 0 24 24"><path d="M3 11.5L21 3l-7.5 18-2.5-7.5z" fill="#fff"/></svg></span></div></div>`;
  },
};

// ---------- captions ----------
function captionHTML(t) {
  const c = PLAN.captions.find(c => t >= c.start && t < c.end);
  if (!c) return "";
  const face = modeAt(t) === "face";
  const words = c.words.map(w => {
    if (PLAN.caption_style === "mono") w = w.toUpperCase();
    const em = PLAN.emphasis.includes(w.replace(/[.,!?]/g, "").toLowerCase());
    const style = PLAN.caption_style === "mono" ? "font:800 76px/1.05 Inter;letter-spacing:1px" : em && PLAN.caption_style !== "mono" ? `font:italic 700 ${face ? 118 : 108}px/1.05 'Playfair Display'` : `font:800 ${face ? 96 : 86}px/1.05 Inter;letter-spacing:-2px`;
    return `<span style="${style};display:inline-block;margin:0 12px">${esc(w)}</span>`;
  }).join(" ");
  const y = face ? 1420 : PLAN.caption_y;
  const capsule = PLAN.caption_style === "capsule";
  const col = capsule ? "color:#111" : face ? "color:#fff;text-shadow:0 4px 30px rgba(0,0,0,.45)" : (DARK ? "color:#fff" : "color:#111");
  return `<div style="position:absolute;left:60px;right:60px;top:${y}px;transform:translateY(-50%);text-align:center;${col}"><span style="${PLAN.caption_style === "capsule" ? "display:inline-block;background:rgba(255,255,255,.92);border-radius:24px;padding:14px 24px;box-shadow:0 4px 20px rgba(0,0,0,.08)" : ""}">${words}</span></div>`;
}
function modeAt(t) { const l = PLAN.layout.find(l => t >= l.start && t < l.end); return l ? l.mode : "top"; }

function render(t) {
  let html = "";
  for (const sc of PLAN.scenes) if (t >= sc.start && t < sc.end) html += SCENES[sc.type](sc, t);
  html += captionHTML(t);
  const root = document.getElementById("root");
  if (DARK) {
    html = html.replace(/color:#111/g, "color:#fff").replace(/fill="#111"/g, 'fill="#fff"')
      .replace(/color:#777/g, "color:#b8bbc4").replace(/color:#888/g, "color:#b8bbc4")
      .replace(/background:#f2f2f4/g, "background:#282b33");
  }
  root.innerHTML = html;
  if (PLAN.caption_style === "capsule") {
    const c = root.lastElementChild;
    if (c && c.querySelector("span[style*=background]")) c.style.color = "#111";
  }
  document.querySelectorAll('.media-slot').forEach(e => { e.style.opacity = '0'; });
  return [...root.querySelectorAll("[data-hole]")].map(e => {
    const r = e.getBoundingClientRect();
    const slot = document.getElementById(e.dataset.mediaId);
    if (slot) Object.assign(slot.style, {
      left: `${r.left}px`, top: `${r.top}px`, width: `${r.width}px`, height: `${r.height}px`,
      borderRadius: `${e.dataset.r}px`, opacity: e.dataset.op,
    });
    return { key: e.dataset.hole, x: r.left, y: r.top, w: r.width, h: r.height, r: +e.dataset.r,
             op: +e.dataset.op, local: t - +e.dataset.start + +e.dataset.from };
  });
}

// A property setter runs even when a seek suppresses GSAP event callbacks.
// This makes repeated, backward and random seeks reconstruct the same scene.
const clock = {
  _value: 0,
  get value() { return this._value; },
  set value(t) { this._value = t; render(t); },
};
const timeline = gsap.timeline({ paused: true });
timeline.fromTo(clock, { value: 0 }, { value: PLAN.duration, duration: PLAN.duration, ease: 'none' }, 0);
render(0);
