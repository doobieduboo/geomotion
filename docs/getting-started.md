# Mulai, environment dan penggunaan ulang

## Repo, skill dan environment berbeda

- Repo menyimpan kode, dokumentasi dan preferensi.
- Skill terpasang adalah salinan di mesin tertentu; perubahan repo tidak otomatis memperbarui salinan itu.
- Cloud environment menyimpan setup runtime dan binding kredensial. Buka repo di Base Environment tidak memindahkan sesi ke environment bernama geomotion.
- Obrolan/environment baru tidak otomatis membawa media/source produksi lama. Buka workspace yang sesuai atau sertakan paket source, bukan hanya MP4 final.

## Environment pribadi yang sudah disiapkan

Pilih **geomotion** di pemilih lingkungan **sebelum memulai obrolan**, lalu buka repo. Jika environment disiapkan/disimpan tapi belum dipublikasikan, selesaikan publikasi dengan privasi yang sesuai. Memublikasikan environment tidak sama dengan membagikannya ke publik. Update setup tersimpan biasanya digunakan oleh tugas baru dari versi yang dipublikasikan; jangan menganggap sesi lama langsung berganti environment.

Untuk obrolan baru maupun aktif, minta agent membaca repo terbaru. Agent mengikuti prosedur sinkronisasi pada AGENTS.md tanpa menimpa pekerjaan lokal, lalu memakai skill/preset checkout terbaru. Salinan skill terpasang perlu diperbarui terpisah bila dipakai.

```bash
python scripts/install_skill.py
```

Installer menolak menimpa salinan yang sudah ada. Untuk mengganti salinan setelah diperiksa, gunakan `--replace`; installer membuat backup bertanggal di luar direktori skill. Jangan menghapus perubahan lokal hanya agar installer bisa berjalan.

## API key Gemini

Nama dan model mengikuti `defaults.json` → `audio.tts`. Rahasia jaringan dikonfigurasi untuk host Gemini pada pengaturan environment; jangan tempel key ke chat, repo atau frontend player. Secret milik environment dapat dipakai pengguna environment tersebut; pertahankan audience pribadi bila itu tujuannya. Secret pribadi/vault mengikuti konfigurasi pengguna masing-masing.

Agent memakai cloud environment runtime skill dan `environment_status` untuk memeriksa readiness. Placeholder proxy bukan nilai key asli dan bukan bukti key hilang. Hanya tes API yang berhasil dapat memastikan izin model/kuota saat itu. Jangan mengaktifkan billing atau beralih model otomatis. Lihat [tts.md](../.agents/skills/geomotion/references/tts.md).

## Menjalankan visual dan menyiapkan player

```bash
python -m pip install -r .agents/skills/geomotion/scripts/requirements.txt
python .agents/skills/geomotion/scripts/render_scene.py scene.json --mode preview --output outputs/preview.mp4
python .agents/skills/geomotion/scripts/prepare_delivery.py outputs/preview.mp4 --stage preview --output SITE/dist --title "Judul dari brief"
```

`SITE/dist` adalah direktori static dari checkout Site yang dipilih; ganti dengan jalur sebenarnya. Perintah terakhir tidak memublikasikan. Baca [delivery.md](../.agents/skills/geomotion/references/delivery.md) dan gunakan skill Sites untuk menyiapkan source serta menerbitkan ke binding pengguna yang sama. Fitur komposisi yang belum ada di renderer memerlukan langkah proyek, lihat [capabilities.md](../.agents/skills/geomotion/references/capabilities.md).

Final hanya dibuat saat diminta: render ulang dari sumber dengan `--mode final`, lakukan komposisi/cek, lalu siapkan `--stage final`. Tidak meng-upscale preview. Simpan sumber/licensing dan audio terpisah agar perubahan VO/teks tetap dapat diedit.

Referensi platform: [Cloud environments](https://learn.chatgpt.com/docs/environments/cloud-environments), [Gemini API keys](https://ai.google.dev/gemini-api/docs/api-key). UI dan kuota bisa berubah; gunakan observasi/ketentuan terkini untuk diagnosis, bukan menghafal posisi tombol dari screenshot lama.
