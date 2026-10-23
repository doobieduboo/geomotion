# Kemampuan aktual dan batas implementasi

| Bagian | Sudah tersedia di toolkit | Batas / langkah tambahan |
|---|---|---|
| Kamera | Pan/zoom/rotasi, keyframe, easing, lintasan bujur pendek | Peta datar Web Mercator; bukan globe 3D atau orbit bebas |
| Peta | Esri World Imagery, terrain-preserving multiply region tint and clipped emission/edge bloom, batas/reveal/glow, phrase-timed focus stroke cues replacing the same outline path, supplied transparent Web Mercator world overlays anchored through pan/zoom/rotation/wrap | Data/lisensi berasal dari input proyek; proyeksi/seam/luas ekstrem perlu penanganan |
| Bendera | Flag fill polygon dengan holes, flagpole flutter; overlay geografis tersuplai untuk bendera/lambang yang ikut pan/zoom/rotasi/wrap | Region flag memakai bbox layar gabungan, bukan tekstur geografis tetap. Mask historis, komposisi satu lambang dan transparansi disiapkan proyek; tidak otomatis |
| Kendaraan / ikon bergerak | Pemilihan atlas sesuai heading, supplied animation frames per heading, follower rute dan ground anchor tetap | Atlas/frame animasi harus disuplai; satu heading adalah billboard tetap, bukan model 3D atau multi-angle |
| Panah rute | Stroke reveal persisten, kepala panah mengikuti tangent, casing opsional | Kurva geografis disuplai sebagai titik; bukan rute historis otomatis |
| Info/gambar | Bubble dengan ukuran font aktual, padding preset, rasio gambar asli dan telemetry benturan subtitle | Layout otomatis menghindari fokus, subtitle, simbol dan panel lain; foto tidak dicari otomatis |
| Audio scene | Menyertakan file audio yang sudah ada | Tidak membuat VO atau mencampur stem otomatis |
| Gemini TTS | Preset model tetap serta prosedur kredensial/kuota/reuse | Belum ada client Gemini TTS khusus di repo; agent membuat/memakai langkah API terverifikasi |
| Title 01 | Title JSON editable, reveal/caret, compact, subline panel, tilt and optional exit; transparent scene layer | Reconstructed from GIF; user visual approval pending. Other title variants remain separate; scene composition checks its visible bounds |
| Subtitle | Cues aktual inline/file, phrase event, wrapping dan burn-in sesuai preset | Tidak membuat alignment otomatis; wording/pungtuasi perlu review |
| Komposisi/CTA | Fokus geografis terlindungi, panel bergerak terbatas, CTA authored di tengah/atas fokus, batas jumlah/luas overlay dan pemeriksaan benturan | BBox konservatif; kasus tanpa ruang aman gagal; efek/compositor khusus perlu adapter dan review visual |
| Mixing | Target preset dan pengukuran encoded LUFS/true peak | Mixing stem/ducking dan TTS tetap langkah proyek |
| Timeline/provenance | Clock source/output, cut eksplisit, manifest arsip dan lock hash per domain | Status fakta/reuse dicatat agent; bukan sertifikasi oleh software |
| Render pipeline | Worker terbatas, checkpoint hash/frame count, resume, cache key video per rentang dan reuse lintas revisi terverifikasi, concat native/QA | Invalidasi konservatif termasuk prefix layout/global dependencies; custom runner belum memiliki reuse lintas revisi otomatis |
| Save/load proyek aktif | `pipeline.py save/load`, satu `.geomotion-project.json`, stage final persisten, referensi scene/aset/checkpoint dan deteksi hasil stale | File hanya selama workspace tersedia; tidak memulihkan aset hilang atau menyediakan backup permanen |
| Compositor tambahan | `pipeline.py composite`, PNG/atlas transparan, posisi/ukuran pixel native, fade, encode GOP terdampak, copy video/audio lain dan bukti packet/timing | Memerlukan base checkpoint + render receipt; belum ada parenting geografis/keyframe transform umum, clean-layer extraction, atau penghapusan elemen baked-in |
| Asap/api/ledakan | Kontrak aset dan aturan geografis/komposisi | Efek produksi khusus tidak otomatis menjadi primitive generik |
| Ekspor | Preview dan final native langsung dengan profil ringkas | Source imagery/foto punya resolusi terbatas; native canvas bukan detail tanpa batas |
| Pengiriman | Default aturan: link MP4 langsung pada hosting yang sama; player reusable tersedia bila diminta | CLI `prepare`/`handoff` masih khusus player; pengiriman langsung memerlukan staging/provenance adapter proyek terverifikasi dan native Sites. Belum ada flag direct generik |
| Source mentah | Panduan menjaga scene/media/stem/cue portable | Belum ada packager universal proyek; source ZIP tertentu adalah output produksi |

Scene JSON dan layer opsional didokumentasikan di [scene-format.md](scene-format.md). Jangan menambahkan field dari renderer produksi khusus lalu mengklaim renderer generik mendukungnya tanpa implementasi dan pemeriksaan.

Callouts support source-time `fade_in` / `fade_out` envelopes applied to the complete composed image/panel/caption/leader layer; see scene-format.md.

Image callouts support validated original-pixel `image_crop` detail views and optional `show_leader: false`; source bytes remain unchanged and layout uses the detail's actual aspect ratio. Cropping does not improve source resolution or authenticate the claim; retain context and visible excerpt attribution.

Routes support source-clock whole-layer fade envelopes over visibility `start`–`hide_at`, independent of movement `end`, while preserving the completed stroke during hold.

Appearance recipes are owned by [style.md](style.md); authored camera timing and layer lifetimes by [composition.md](composition.md). These are not automatic scene-generation features. Geometry and transition review follow [quality.md](quality.md).

Outline appearance automatically inherits the reference/focus roles from `defaults.json.region_outline`. A focus cue keeps reference portions visible until revealed, replaces their core/neutral halo locally, and uses its own equally thin colored core and linear-light additive multilayer bloom at a camera-independent screen width. Bloom follows only revealed geometry and holds with the completed boundary; this renderer approximation does not invoke an After Effects plugin. Cue timing/geography still require authoring; explicit scene exceptions override the preset.

Colored region fills inherit `region_fill.blend` and `region_fill.glow`; `fill_blend` and `fill_glow` provide explicit local exceptions. Supplied world overlays preserve authored RGB/alpha by default and support optional projected-alpha bloom; explicit color overlays may request terrain tint. Flag textures retain factual colors and use restrained flag-strength emission. These are geographic compositing features, not automatic mask research, flag preparation or ownership timing. See [scene-format.md](scene-format.md) for accepted fields.
