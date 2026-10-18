# Pembagian instruksi, skill dan knowledge

## Fungsi setiap lapisan

| Lapisan | Lokasi | Tanggung jawab |
|---|---|---|
| Pengantar pengguna | `README.md`, `docs/getting-started.md` | Cara mulai, instalasi, environment dan penggunaan |
| Instruksi agent | `AGENTS.md` | Aturan repo, pintu masuk dan cara merawatnya |
| Skill | `.agents/skills/geomotion/SKILL.md` | Workflow tugas dan referensi yang dibaca sesuai kebutuhan |
| Konfigurasi | `defaults.json` | Nilai preset produksi yang bisa dibaca program/agent |
| Binding pengguna | `delivery-target.json` | Target player milik pengguna; dapat diganti, bukan cerita default |
| Knowledge | `references/` | Pengetahuan teknis per bidang; indeksnya `references/README.md` |
| Metadata skill | `agents/openai.yaml` | Nama/deskripsi/prompt di UI; bukan agent terpisah atau workflow kedua |
| Implementasi | `scripts/`, `templates/`, `fonts/` | Kode, struktur input, UI reusable dan font berlisensi |
| Verifikasi | `tests/` | Pemeriksaan perilaku toolkit |
| Produksi tertentu | Workspace produksi di luar Git toolkit | Scene, media, sumber, audio, timing dan ekspor untuk satu proyek |

Instruksi kerja sudah bagian dari `AGENTS.md`; tidak perlu `INSTRUCTIONS.md` tambahan yang berisi aturan sama. Detail langkah produksi tetap di skill agar agent yang memakai skill terpasang bisa membacanya. Knowledge bukan salinan percakapan atau daftar fakta topik tertentu.

## Konsistensi dan perubahan

Instruksi eksplisit pengguna dapat mengubah default proyek; aturan sesi/platform yang lebih tinggi tetap berlaku. `AGENTS.md` mengatur pekerjaan repo, `SKILL.md` menjelaskan workflow, JSON menyimpan nilai, dan referensi menjelaskan teknik penerapannya. Jika ada ketidaksesuaian, perbaiki sumber yang memilikinya serta tautan terkait, bukan menambah aturan baru di akhir banyak file.

Ubah nilai numerik/model di preset, lalu perbarui dokumentasi ringkas yang menyebutnya. Jangan mengubah preset saat sekadar merapikan dokumentasi. Pertahankan jalur script/installer; reference lama boleh menjadi indeks kompatibilitas singkat. Baca referensi sesuai tugas agar konteks tidak membengkak.

## Yang dibaca program dan yang memandu agent

- `render_scene.py` membaca profil ekspor/encoding dan jalur font regular/bold.
- `prepare_delivery.py` membaca profil ekspor, daftar kualitas per tahap, dan template player; menulis `media.json`.
- Preset komposisi, CTA, subtitle, mixing, kamera naratif dan pin model TTS memandu langkah produksi agent. Tidak semuanya fitur JSON renderer.
- Binding Sites tidak memublikasikan sendiri; agent memakai workflow Sites dengan akses yang tersedia.

Lihat [capabilities.md](capabilities.md) sebelum menambah klaim fitur. Tidak ada janji bahwa semua capability produksi sebelumnya sudah di-port ke renderer generik.
