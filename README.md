# GeoMotion Skill

Skill Codex untuk animasi peta bergaya GeoLayers: kamera dinamis, batas wilayah glow, label lokasi, ikon, rute, serta bubble foto/info. Fokus pada video vertikal dan sprite 2.5D, tanpa Blender.

**Gaya tersimpan:** peta mendominasi layar; tanpa judul presentasi besar, tanggal pojok, kompas, skala, atau footer dekoratif. Preview **360×640 / 24 fps**. Final **720×1280 / 30 fps**, hanya saat diminta.

## Pakai di obrolan baru

1. Buka repo ini sebagai workspace/environment di sesi Codex baru.
2. Minta: **“Pakai $geomotion, buat preview animasi peta Indonesia ke Belanda.”**
3. Agent membaca `AGENTS.md` dan `.agents/skills/geomotion/SKILL.md`.

Repo tidak otomatis membuat semua chat ChatGPT atau Work mengenal skill ini. Session perlu akses repo/file dan alat eksekusi. Jika ingin memasang untuk user Codex pada mesin yang sama:

```bash
python scripts/install_skill.py
```

Mulai sesi baru setelah pemasangan. Di environment/mesin lain, buka repo atau install lagi. Jika platform tidak mendeteksi skill otomatis, arahkan agent untuk membaca `.agents/skills/geomotion/SKILL.md` secara eksplisit.

## Contoh render yang sudah berjalan

Memerlukan Python 3.10+, FFmpeg, font DejaVu Sans, Pillow dan NumPy. Installer skill tidak memasang dependency sistem. Bila font berbeda, set `GEOMOTION_FONT_BOLD` dan `GEOMOTION_FONT_REGULAR` ke file TTF/OTF yang sesuai.

```bash
python -m pip install -r .agents/skills/geomotion/scripts/requirements.txt
python .agents/skills/geomotion/scripts/render_demo.py --mode preview --output outputs/preview.mp4
```

Contoh ini adalah adegan **Jakarta–Rengasdengklok, 15 detik**. Skrip mendownload data wilayah, foto arsip dan tile peta pada pemakaian pertama. Cache dipakai ulang. Jalankan setelah meninjau sumber dan ketentuan aset di `SOURCES.md`.

Cek cuplikan 1 detik:

```bash
python .agents/skills/geomotion/scripts/render_demo.py --mode preview --start 11 --duration 1 --output outputs/check.mp4
```

Saat final sudah diminta:

```bash
python .agents/skills/geomotion/scripts/render_demo.py --mode final --output outputs/final.mp4
```

## Apa yang tersedia

- Skill dan pedoman visual yang bisa dibaca agent di sesi baru.
- Renderer referensi dengan kamera peta, polygon glow, rute, ikon mobil bergerak, pin, serta bubble foto/info.
- Utility untuk isian bendera mengikuti polygon/pulau/lubang, penanda bendera bertiang berkibar, dan pemilihan sprite berdasarkan arah relatif kamera.
- Kontrak aset 16–32 arah untuk tank, pesawat, helikopter, kapal dan kendaraan lain; spesifikasi efek dan sumber.
- Installer lokal, manifest input demo dengan checksum, serta tes utilitas layer.

**Belum termasuk:** koleksi sprite kendaraan, paket bendera semua negara, animasi ledakan siap pakai, voice-over, globe 3D, atau editor visual. Utility bendera/sprite perlu diintegrasikan ke scene dengan aset nyata. Renderer demo bukan engine scene JSON universal; agent mengadaptasi kode untuk cerita/lokasi baru.

## Struktur

```text
AGENTS.md
.agents/skills/geomotion/
  SKILL.md
  agents/openai.yaml
  references/          # gaya, kontrak aset, manifest sumber
  scripts/             # renderer demo, downloader, utility layer
scripts/install_skill.py
tests/test_layers.py
SOURCES.md
```

```bash
python -m unittest discover -s tests
```

Sumber, tanggal data dan lisensi media dicatat terpisah. Batas administratif modern bukan bukti batas tahun 1945. Hormati atribusi yang benar-benar diwajibkan penyedia; lisensi kode repo tidak mencakup media pihak ketiga.
