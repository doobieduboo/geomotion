# GeoMotion

Toolkit dan skill Codex untuk animasi peta berdasarkan brief pengguna. Lokasi, topik, periode dan narasi berasal dari proyek, bukan cerita bawaan repo.

## Mulai atau lanjutkan pekerjaan

Pilih environment yang memiliki dependensi dan kredensial proyek. Buka repo, lalu gunakan:

> Baca repo GeoMotion terbaru dan terapkan konfigurasinya pada proyek ini. Lanjutkan dari hasil yang sudah disetujui.

Instruksi ini berlaku untuk obrolan baru maupun yang sedang berjalan. Agent mengikuti [AGENTS.md](AGENTS.md), menyinkronkan checkout tanpa menimpa pekerjaan lokal, lalu membaca skill dan preset terbaru. Perubahan repo tidak mengganti environment sesi atau membawa source produksi dari obrolan lain.

## Produksi

- Peta satelit datar Esri mengisi frame secara default; overlay geografis, outline, zoom, pan, rotasi dan wrap bujur tetap didukung.
- Teks tambahan, caption foto dan kredit visual otomatis nonaktif. Nama geografis, subtitle VO dan judul pembuka yang disetujui/ditulis eksplisit tetap tersedia; permintaan teks eksplisit memakai override scene `text_policy`. Foto callout secara default hanya gambar. Provenance, tanggal, kredit/lisensi dan batas verifikasi tetap disimpan di `SOURCES.md` proyek.
- Esri World Imagery adalah satu-satunya basemap; metadata atribusi dan ketentuan penggunaannya mengikuti [referensi basemap](.agents/skills/geomotion/references/basemaps.md).
- Editing memakai preview ringan. Final native hanya dibuat saat diminta, langsung dalam encoding ringkas.
- Narasi/VO yang disetujui dipakai ulang untuk revisi visual. Kamera, subtitle dan arsip mengikuti frasa aktual.
- Player Sites dipakai ulang, dengan pilihan kualitas sesuai tahap dan satu tombol download.

Nilai resolusi, model/suara TTS, font, posisi subtitle, audio, kamera dan pacing ada di [defaults.json](.agents/skills/geomotion/defaults.json). Jangan memelihara salinan preset di dokumen atau prompt lain.

## Menjalankan

Python 3.10+ dan FFmpeg diperlukan. Font berlisensi sudah disertakan.

```bash
python -m pip install -r .agents/skills/geomotion/scripts/requirements.txt
python .agents/skills/geomotion/scripts/render_scene.py scene.json --mode preview --output outputs/preview.mp4
```

Untuk pemeriksaan satu frame native tanpa FFmpeg atau audio, jalankan renderer dengan `--still --output sample.png --start-frame N`; gunakan mode ekspor tahap proyek.

Mulai dari [template scene](.agents/skills/geomotion/templates/scene.json), lalu isi kamera dan layer berdasarkan brief. Jalur aset relatif terhadap scene. Renderer menangani visual dan audio supplied. Subtitle dari cue aktual dapat dibakar; CTA yang diminta eksplisit dan diaktifkan lewat `text_policy.extra_annotations` dapat ditempatkan otomatis di ruang aman; TTS, efek khusus dan mixing tetap memerlukan langkah produksi terpisah. Perlindungan fokus peta, penempatan panel, batas kepadatan dan pemeriksaan benturan mengikuti [kontrak komposisi](.agents/skills/geomotion/references/composition.md#executable-composition-contract). Pipeline menyediakan render paralel/checkpoint, clock terpadu, manifest arsip, lock revisi dan QA hasil encode; lihat [kontrak pipeline](.agents/skills/geomotion/references/pipeline.md). Lihat [kemampuan aktual](.agents/skills/geomotion/references/capabilities.md).

Pemasangan skill pada mesin ini bersifat opsional:

```bash
python scripts/install_skill.py
```

Baca [panduan mulai](docs/getting-started.md) untuk penggantian instalasi dan diagnosis environment.

## Dokumentasi

| Sumber | Tanggung jawab |
|---|---|
| [AGENTS.md](AGENTS.md) | Cara agent membaca, memperbarui dan merawat repo |
| [SKILL.md](.agents/skills/geomotion/SKILL.md) | Workflow produksi |
| [defaults.json](.agents/skills/geomotion/defaults.json) | Preset tunggal |
| [Indeks referensi](.agents/skills/geomotion/references/README.md) | Kontrak teknis per bidang |
| [Arsitektur](docs/architecture.md) | Struktur dan batas implementasi |
| [SOURCES.md](SOURCES.md) | Kebijakan sumber dan lisensi |

```bash
python -m unittest discover -s tests
```
