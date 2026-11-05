#!/usr/bin/env python3
"""SwitchBot 温湿度計用の Lagoon 3 ダッシュボード JSON を生成する。
ターゲットの形式は try.soracom.io/lagoon-gallery のテンプレート (harvest-backend-datasource) に合わせている。
IMSI はインポート時に入力する (__inputs の constant)。

使い方: python3 tools/gen_lagoon_dashboard.py [出力先 (既定: lagoon/dashboard.json)]
"""
import json
import sys

IMSI = "${VAR_IMSI}"
OUT = sys.argv[1] if len(sys.argv) > 1 else "lagoon/dashboard.json"
DS = {"type": "harvest-backend-datasource", "uid": "${DS_HARVEST}"}


def target(prop, ref):
    return {"datasource": DS, "datatype": "standard", "devicetype": "subscribers", "pro": True,
            "properties": prop, "refId": ref, "target": IMSI, "type": "timeseries"}


def thresholds(steps):
    return {"mode": "absolute", "steps": [{"color": c, "value": v} for v, c in steps]}


def stat(pid, title, prop, unit, x, y, steps, decimals=1, w=3, h=4):
    return {
        "id": pid, "type": "stat", "title": title, "datasource": DS,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "fieldConfig": {"defaults": {"unit": unit, "decimals": decimals, "color": {"mode": "thresholds"},
                                     "thresholds": thresholds(steps)}, "overrides": []},
        "options": {"reduceOptions": {"calcs": ["lastNotNull"], "fields": "", "values": False},
                    "colorMode": "value", "graphMode": "area", "justifyMode": "center", "textMode": "value",
                    "orientation": "auto"},
        "targets": [target(prop, "A")],
    }


def series(pid, title, props, x, y, w=12, h=8, overrides=None, unit=None, axis=None):
    defaults = {"unit": unit or "none", "color": {"mode": "palette-classic"},
                "custom": {"drawStyle": "line", "lineWidth": 2, "fillOpacity": 10,
                           "showPoints": "never", "spanNulls": False}}
    if axis:
        defaults["min"], defaults["max"] = axis
    return {
        "id": pid, "type": "timeseries", "title": title, "datasource": DS,
        "gridPos": {"h": h, "w": w, "x": x, "y": y},
        "fieldConfig": {"defaults": defaults, "overrides": overrides or []},
        "options": {"legend": {"displayMode": "list", "placement": "bottom", "showLegend": True},
                    "tooltip": {"mode": "multi", "sort": "none"}},
        "targets": [target(p, chr(65 + i)) for i, p in enumerate(props)],
    }


def dashed(name):
    return {"matcher": {"id": "byName", "options": name},
            "properties": [{"id": "custom.lineStyle", "value": {"fill": "dash", "dash": [10, 10]}},
                           {"id": "custom.fillOpacity", "value": 0}]}


def right_axis(name, unit):
    return {"matcher": {"id": "byName", "options": name},
            "properties": [{"id": "custom.axisPlacement", "value": "right"}, {"id": "unit", "value": unit}]}


G, Y, O, R = "green", "yellow", "orange", "red"
panels = [
    stat(1, "温度", "switchbot_temperature", "celsius", 0, 0, [(None, "blue"), (18, G), (28, O), (31, R)], w=8),
    stat(2, "湿度", "switchbot_humidity", "percent", 8, 0, [(None, O), (40, G), (60, Y), (70, O)], decimals=0, w=8),
    stat(3, "電池残量", "switchbot_battery", "percent", 16, 0, [(None, R), (20, Y), (40, G)], decimals=0, w=8),
    series(4, "温度・湿度", ["switchbot_temperature", "switchbot_humidity"], 0, 4, w=24, unit="celsius",
           overrides=[right_axis("switchbot_humidity", "percent")]),
]

dashboard = {
    "__inputs": [{"name": "DS_HARVEST", "label": "Soracom", "description": "", "type": "datasource",
                  "pluginId": "harvest-backend-datasource", "pluginName": "soracom-backend"},
                 {"name": "VAR_IMSI", "label": "IMSI", "description": "Harvest Data に送信している SIM の IMSI",
                  "type": "constant", "value": ""}],
    "__elements": {},
    "__requires": [
        {"type": "grafana", "id": "grafana", "name": "Grafana", "version": "9.3.9"},
        {"type": "datasource", "id": "harvest-backend-datasource", "name": "soracom-backend", "version": "1.0.0"},
        {"type": "panel", "id": "stat", "name": "Stat", "version": ""},
        {"type": "panel", "id": "timeseries", "name": "Time series", "version": ""},
    ],
    "annotations": {"list": []},
    "editable": True,
    "graphTooltip": 1,
    "links": [],
    "panels": panels,
    "refresh": "1m",
    "schemaVersion": 37,
    "tags": ["SwitchBot"],
    "templating": {"list": []},
    "time": {"from": "now-3h", "to": "now"},
    "timepicker": {},
    "timezone": "browser",
    "title": "SwitchBot 温湿度計",
    "uid": "switchbot-meter",
    "version": 1,
    "weekStart": "",
}

with open(OUT, "w") as f:
    json.dump(dashboard, f, ensure_ascii=False, indent=2)
print(f"panels={len(panels)} -> {OUT}")
