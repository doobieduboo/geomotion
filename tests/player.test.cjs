// Event-level regression checks. These do not replace browser/device QA.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const { readFileSync } = require('node:fs');
const { resolve } = require('node:path');
const vm = require('node:vm');
const playerRoot = process.env.PLAYER_ROOT || resolve(__dirname, '../.agents/skills/geomotion/templates/player');
const code = readFileSync(resolve(playerRoot, 'app.js'), 'utf8');

class Element {
  constructor() {
    this.handlers = new Map(); this.attributes = {}; this.hidden = false;
    this.style = { setProperty: (key, value) => { this.attributes[key] = value; } };
    this.value = '0'; this.children = []; this.disabled = false;
  }
  addEventListener(name, fn) {
    if (!this.handlers.has(name)) this.handlers.set(name, []);
    this.handlers.get(name).push(fn);
  }
  emit(type, properties = {}) {
    const event = { type, preventDefault() {}, ...properties };
    for (const handler of this.handlers.get(type) || []) handler(event);
  }
  setAttribute(key, value) { this.attributes[key] = value; }
  appendChild(child) { this.children.push(child); }
  focus() {}
  getBoundingClientRect() { return { left: 20, width: 300 }; }
  setPointerCapture(pointer) { this.pointer = pointer; }
  hasPointerCapture(pointer) { return this.pointer === pointer; }
  releasePointerCapture(pointer) { this.pointer = null; this.emit('lostpointercapture', { pointerId: pointer }); }
}
const settle = () => new Promise(resolve => setImmediate(resolve));
async function setup(stage = 'preview', transport = 'range') {
  const ids = ['video', 'quality', 'error', 'download', 'video-stage', 'tap-toggle',
    'play-toggle', 'mute-toggle', 'fullscreen-toggle', 'timeline', 'current-time',
    'total-time', 'play-icon', 'mute-icon', 'video-controls', 'stage', 'eyebrow',
    'title', 'description', 'meta', 'hint', 'credits'];
  const elements = Object.fromEntries(ids.map(id => [id, new Element()]));
  const video = elements.video;
  Object.assign(video, { duration: NaN, readyState: 0, currentTime: 0, paused: true,
    ended: false, loads: [], playCount: 0, controls: true,
    load() { this.loads.push(this.preload); this.readyState = 0; this.duration = NaN; },
    pause() { this.paused = true; this.emit('pause'); },
    play() { this.paused = false; this.ended = false; this.playCount++; this.emit('play'); return Promise.resolve(); },
    metadata() { this.readyState = 1; this.duration = 33.625; this.emit('loadedmetadata'); },
  });
  const document = new Element();
  Object.assign(document, { fullscreenEnabled: true,
    querySelector: selector => elements[selector.slice(1)],
    createElement: () => new Element(),
    async exitFullscreen() { this.fullscreenElement = null; this.emit('fullscreenchange'); },
  });
  elements['video-stage'].requestFullscreen = async function() { document.fullscreenElement = this; document.emit('fullscreenchange'); };
  const mediaRequests = [], revoked = [];
  vm.runInNewContext(code, { document, AbortController,
    URL: { createObjectURL: () => 'blob:local-video', revokeObjectURL: value => revoked.push(value) },
    fetch: async (url, options) => {
    if (url !== 'media.json') {
      mediaRequests.push({ url, options });
      if (transport === 'error') return { ok: false };
      return transport === 'range'
        ? { ok: true, status: 206, body: { cancel: async () => {} } }
        : { ok: true, status: 200, blob: async () => ({ type: 'video/mp4' }) };
    }
    return { ok: true, json: async () => ({ stage, title: 'Example', duration: 33.625,
      variants: [360, 1080].map(height => ({ height, src: `${height}.mp4`, bytes: 2000000 })) }) };
  }});
  await settle();
  return { ...elements, document, mediaRequests, revoked };
}
const pointer = (fraction, pointerId = 1) => ({ pointerId, isPrimary: true, button: 0, clientX: 27 + fraction * 286 });
const near = (actual, expected) => assert.ok(Math.abs(Number(actual) - expected) < 0.02, `${actual} != ${expected}`);

test('initial page keeps media unloaded, uses invisible tap target and stage-safe download', async () => {
  const p = await setup();
  assert.deepEqual(p.video.loads, ['none']);
  assert.equal(p.video.controls, false);
  assert.equal(p['tap-toggle'].hidden, false);
  assert.equal(p.quality.children.length, 1);
  assert.equal(p.download.href, '360.mp4');
  assert.equal(p.timeline.disabled, false);
  assert.equal(p['total-time'].textContent, '0:33');
  assert.equal(p.mediaRequests.length, 0);
  const html = readFileSync(resolve(playerRoot, 'index.html'), 'utf8');
  assert.match(html, /id="tap-toggle"[^>]*><\/button>/);
});
test('tap before metadata keeps requested position until metadata becomes available', async () => {
  const p = await setup();
  p.timeline.emit('pointerdown', pointer(0.6));
  p.timeline.emit('pointerup', pointer(0.6));
  await settle();
  assert.equal(p.video.paused, true);
  assert.deepEqual(p.video.loads, ['none', 'auto']);
  near(p.timeline.value, 33.625 * 0.6);
  p.video.metadata();
  near(p.video.currentTime, 33.625 * 0.6);
  assert.equal(p.video.paused, true);
});
test('drag while playing does not snap back on timeupdate and resumes only once', async () => {
  const p = await setup(); p.video.metadata();
  p['tap-toggle'].emit('click');
  assert.equal(p.video.paused, false);
  p.timeline.emit('pointerdown', pointer(0.2));
  assert.equal(p.video.paused, true);
  p.timeline.emit('pointermove', pointer(0.75));
  p.video.currentTime = 7; p.video.emit('timeupdate');
  near(p.timeline.value, 33.625 * 0.75);
  p.timeline.emit('pointerup', pointer(0.8));
  await settle();
  near(p.video.currentTime, 33.625 * 0.8);
  assert.equal(p.video.paused, false);
  assert.equal(p.video.playCount, 2);
});
test('seeking after end stays paused, and transparent tap replays from zero', async () => {
  const p = await setup(); p.video.metadata();
  p.video.currentTime = 33.625; p.video.ended = true; p.video.emit('ended');
  p.timeline.emit('pointerdown', pointer(0.25));
  p.timeline.emit('pointerup', pointer(0.25));
  await settle();
  near(p.video.currentTime, 33.625 / 4);
  assert.equal(p.video.playCount, 0);
  p.video.currentTime = 33.625; p.video.ended = true;
  p['tap-toggle'].emit('click');
  await settle();
  assert.equal(p.video.currentTime, 0);
  assert.equal(p.video.paused, false);
});
test('cancelled drag releases state, keyboard seeking clamps, range input remains usable', async () => {
  const p = await setup(); p.video.metadata(); p.video.play();
  p.timeline.value = '0'; p.timeline.emit('input'); await settle();
  p.timeline.emit('pointerdown', pointer(0.5));
  p.timeline.emit('pointercancel', pointer(0.5));
  assert.equal(p.video.paused, false);
  p.timeline.emit('keydown', { key: 'Home' }); assert.equal(p.video.currentTime, 0);
  p.timeline.emit('keydown', { key: 'ArrowLeft' }); assert.equal(p.video.currentTime, 0);
  p.timeline.emit('keydown', { key: 'ArrowRight' }); assert.equal(p.video.currentTime, 5);
  p.timeline.emit('keydown', { key: 'End' }); assert.equal(p.video.currentTime, 33.625);
  p.timeline.value = '12.5'; p.timeline.emit('input'); assert.equal(p.video.currentTime, 12.5);
  assert.equal(p.timeline.attributes['aria-valuetext'], '0:12 dari 0:33');
});
test('quality switch preserves requested paused position and current playing position', async () => {
  const p = await setup('final'); p.video.metadata();
  p.timeline.value = '12.5'; p.timeline.emit('input');
  p.quality.value = '1080'; p.quality.emit('change'); p.video.metadata();
  await settle();
  assert.equal(p.video.currentTime, 12.5); assert.equal(p.video.paused, true);
  assert.equal(p.download.href, '1080.mp4');
  p.video.play(); p.video.currentTime = 20;
  p.quality.value = '360'; p.quality.emit('change'); p.video.metadata();
  await settle();
  assert.equal(p.video.currentTime, 20); assert.equal(p.video.paused, false);
});
test('mute and fullscreen remain available outside the transparent tap target', async () => {
  const p = await setup(); p['mute-toggle'].emit('click');
  assert.equal(p.video.muted, true);
  p.video.emit('volumechange');
  assert.equal(p['mute-toggle'].attributes['aria-label'], 'Aktifkan audio');
  p['fullscreen-toggle'].emit('click');
  assert.equal(p.document.fullscreenElement, p['video-stage']);
  assert.equal(p['fullscreen-toggle'].attributes['aria-label'], 'Keluar layar penuh');
});
test('hosts ignoring Range use a seekable local Blob only after explicit seek', async () => {
  const p = await setup('preview', 'full');
  p.video.metadata(); p.video.play();
  assert.equal(p.mediaRequests.length, 0);
  p.timeline.emit('pointerdown', pointer(0.7));
  p.timeline.emit('pointerup', pointer(0.7));
  await settle();
  assert.equal(p.mediaRequests.length, 1);
  assert.equal(p.mediaRequests[0].options.headers.Range, 'bytes=0-0');
  assert.equal(p.video.src, 'blob:local-video');
  p.video.metadata();
  near(p.video.currentTime, 33.625 * 0.7);
  assert.equal(p.video.paused, false);
  p.timeline.emit('keydown', { key: 'Home' });
  assert.equal(p.video.currentTime, 0);
  assert.equal(p.mediaRequests.length, 1);
});
test('paused Blob seek stays paused and changing quality releases the old Blob', async () => {
  const p = await setup('final', 'full');
  p.timeline.emit('pointerdown', pointer(0.5));
  p.timeline.emit('pointerup', pointer(0.5));
  await settle(); p.video.metadata();
  near(p.video.currentTime, 33.625 / 2);
  assert.equal(p.video.paused, true);
  p.quality.value = '1080'; p.quality.emit('change');
  assert.deepEqual(p.revoked, ['blob:local-video']);
});
test('failed media buffering reports an error and allows another seek attempt', async () => {
  const p = await setup('preview', 'error');
  p.timeline.emit('pointerdown', pointer(0.5)); p.timeline.emit('pointerup', pointer(0.5));
  await settle();
  assert.equal(p.error.hidden, false);
  assert.equal(p['video-stage'].attributes['aria-busy'], 'false');
  p.timeline.emit('keydown', { key: 'ArrowLeft' });
  await settle();
  assert.equal(p.mediaRequests.length, 2);
});
