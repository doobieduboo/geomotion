# GeoMotion

Toolkit dan skill Codex untuk **animasi peta yang agnostik topik**. Negara, lokasi, periode, durasi dan narasi mengikuti brief; tidak ada cerita bawaan. Peta, batas, label, bendera, rute, aset 2.5D dan gambar dipilih sesuai kebutuhan.

## Mulai di chat baru

1. Pilih cloud environment **geomotion** sebelum memulai obrolan jika memakai konfigurasi pribadi yang sudah disiapkan.
2. Buka repo ini, lalu minta: **“Pakai $geomotion untuk membuat animasi peta sesuai brief berikut: …”**
3. Agent membaca [AGENTS.md](AGENTS.md), skill dan preset produksi. Checkout/skill lama perlu disinkronkan sebelum memakai aturan terbaru.

Repo menyimpan kode dan preferensi; API key disimpan di environment. Membuka repo saja tidak memindahkan sesi dari Base Environment. Detail: [panduan mulai dan environment](docs/getting-started.md).

## Default produksi

| Tahap | Hasil dan player |
|---|---|
| Komposisi / editing | 360×640, 24 fps; player hanya 360p |
| Final diminta | Render sumber native 1080×1920, 30 fps, langsung ringkas; player menawarkan 360p/1080p |

Satu tombol download mengikuti kualitas terpilih. UI player dipakai ulang. Tidak ada ekspor 720p atau master besar secara default; final bukan upscale preview.

VO memakai model **`gemini-2.5-flash-preview-tts`**, suara default **Charon**, dan gaya **fast-paced yang tetap jelas**, tanpa fallback model/provider atau penggunaan berbayar otomatis. Audio yang disetujui dipakai ulang saat revisi visual. Kuota/reset mengikuti akun dan model. Baca [aturan TTS](.agents/skills/geomotion/references/tts.md).

Gaya: peta dominan, kamera mengikuti frasa, Montserrat ExtraBold untuk CTA, Open Sans untuk label/subtitle, subtitle terpusat dan tidak bertabrakan dengan elemen lain. Semua nilai tersimpan di [defaults.json](.agents/skills/geomotion/defaults.json).

Pacing Shorts mengikuti [retention.md](.agents/skills/geomotion/references/retention.md): hook cepat, perubahan visual yang bermakna mengikuti frasa, subtitle terbaca, serta minim jeda kosong. Ini default editorial, bukan jaminan angka retensi.

## Menjalankan toolkit

Python 3.10+, FFmpeg, Pillow dan NumPy diperlukan; font Open Sans/Montserrat beserta lisensi OFL sudah disertakan.

```bash
python -m pip install -r .agents/skills/geomotion/scripts/requirements.txt
python .agents/skills/geomotion/scripts/render_scene.py scene.json --mode preview --output outputs/preview.mp4
```

Gunakan [template scene](.agents/skills/geomotion/templates/scene.json) sebagai struktur, lalu ganti input anonimnya. Jalur aset relatif terhadap scene. `--mode final` digunakan hanya setelah final diminta. Renderer menghasilkan layer scene dan bisa menyertakan audio yang sudah tersedia; pembuatan VO, komposisi subtitle/CTA dan mixing membutuhkan langkah produksi terpisah.

Untuk memasang skill pada mesin yang sama:

```bash
python scripts/install_skill.py
```

Instalasi tidak otomatis berlaku di semua perangkat/chat. Untuk mengganti instalasi lama, lihat panduan mulai; jangan menimpa perubahan lokal yang belum diperiksa.

## Peta dokumentasi

| Berkas | Fungsi |
|---|---|
| [AGENTS.md](AGENTS.md) | Instruksi utama agent di repo |
| [SKILL.md](.agents/skills/geomotion/SKILL.md) | Workflow produksi dan pemilihan referensi |
| [defaults.json](.agents/skills/geomotion/defaults.json) | Nilai konfigurasi produksi |
| [Indeks pengetahuan](.agents/skills/geomotion/references/README.md) | Komposisi, aset, scene, audio, TTS, delivery dan troubleshooting |
| [Arsitektur repo](docs/architecture.md) | Pembagian aturan, konfigurasi dan pengetahuan |
| [Kemampuan aktual](docs/capabilities.md) | Fitur implementasi dan batasnya |
| [SOURCES.md](SOURCES.md) | Kebijakan sumber/lisensi toolkit; setiap produksi punya sumber sendiri |

```bash
python -m unittest discover -s tests
```
