#!/usr/bin/env python3
"""SwitchBot 温湿度計の値 (温度・湿度・電池残量) を BLE のアドバタイズから読み取り、受信するたびに JSON を 1 行ずつ標準出力に出す。

接続はせずアドバタイズを受信するだけなので、ほかの BLE 機器の接続を妨げず、SwitchBot アプリとも併用できる。
"""
import argparse
import asyncio
import json
import signal
import sys

SERVICE_UUIDS = ("0000fd3d-0000-1000-8000-00805f9b34fb", "00000d00-0000-1000-8000-00805f9b34fb")
COMPANY_ID = 0x0969  # Woan Technology (SwitchBot)
# サービスデータ 1 バイト目のデバイス種別
METER_TYPES = {0x54: "meter", 0x69: "meter_plus", 0x77: "outdoor_meter"}


def decode_temp_hum(frac: int, temp: int, hum: int) -> tuple[float, int]:
    t = (temp & 0x7F) + (frac & 0x0F) / 10
    if not temp & 0x80:  # 最上位ビットが 0 なら氷点下
        t = -t
    return round(t, 1), hum & 0x7F


def decode(service_data: dict, manufacturer_data: dict, strict: bool = False) -> dict | None:
    """アドバタイズから値を取り出す。温湿度計でなければ None。

    strict のときは、デバイス種別が入ったサービスデータを受信したときだけ値を返す
    (メーカーデータだけでは温湿度計かどうか判別できないため)。
    """
    sd = next((bytes(service_data[u]) for u in SERVICE_UUIDS if u in service_data), b"")
    md = bytes(manufacturer_data.get(COMPANY_ID, b""))
    if (sd and sd[0] not in METER_TYPES) or (strict and not sd):
        return None
    out = {}
    # 新しいファームウェアはメーカーデータ (MAC 6 バイト + 連番 + 状態 + 温度 2 バイト + 湿度) に値を入れる
    if len(md) >= 11:
        out["temperature"], out["humidity"] = decode_temp_hum(md[8], md[9], md[10])
    elif len(sd) >= 6:
        out["temperature"], out["humidity"] = decode_temp_hum(sd[3], sd[4], sd[5])
    if len(sd) >= 3:
        out["battery"] = sd[2] & 0x7F
    return out if "temperature" in out else None


async def scan(args) -> None:
    from bleak import BleakScanner

    target = args.address.upper() if args.address else None
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, stop.set)

    def on_adv(device, adv) -> None:
        if target and device.address.upper() != target:
            return
        values = decode(adv.service_data, adv.manufacturer_data, strict=args.list)
        if values is None:
            return
        if args.list:
            line = f"{device.address}\trssi={adv.rssi}\t{json.dumps(values)}"
        else:
            line = json.dumps({f"{args.prefix}{k}": v for k, v in values.items()})
        try:
            print(line, flush=True)
        except BrokenPipeError:  # 読み手 (harvest-relay など) がいなくなったら終わる
            stop.set()

    async with BleakScanner(on_adv):
        if args.list:
            try:
                await asyncio.wait_for(stop.wait(), timeout=args.list_seconds)
            except asyncio.TimeoutError:
                pass
        else:
            await stop.wait()


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--address", help="読み取る温湿度計の MAC アドレス")
    p.add_argument("--prefix", default="switchbot_", help="出力するフィールド名の接頭辞")
    p.add_argument("--list", action="store_true", help="近くの SwitchBot 温湿度計を一覧表示する")
    p.add_argument("--list-seconds", type=float, default=20, help="--list のスキャン時間 (秒)")
    args = p.parse_args()
    if not args.address and not args.list:
        p.error("--address か --list を指定してください")
    asyncio.run(scan(args))
    return 0


if __name__ == "__main__":
    sys.exit(main())
