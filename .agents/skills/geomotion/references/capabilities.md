# Kemampuan aktual dan batas implementasi

| Bagian | Sudah tersedia di toolkit | Batas / langkah tambahan |
|---|---|---|
| Kamera | Pan/zoom/rotasi, keyframe, easing, lintasan bujur pendek | Peta datar Web Mercator; bukan globe 3D atau orbit bebas |
| Peta | Esri World Imagery, region, batas/reveal/glow | Data/lisensi berasal dari input proyek; proyeksi/seam/luas ekstrem perlu penanganan |
| Bendera | Flag fill polygon dengan holes, flagpole flutter | Tekstur dan geometri harus disediakan; bukan seluruh library bendera |
| Kendaraan | Pemilihan frame atlas sesuai heading dan follower rute | Atlas multi-angle harus tersedia; bukan model 3D atau library kendaraan lengkap |
| Info/gambar | Label/marker dan bubble dengan gambar/audio supplied | Fit/clipping/collision harus diperiksa; foto tidak diambil otomatis |
| Audio scene | Menyertakan file audio yang sudah ada | Tidak membuat VO atau mencampur stem otomatis |
| Gemini TTS | Preset model tetap serta prosedur kredensial/kuota/reuse | Belum ada client Gemini TTS khusus di repo; agent membuat/memakai langkah API terverifikasi |
| Title 01 | Title JSON editable, reveal/caret, compact, subline panel, tilt and optional exit; transparent scene layer | Reconstructed from GIF; user visual approval pending. Other title variants and general subtitle composition remain separate |
| Subtitle/CTA/mixing | Aturan gaya, posisi, wording, timing dan target audio | Belum otomatis dibakar/mix oleh renderer generik; perlu script komposisi proyek |
| Asap/api/ledakan | Kontrak aset dan aturan geografis/komposisi | Efek produksi khusus tidak otomatis menjadi primitive generik |
| Ekspor | Preview dan final native langsung dengan profil ringkas | Source imagery/foto punya resolusi terbatas; native canvas bukan detail tanpa batas |
| Player | UI reusable, filter kualitas per tahap, satu tombol download | `prepare_delivery.py` membuat aset/manifest; deployment tetap lewat Sites |
| Source mentah | Panduan menjaga scene/media/stem/cue portable | Belum ada packager universal proyek; source ZIP tertentu adalah output produksi |

Scene JSON dan layer opsional didokumentasikan di [scene-format.md](scene-format.md). Jangan menambahkan field dari renderer produksi khusus lalu mengklaim renderer generik mendukungnya tanpa implementasi dan pemeriksaan.
