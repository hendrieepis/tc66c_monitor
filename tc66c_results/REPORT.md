# Hasil uji TC66C — 7 Oktober 2026

Perangkat TC66, firmware 1.12, serial number 00003405. Pengujian dilakukan pada Windows menggunakan Python 3.13.12, pyserial, bleak, dan cryptography, dengan akses perangkat di luar sandbox. COM3 dan COM4 tidak dibuka.

| Jalur | Hasil |
|---|---|
| USB serial COM29, 115200 8N1 | 30/30 pembacaan sukses, masing-masing 192 byte; ketiga blok pac1/pac2/pac3 dan seluruh CRC-16/MODBUS valid |
| Bluetooth LE 82:EA:CA:10:0D:05 | Scan menemukan TC66C, RSSI sekitar -81 sampai -82 dBm; koneksi dan notifikasi berhasil; 30/30 pembacaan sukses dengan semua CRC valid |
| sigrok-cli serial COM29 | Scan berhasil mengenali TC66 1.12, S/N 00003405, 6 channel. Akuisisi --frames 4 gagal: Invalid poll response packet (magic values). Terulang pada uji dengan log diagnostik. |

Serial: 05:56:19–05:56:30 waktu lokal komputer, 5.1738–5.1748 V, 0.47–0.50 mA, 2.4–2.5 mW. BLE: 05:57:32–05:57:52, 5.1703–5.1722 V, 0.54–0.81 mA, 2.7–4.1 mW. Nilai suhu mentah 24; satuan mengikuti pengaturan perangkat.

## Cara pembacaan yang berhasil

- USB: kirim `getva`, terima 192 byte. `query` mengembalikan `firm`.
- BLE: subscribe notifikasi FFE4 (handle 22) di service FFE0; kirim `bgetva\r\n` ke FFE9 (handle 17) di service FFE5 menggunakan `response=True`.
- FFE9 pada unit ini mengiklankan properti `write` saja. Uji awal dengan `response=False` berhasil terhubung tetapi tidak menerima data; setelah diganti menjadi `response=True`, seluruh 30 pembacaan berhasil.
- Dekripsi AES-256 ECB kemudian pemeriksaan header dan CRC untuk ketiga blok 64 byte.

Bluetooth perangkat terbukti berfungsi. Penyebab percobaan Bluetooth pengguna sebelumnya belum dapat dipastikan tanpa perintah atau kode yang digunakan. Mode write tanpa respons terbukti gagal pada percobaan sesi ini.

Build sigrok terpasang: libsigrok 0.6.0-git-883c2ac. Log menunjukkan probe 192 byte berhasil didekripsi dan divalidasi, tetapi paket akuisisi berikutnya ditolak. Penyebab internal kegagalan sigrok belum terkonfirmasi. Keberhasilan Python membuktikan komunikasi USB dan format paket perangkat dapat dibaca dengan benar.

Pengujian ini memverifikasi komunikasi dan integritas paket dalam sesi singkat; belum menguji akurasi dengan alat referensi, beban besar, atau kestabilan jangka panjang. Tidak ada perintah perubahan pengaturan atau pembaruan firmware yang dikirim.

## Bukti

- [Data serial](serial.csv)
- [Data BLE](ble_0.csv)
- [Script uji](../tc66c_test.py)
- [Log serial dan percobaan awal BLE](../tc66c_test.log)
- [Log BLE yang berhasil](../tc66c_ble_test.log)
- [Log diagnostik sigrok](../tc66c_sigrok_test.log)
- Paket mentah disimpan sebagai file `.bin` pada folder ini.

Referensi protokol: https://sigrok.org/wiki/RDTech_TC66C
