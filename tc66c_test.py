import asyncio
import argparse
import csv
import struct
import time
from pathlib import Path

import serial
from bleak import BleakClient, BleakScanner
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes

KEY = bytes.fromhex('5821fa5601b2f02687ff1204622a4fb086f40260816f9a0ba7f106619ab87288')
OUT = Path(__file__).resolve().parent / 'tc66c_results'
OUT.mkdir(exist_ok=True)

def decode(raw):
    if len(raw) != 192:
        raise ValueError(f'length {len(raw)}, expected 192')
    dec = Cipher(algorithms.AES(KEY), modes.ECB()).decryptor()
    data = dec.update(raw) + dec.finalize()
    checks = []
    for i in range(3):
        block = data[i*64:(i+1)*64]
        if block[:4] != f'pac{i+1}'.encode():
            raise ValueError(f'invalid header: {block[:4]!r}')
        crc = 0xffff
        for b in block[:60]:
            crc ^= b
            for _ in range(8):
                crc = (crc >> 1) ^ (0xa001 if crc & 1 else 0)
        checks.append(crc == int.from_bytes(block[60:64], 'little'))
    u = lambda n: struct.unpack_from('<I', data, n)[0]
    return dict(time=time.strftime('%Y-%m-%d %H:%M:%S'), model=data[4:8].decode(), firmware=data[8:12].decode(), V=u(48)/10000, I=u(52)/100000, W=u(56)/10000, temperature=u(92)*(-1 if u(88)==1 else 1), crc_ok=all(checks))

def save(name, rows):
    if rows:
        with (OUT / f'{name}.csv').open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

def serial_test(port='COM29', polls=30):
    rows = []
    with serial.Serial(port, 115200, timeout=2, write_timeout=2) as s:
        s.reset_input_buffer()
        s.write(b'query')
        print('SERIAL query:', repr(s.read(4)), flush=True)
        for i in range(polls):
            s.reset_input_buffer()
            s.write(b'getva')
            raw = s.read(192)
            (OUT / f'serial_{i:02}.bin').write_bytes(raw)
            try:
                d = decode(raw)
                rows.append(d)
                print('SERIAL', i+1, d, flush=True)
            except Exception as e:
                print('SERIAL ERROR', i+1, str(e), flush=True)
            time.sleep(.3)
    save('serial', rows)

async def ble_test(polls=30):
    for attempt in range(2):
        print('BLE SCAN', attempt+1, flush=True)
        found = await BleakScanner.discover(timeout=15, return_adv=True)
        targets = []
        for dev, adv in found.values():
            print('ADV', dev.address, repr(adv.local_name), adv.rssi, adv.service_uuids, flush=True)
            if 'tc66' in (adv.local_name or dev.name or '').lower() or any('0000ffe5-' in x for x in adv.service_uuids):
                targets.append(dev)
        for dev in targets:
            try:
                async with BleakClient(dev, timeout=20) as client:
                    print('BLE CONNECTED', dev.address, client.is_connected, flush=True)
                    for svc in client.services:
                        print('GATT', svc.uuid, [(c.uuid,c.properties,c.handle) for c in svc.characteristics], flush=True)
                    rx = '0000ffe4-0000-1000-8000-00805f9b34fb'
                    tx = '0000ffe9-0000-1000-8000-00805f9b34fb'
                    buf = bytearray()
                    await client.start_notify(rx, lambda _, data: buf.extend(data))
                    rows = []
                    for i in range(polls):
                        buf.clear()
                        await client.write_gatt_char(tx, b'bgetva\r\n', response=True)
                        end = time.monotonic()+3
                        while len(buf)<192 and time.monotonic()<end:
                            await asyncio.sleep(.02)
                        raw = bytes(buf)
                        (OUT / f'ble_{attempt}_{i:02}.bin').write_bytes(raw)
                        try:
                            d = decode(raw)
                            rows.append(d)
                            print('BLE', i+1, d, flush=True)
                        except Exception as e:
                            print('BLE ERROR', i+1, str(e), flush=True)
                        await asyncio.sleep(.3)
                    save(f'ble_{attempt}', rows)
                    if rows:
                        return
            except Exception as e:
                print('BLE CONNECTION ERROR', dev.address, repr(e), flush=True)
        if not targets:
            print('TC66C not advertising in scan', flush=True)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Uji pembacaan TC66C melalui USB serial atau BLE.')
    parser.add_argument('--mode', choices=['serial', 'ble', 'both'], default='both')
    parser.add_argument('--port', default='COM29', help='Port USB serial (default COM29)')
    parser.add_argument('--polls', type=int, default=30, help='Jumlah pembacaan (default 30)')
    args = parser.parse_args()
    if args.polls < 1:
        parser.error('--polls harus lebih dari 0')
    if args.mode in ('serial', 'both') and args.port.upper() in ('COM3', 'COM4'):
        parser.error('COM3 dan COM4 tidak boleh digunakan')
    if args.mode in ('serial', 'both'):
        try:
            serial_test(args.port, args.polls)
        except Exception as e:
            print('SERIAL FAILURE', repr(e), flush=True)
    if args.mode in ('ble', 'both'):
        asyncio.run(ble_test(args.polls))
