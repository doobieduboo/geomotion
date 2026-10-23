# Struktur dan kepemilikan

| Lokasi | Isi |
|---|---|
| `README.md`, `docs/getting-started.md` | Penggunaan dan setup |
| `AGENTS.md` | Instruksi agent dan pemutakhiran repo dalam obrolan aktif |
| `.agents/skills/geomotion/SKILL.md` | Workflow dan routing referensi |
| `defaults.json` | Nilai serta kebijakan produksi |
| `delivery-target.json` | Binding hosting pengguna; link MP4 langsung default, player opsional |
| `references/` | Kontrak teknis; indeks `references/README.md` |
| `library/catalog.json`, `library/` | Kategori, status dan definisi komponen reusable; referensi asli tetap di workspace eksternal |
| `agents/openai.yaml` | Metadata UI skill |
| `scripts/`, `templates/`, `fonts/` | Implementasi, struktur input dan dependensi font |
| `tests/` | Verifikasi perilaku |
| Workspace produksi di luar repo | Scene, source media, narasi, stem, subtitle dan hasil render |

Path skill di tabel bersifat relatif terhadap `.agents/skills/geomotion/`. Installed skill membawa preset, referensi, template dan kode yang sama; ia tidak membutuhkan dokumen root untuk menjalankan workflow.

## Konfigurasi dan implementasi

- `scripts/config.py` membaca preset untuk renderer, basemap dan persiapan delivery.
- Renderer menerapkan basemap, profil ekspor, font dan design grid. Template berisi struktur konten, tanpa menyalin nilai default provider/encoding maupun resep appearance. `defaults.json` memiliki nilai outline reference/focus, bloom dan tint daratan; referensi style menjelaskan penggunaannya. Lokasi, koordinat, bendera dan state kepemilikan tetap input produksi.
- `effects.py` memiliki validasi glow, bloom multilapis dan komposit emisi linear-light, serta tint daratan yang mempertahankan terrain. `region_stroke.py` menyiapkan core dan emisi outline dari path yang sudah terungkap; renderer mengomposit emisi di bawah core tajam. Region dan world overlay memakai primitive efek geografis yang sama tanpa mengubah RGB bendera historis.
- Persiapan player membaca profil ekspor dan kualitas tahap dari preset, lalu menulis `media.json`. Player memvalidasi kualitas yang diizinkan sebelum menampilkan pilihan.
- `timeline.py` menyatukan clock source/output; `project_state.py` memiliki provenance/hash persetujuan. `project_workspace.py` memiliki satu `.geomotion-project.json` untuk save/load dan stage tersimpan. `revision_cache.py` menghitung dependency key konservatif per rentang; `execution.py` memvalidasi reuse, menjalankan worker dan menggabungkan segmen. `compositor.py` menambahkan PNG/atlas ke base native dengan receipt sendiri, tanpa menduplikasi scene renderer atau membuat receipt palsu. `qa.py` memeriksa hasil encode; `pipeline.py` menjadi pintu CLI untuk langkah tersebut serta review/handoff. [Kontrak pipeline](../.agents/skills/geomotion/references/pipeline.md) menjelaskan batasnya.
- `composition.py` dan `scene_layout.py` merencanakan posisi global frame, melindungi fokus geografis, memeriksa kepadatan/benturan, dan menempatkan CTA authored tanpa dekorasi tambahan.
- Subtitle aktual didukung renderer. Preset narasi, mixing, kamera editorial dan TTS tetap memandu agent; fitur itu tidak otomatis menjadi primitive renderer. Lihat [kemampuan aktual](../.agents/skills/geomotion/references/capabilities.md).
- Binding Sites adalah target delivery, bukan deployment otomatis. Agent menjalankan persiapan dan workflow Sites.

Ubah aturan pada pemiliknya, bukan melalui catatan pengecualian di banyak file. Hapus referensi usang beserta tautannya. Pemutakhiran checkout mengikuti AGENTS.md; pemutakhiran environment/kredensial mengikuti panduan setup. Keduanya tidak saling menggantikan.
