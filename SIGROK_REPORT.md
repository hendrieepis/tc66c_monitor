# Uji langsung sigrok-cli — TC66C

Uji ini hanya memakai sigrok-cli terpasang, tanpa script Python atau jembatan BLE. COM3 dan COM4 tidak dibuka. Versi: sigrok-cli 0.8.0-git-f44dd91, libsigrok 0.6.0-git-883c2ac.

## Perintah yang diuji

```powershell
sigrok-cli -l 5 -d rdtech-tc:conn=COM29 --scan
sigrok-cli -l 5 -d rdtech-tc:conn=COM29 --frames 4
sigrok-cli -l 5 -d rdtech-tc:conn=COM29 --time 2000
sigrok-cli -l 5 -d rdtech-tc:conn=bt/dialog/82-EA-CA-10-0D-05 --scan
sigrok-cli -l 5 -d rdtech-tc:conn=bt/dialog/82-EA-CA-10-0D-05 --frames 4
```

## Hasil

- Serial scan COM29 berhasil: TC66 1.12, S/N 00003405, enam channel V, I, D+, D-, E0, E1.
- Akuisisi serial `--frames 4` gagal dua kali dengan `Invalid poll response packet (magic values)` setelah menerima 192 byte. Tidak menghasilkan frame pengukuran.
- Akuisisi serial `--time 2000` pertama berhasil sampai batas waktu dengan 20 frame dan tanpa error paket; pengulangan kedua gagal dengan error magic values dan nol frame. Contoh nilai pada sesi berhasil: 5.1557 V, 2.17 mA, D+ dan D- 2.47 V, E0 5 mWh, E1 0 mWh. Dengan demikian pembacaan serial sigrok terbukti bisa berhasil, tetapi belum konsisten. Penyebabnya belum terkonfirmasi; jangan menganggap opsi batas waktu sebagai perbaikan pasti.
- Bluetooth scan maupun akuisisi gagal sebelum koneksi perangkat. Log memperlihatkan `bt/dialog/...` dibuka melalui `serial-libsp` sebagai port serial biasa dan gagal dengan `The system cannot find the path specified`. Executable terpasang tidak mengandung penanda `serial-bt`, `bt/dialog`, `bt/notify`, atau `bt/rfcomm`. Bukti ini menunjukkan build terpasang tidak menyediakan transport Bluetooth tersebut; hasil ini bukan pengujian komunikasi radio yang berhasil mencapai perangkat.

## Log lengkap

- [Serial scan](sigrok_serial_scan.log)
- [Serial 4 frame](sigrok_serial_frames.log)
- [Serial 4 frame ulang](sigrok_serial_frames_retry.log)
- [Serial 2 detik](sigrok_serial_time.log)
- [Serial 2 detik ulang](sigrok_serial_time_retry.log)
- [BLE scan](sigrok_ble_scan.log)
- [BLE 4 frame](sigrok_ble_frames.log)

Sintaks transport mengikuti [dokumentasi sigrok TC66C](https://sigrok.org/wiki/RDTech_TC66C).
