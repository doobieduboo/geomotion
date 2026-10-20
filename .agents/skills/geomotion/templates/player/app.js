const video = document.querySelector("#video"),
  quality = document.querySelector("#quality"),
  error = document.querySelector("#error"),
  download = document.querySelector("#download");
const allowed = (stage) => (stage === "final" ? [360, 1080] : [360]);
let variants = [];
const stage = document.querySelector("#video-stage"),
  tapToggle = document.querySelector("#tap-toggle"),
  playToggle = document.querySelector("#play-toggle"),
  muteToggle = document.querySelector("#mute-toggle"),
  fullscreenToggle = document.querySelector("#fullscreen-toggle"),
  timeline = document.querySelector("#timeline"),
  currentTime = document.querySelector("#current-time"),
  totalTime = document.querySelector("#total-time");
let durationHint = 0, pendingTime = null, loadingForSeek = false,
  resumeOnMetadata = false, scrubPointer = null, resumeAfterScrub = false;
let sourceUrl = "", sourceGeneration = 0, objectUrl = null,
  rangeSupported = false, seekRequest = null;
video.volume = 1;
video.muted = false;
const duration = () => Number.isFinite(video.duration) && video.duration > 0
  ? video.duration : durationHint;
const clock = (seconds) => {
  const value = Math.max(0, Math.floor(Number(seconds) || 0));
  return `${Math.floor(value / 60)}:${String(value % 60).padStart(2, "0")}`;
};
function updateTimeline() {
  const length = duration();
  const time = pendingTime ?? (scrubPointer !== null ? Number(timeline.value) : video.currentTime || 0);
  timeline.max = String(length);
  timeline.disabled = !(length > 0);
  timeline.value = String(Math.min(time, length));
  timeline.style.setProperty("--progress", `${length ? time / length * 100 : 0}%`);
  timeline.setAttribute("aria-valuetext", `${clock(time)} dari ${clock(length)}`);
  currentTime.textContent = clock(time);
  totalTime.textContent = clock(length);
}
function updatePlayback() {
  const label = video.paused || video.ended ? "Putar video" : "Jeda video";
  tapToggle.setAttribute("aria-label", label);
  playToggle.setAttribute("aria-label", label);
  document.querySelector("#play-icon").setAttribute("d",
    video.paused || video.ended ? "M8 5v14l11-7z" : "M6 5h4v14H6zm8 0h4v14h-4z");
}
function play() {
  video.play().catch((e) => {
    if (e.name === "AbortError") return;
    error.textContent = "Pemutaran belum berhasil. Ketuk video untuk mencoba lagi.";
    error.hidden = false;
    updatePlayback();
  });
}
function prepareSeekSource() {
  if (seekRequest) return;
  const generation = sourceGeneration;
  const controller = new AbortController();
  seekRequest = controller;
  stage.setAttribute("aria-busy", "true");
  fetch(sourceUrl, { headers: { Range: "bytes=0-0" }, signal: controller.signal })
    .then(async (response) => {
      if (!response.ok) throw Error("Media request failed");
      if (response.status === 206) {
        await response.body?.cancel();
        if (generation !== sourceGeneration) return;
        rangeSupported = true;
        if (pendingTime !== null) seekTo(pendingTime);
        return;
      }
      // Some static hosts ignore Range. A local Blob is seekable without it.
      // This full download occurs only after the user explicitly seeks.
      const blob = await response.blob();
      if (generation !== sourceGeneration) return;
      const resume = !video.paused && scrubPointer === null;
      const time = pendingTime ?? (video.currentTime || 0);
      objectUrl = URL.createObjectURL(blob);
      video.src = objectUrl;
      video.preload = "auto";
      video.load();
      pendingTime = time;
      resumeOnMetadata = resume;
      loadingForSeek = true;
      if (resume) play();
      updateTimeline();
    })
    .catch((e) => {
      if (generation !== sourceGeneration || e.name === "AbortError") return;
      error.textContent = "Posisi video belum berhasil dimuat. Coba geser bar durasi lagi.";
      error.hidden = false;
    })
    .finally(() => {
      if (generation !== sourceGeneration) return;
      seekRequest = null;
      stage.setAttribute("aria-busy", "false");
    });
}
function seekTo(seconds) {
  const length = duration();
  if (!(length > 0) || !Number.isFinite(seconds)) return;
  pendingTime = Math.max(0, Math.min(seconds, length));
  timeline.value = String(pendingTime);
  if (!rangeSupported && !objectUrl) {
    prepareSeekSource();
  } else if (video.readyState >= 1) {
    try {
      video.currentTime = pendingTime;
      pendingTime = null;
    } catch {
      // Retry the requested position when media data becomes available.
    }
  } else if (!loadingForSeek) {
    loadingForSeek = true;
    video.preload = "auto"; // Only fetch media after a playback/seek interaction.
    video.load();
  }
  updateTimeline();
}
function togglePlayback() {
  if (video.paused || video.ended) {
    resumeOnMetadata = false;
    if (video.ended) seekTo(0);
    play();
  } else {
    resumeOnMetadata = false;
    video.pause();
  }
}
tapToggle.addEventListener("click", togglePlayback);
playToggle.addEventListener("click", togglePlayback);
function seekFromPointer(event) {
  const bounds = timeline.getBoundingClientRect();
  const fraction = Math.max(0, Math.min(1, (event.clientX - bounds.left - 7) / Math.max(1, bounds.width - 14)));
  seekTo(fraction * duration());
}
timeline.addEventListener("pointerdown", (event) => {
  if (timeline.disabled || !event.isPrimary || event.button !== 0 || scrubPointer !== null) return;
  event.preventDefault();
  timeline.focus({ preventScroll: true });
  scrubPointer = event.pointerId;
  resumeAfterScrub = !video.paused;
  resumeOnMetadata = false;
  video.pause();
  timeline.setPointerCapture(event.pointerId);
  seekFromPointer(event);
});
timeline.addEventListener("pointermove", (event) => {
  if (event.pointerId !== scrubPointer) return;
  event.preventDefault();
  seekFromPointer(event);
});
function finishScrub(event) {
  if (scrubPointer === null || event.pointerId !== scrubPointer) return;
  if (event.type === "pointerup") seekFromPointer(event);
  scrubPointer = null;
  if (timeline.hasPointerCapture(event.pointerId)) timeline.releasePointerCapture(event.pointerId);
  const resume = resumeAfterScrub;
  resumeAfterScrub = false;
  if (resume) play();
}
for (const name of ["pointerup", "pointercancel", "lostpointercapture"]) timeline.addEventListener(name, finishScrub);
// Native range input remains usable with keyboards and assistive technology.
timeline.addEventListener("input", () => seekTo(Number(timeline.value)));
timeline.addEventListener("keydown", (event) => {
  const time = Number(timeline.value), length = duration();
  const target = { ArrowLeft: time - 5, ArrowDown: time - 5,
    ArrowRight: time + 5, ArrowUp: time + 5, Home: 0, End: length,
    PageDown: time - length / 10, PageUp: time + length / 10 }[event.key];
  if (target === undefined) return;
  event.preventDefault();
  seekTo(target);
});
muteToggle.addEventListener("click", () => { video.muted = !video.muted; });
video.addEventListener("volumechange", () => {
  const muted = video.muted || video.volume === 0;
  muteToggle.setAttribute("aria-label", muted ? "Aktifkan audio" : "Bisukan audio");
  document.querySelector("#mute-icon").setAttribute("d", muted
    ? "M3 9v6h4l5 4V5L7 9zm13 0 2 2 2-2 1 1-2 2 2 2-1 1-2-2-2 2-1-1 2-2-2-2z"
    : "M3 9v6h4l5 4V5L7 9zm12-2v2a4 4 0 010 6v2a6 6 0 000-10z");
});
const fullscreenEnabled = Boolean(stage.requestFullscreen && document.fullscreenEnabled);
fullscreenToggle.hidden = !fullscreenEnabled;
fullscreenToggle.addEventListener("click", async () => {
  try {
    if (document.fullscreenElement) await document.exitFullscreen();
    else await stage.requestFullscreen();
  } catch {
    error.textContent = "Layar penuh tidak tersedia di browser ini.";
    error.hidden = false;
  }
});
document.addEventListener("fullscreenchange", () => {
  fullscreenToggle.setAttribute("aria-label", document.fullscreenElement ? "Keluar layar penuh" : "Layar penuh");
});
function applyPendingSeek() {
  loadingForSeek = false;
  if (pendingTime !== null) seekTo(pendingTime);
  if (resumeOnMetadata) { resumeOnMetadata = false; play(); }
  updateTimeline();
}
video.addEventListener("loadedmetadata", applyPendingSeek);
video.addEventListener("canplay", () => { if (pendingTime !== null) applyPendingSeek(); });
for (const name of ["timeupdate", "durationchange", "seeked", "ended"]) video.addEventListener(name, updateTimeline);
for (const name of ["play", "pause", "ended"]) video.addEventListener(name, updatePlayback);
// Keep native controls as a fallback until custom controls have initialized.
video.controls = false;
tapToggle.hidden = false;
document.querySelector("#video-controls").hidden = false;
updatePlayback();
function choose(item, keepTime = false) {
  const time = keepTime ? (pendingTime ?? (video.currentTime || 0)) : 0,
    wasPlaying = keepTime && !video.paused;
  error.hidden = true;
  sourceGeneration++;
  seekRequest?.abort();
  seekRequest = null;
  const previousObjectUrl = objectUrl;
  objectUrl = null;
  rangeSupported = false;
  sourceUrl = item.src;
  stage.setAttribute("aria-busy", "false");
  pendingTime = time || null;
  resumeOnMetadata = wasPlaying;
  loadingForSeek = false;
  video.preload = wasPlaying ? "auto" : "none";
  video.src = item.src;
  video.load();
  if (previousObjectUrl) URL.revokeObjectURL(previousObjectUrl);
  if (wasPlaying) play();
  updateTimeline();
  download.href = item.src;
  download.download = item.downloadName || `geomotion-${item.height}p.mp4`;
  download.textContent = `Download ${item.height}p · ${(item.bytes / 1e6).toFixed(1).replace(".", ",")} MB`;
  download.hidden = false;
}
quality.addEventListener("change", () => {
  const item = variants.find((v) => String(v.height) === quality.value);
  if (item) choose(item, true);
});
video.addEventListener("error", () => {
  error.textContent =
    "Video belum berhasil dimuat. Coba ganti kualitas atau gunakan tombol download.";
  error.hidden = false;
});
video.addEventListener("playing", () => {
  error.hidden = true;
});
fetch("media.json", { cache: "no-store" })
  .then((r) => {
    if (!r.ok) throw Error("Video belum tersedia.");
    return r.json();
  })
  .then((media) => {
    if (!["preview", "final"].includes(media.stage))
      throw Error("Tahap video tidak valid.");
    variants = media.variants.filter((v) =>
      allowed(media.stage).includes(v.height),
    );
    if (!variants.length) throw Error("Video untuk tahap ini belum tersedia.");
    durationHint = Number(media.duration) || 0;
    document.querySelector("#stage").textContent =
      media.stage === "final" ? "Final" : "Preview · Editing";
    document.querySelector("#eyebrow").textContent =
      media.category || "GEOMOTION / VIDEO";
    document.querySelector("#title").textContent = media.title;
    document.title = media.title + " — GeoMotion";
    document.querySelector("#description").textContent =
      media.stage === "final"
        ? "Versi final siap ditonton dan diunduh. Pilih kualitas yang sesuai koneksi."
        : "Preview komposisi dan editing. Versi 1080p dibuat setelah final diminta.";
    document.querySelector("#meta").textContent =
      `${media.duration.toFixed(1).replace(".", ",")} detik · Vertikal 9:16` +
      (media.narrated ? " · VO + subtitle" : "");
    document.querySelector("#hint").textContent =
      media.stage === "final"
        ? "Semua pilihan memakai file ringkas."
        : "Selama revisi, pemutar dan download tetap 360p.";
    if (media.poster) video.poster = media.poster;
    if (media.credits) {
      document.querySelector("#credits").href = media.credits;
    } else document.querySelector("#credits").hidden = true;
    for (const item of variants) {
      const option = document.createElement("option");
      option.value = item.height;
      option.textContent = `${item.height}p${item.height === 360 ? " — hemat data" : ""} · ${(item.bytes / 1e6).toFixed(1).replace(".", ",")} MB`;
      quality.appendChild(option);
    }
    const preferred =
      media.stage === "preview" ? 360 : media.defaultQuality || 1080;
    const initial =
      variants.find((v) => v.height === preferred) || variants.at(-1);
    quality.value = initial.height;
    quality.disabled = false;
    choose(initial);
  })
  .catch((e) => {
    error.textContent = e.message;
    error.hidden = false;
    document.querySelector("#stage").textContent = "Belum tersedia";
  });
