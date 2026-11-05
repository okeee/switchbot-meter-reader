# switchbot-meter-reader

[SwitchBot 温湿度計](https://www.switchbot.jp/) の値 (温度・湿度・電池残量) を BLE のアドバタイズから読み取り、受信するたびに JSON を 1 行ずつ標準出力に出すコマンドです。

[harvest-relay](https://github.com/okeee/harvest-relay) の stream センサーとして使うと、ほかのセンサーの値と 1 リクエストにまとめて SORACOM Harvest Data に送り、SORACOM Lagoon で推移を見られます。

```console
$ switchbot-meter-reader --address XX:XX:XX:XX:XX:XX
{"switchbot_temperature": 24.1, "switchbot_humidity": 56, "switchbot_battery": 100}
{"switchbot_temperature": 24.1, "switchbot_humidity": 56, "switchbot_battery": 100}
```

| フィールド | 内容 |
|---|---|
| switchbot_temperature | 温度 (℃、0.1℃ 単位) |
| switchbot_humidity | 湿度 (%、1% 単位) |
| switchbot_battery | 電池残量 (%)。アドバタイズに含まれないときは出力しません |

接頭辞は `--prefix` で変えられます。

## 特徴

- **接続しない**: アドバタイズを受信するだけなので、ほかの BLE 機器の接続を妨げず、SwitchBot アプリやハブとも併用できます
- **温湿度計を探せる**: `--list` で、近くにある SwitchBot 温湿度計の MAC アドレスと今の値を一覧表示します

## 対応機種

アドバタイズのデバイス種別で判定しています。

| 種別 | 機種 |
|---|---|
| `0x54` | 温湿度計 |
| `0x69` | 温湿度計プラス (動作確認済み) |
| `0x77` | 防水温湿度計 |

ファームウェアによって値の入る場所 (メーカーデータかサービスデータか) が違うため、両方に対応しています。

## 必要なもの

- Raspberry Pi などの Linux 端末 (Raspberry Pi OS で確認)
- Python 3.10 以上と [bleak](https://github.com/hbldh/bleak)

```bash
sudo apt install python3-bleak bluez
```

## セットアップ

1. コマンドを配置します

```bash
sudo install -m 755 switchbot-meter-reader.py /usr/local/bin/switchbot-meter-reader
```

2. 温湿度計の MAC アドレスを調べます。近所の家の温湿度計が見えることもあるので、本体の画面と値が同じものを選びます。電波強度 (rssi) が強い (0 に近い) ほど近くにあります

```console
$ switchbot-meter-reader --list
XX:XX:XX:XX:XX:01	rssi=-68	{"temperature": 24.1, "humidity": 56, "battery": 100}
XX:XX:XX:XX:XX:02	rssi=-88	{"temperature": 22.6, "humidity": 63, "battery": 100}
```

3. 値が出ることを確認します (Ctrl+C で止まります)

```bash
switchbot-meter-reader --address XX:XX:XX:XX:XX:XX
```

### harvest-relay で Harvest Data に送る

[harvest-relay.example.toml](harvest-relay.example.toml) の `[[source]]` を harvest-relay の設定ファイルに加えます。温度・湿度は送信周期ごとの平均、電池残量は最後の値を送ります。

## Lagoon ダッシュボード

[lagoon/dashboard.json](lagoon/dashboard.json) を SORACOM Lagoon 3 の Dashboards → Import から読み込みます。インポート時にデータソースと IMSI (Harvest Data に送っている SIM / Arc の IMSI) を指定します。既定の接頭辞 `switchbot_` を前提にしています。

## 注意点

- アドバタイズの形式は SwitchBot が公開している [BLE の仕様](https://github.com/OpenWonderLabs/SwitchBotAPI-BLE) に基づいています。ファームウェアの更新で変わる可能性があります
- 温湿度計は数秒ごとにアドバタイズしますが、値は 0.1℃ / 1% 単位です

## ライセンス

MIT
