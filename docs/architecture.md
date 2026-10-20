# Struktur dan kepemilikan

| Lokasi | Isi |
|---|---|
| `README.md`, `docs/getting-started.md` | Penggunaan dan setup |
| `AGENTS.md` | Instruksi agent dan pemutakhiran repo dalam obrolan aktif |
| `.agents/skills/geomotion/SKILL.md` | Workflow dan routing referensi |
| `defaults.json` | Nilai serta kebijakan produksi |
| `delivery-target.json` | Binding player pengguna |
| `references/` | Kontrak teknis; indeks `references/README.md` |
| `library/catalog.json`, `library/` | Kategori, status dan definisi komponen reusable; referensi asli tetap di workspace eksternal |
| `agents/openai.yaml` | Metadata UI skill |
| `scripts/`, `templates/`, `fonts/` | Implementasi, struktur input dan dependensi font |
| `tests/` | Verifikasi perilaku |
| Workspace produksi di luar repo | Scene, source media, narasi, stem, subtitle dan hasil render |

Path skill di tabel bersifat relatif terhadap `.agents/skills/geomotion/`. Installed skill membawa preset, referensi, template dan kode yang sama; ia tidak membutuhkan dokumen root untuk menjalankan workflow.

## Konfigurasi dan implementasi

- `scripts/config.py` membaca preset untuk renderer, basemap dan persiapan delivery.
- Renderer menerapkan basemap, profil ekspor, font dan design grid. Template berisi struktur konten, tanpa menyalin nilai default provider/encoding.
- Persiapan player membaca profil ekspor dan kualitas tahap dari preset, lalu menulis `media.json`. Player memvalidasi kualitas yang diizinkan sebelum menampilkan pilihan.
- `timeline.py` menyatukan clock source/output; `project_state.py` mencatat provenance serta hash persetujuan. `execution.py` mengatur segmen native/checkpoint; `qa.py` memeriksa hasil encode; `pipeline.py` mengikat render, review dan handoff Sites. [Kontrak pipeline](../.agents/skills/geomotion/references/pipeline.md) menjelaskan batasnya.
- Subtitle aktual didukung renderer. Preset narasi, mixing, kamera editorial dan TTS tetap memandu agent; fitur itu tidak otomatis menjadi primitive renderer. Lihat [kemampuan aktual](../.agents/skills/geomotion/references/capabilities.md).
- Binding Sites adalah target delivery, bukan deployment otomatis. Agent menjalankan persiapan dan workflow Sites.

Ubah aturan pada pemiliknya, bukan melalui catatan pengecualian di banyak file. Hapus referensi usang beserta tautannya. Pemutakhiran checkout mengikuti AGENTS.md; pemutakhiran environment/kredensial mengikuti panduan setup. Keduanya tidak saling menggantikan.
