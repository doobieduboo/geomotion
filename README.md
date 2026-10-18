# GeoMotion

Skill Codex untuk **map animation yang agnostik topik**. Isi, negara, lokasi, waktu, durasi dan alur ditentukan oleh permintaan pengguna serta data scene. Skill menyediakan kemampuan visual yang bisa dikomposisikan sesuai kebutuhan.

Kamera peta, geometri wilayah, batas glow, isian bendera, pin, label, rute, sprite 2.5D, gambar dan bubble info adalah layer opsional. Tidak ada topik atau cerita bawaan.

## Pakai di obrolan baru

1. Buka repo ini di environment Codex baru.
2. Minta: **“Pakai $geomotion untuk membuat animasi peta sesuai brief berikut: …”**
3. Agent membaca `AGENTS.md` dan `.agents/skills/geomotion/SKILL.md`.

Atau pasang skill untuk user Codex pada mesin yang sama:

```bash
python scripts/install_skill.py
```

Environment lain perlu membuka repo atau memasang ulang. Repo tidak otomatis menjadi skill di semua chat ChatGPT/Work; sesi tetap memerlukan akses file dan alat eksekusi. Jika deteksi otomatis tidak tersedia, minta agent membaca file `SKILL.md` tersebut.

## Render dari scene

Input JSON menentukan kamera, layer dan timeline; renderer tidak memilih topik. Mulai dari `.agents/skills/geomotion/templates/scene.json`, lalu ganti koordinat anonim, label dan parameter sesuai kebutuhan. Jalur aset relatif terhadap file scene.

Memerlukan Python 3.10+, FFmpeg, DejaVu Sans atau font pengganti, Pillow dan NumPy:

```bash
python -m pip install -r .agents/skills/geomotion/scripts/requirements.txt
python .agents/skills/geomotion/scripts/render_scene.py scene.json --mode preview --output outputs/preview.mp4
```

Preview **360×640 / 24 fps**. Hanya saat final diminta:

```bash
python .agents/skills/geomotion/scripts/render_scene.py scene.json --mode final --output outputs/final.mp4
```

Final **720×1280 / 30 fps**. Template berisi koordinat anonim untuk memperlihatkan struktur; bukan konten yang harus dipakai. Format lengkap: [.agents/skills/geomotion/references/scene-format.md](.agents/skills/geomotion/references/scene-format.md).

## Toolkit

- Kamera keyframe: pan, zoom, rotasi dan easing.
- Basemap warna polos atau citra satelit; border reveal/glow dari GeoJSON.
- Bendera mengisi polygon wilayah, termasuk pulau dan lubang polygon.
- Marker lokasi, label, flagpole berkibar, rute dan pengikut rute dari sprite atlas.
- Bubble geografis dengan gambar, judul dan baris informasi; audio opsional.
- Kontrak aset multi-angle 2.5D dan utility layer; installer lokal dan tes.

Aset dipilih per scene. Repo tidak menyertakan koleksi semua bendera, kendaraan, efek atau voice-over. Batas kemampuan: kamera peta datar Web Mercator, bukan globe 3D; scene tertentu memerlukan proyeksi lain, pemotongan geometri atau implementasi tambahan. Tanpa Blender secara default.

## Gaya dan sumber

Default visual: peta mendominasi layar, label terbaca, informasi menempel ke lokasi. Tanpa judul presentasi besar, tanggal pojok, kompas, skala atau footer dekoratif. Semua default bisa disesuaikan permintaan pengguna. Kredit yang diwajibkan lisensi tetap dipenuhi.

Simpan sumber, lisensi dan catatan akurasi per scene. Tidak ada media atau data bertema tertentu yang dimuat otomatis. Lihat [SOURCES.md](SOURCES.md).

```bash
python -m unittest discover -s tests
```
